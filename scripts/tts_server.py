import os
import subprocess
import pyaudio
import io
import wave
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import queue
import time
import atexit
import onnxruntime as ort
import unidecode
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Base directory of the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TTS_MODE = os.getenv("TTS_MODE", "").lower()
VOICEVOX_VOICE_ID = os.getenv("VOICEVOX_VOICE_ID")
PIPER_VOICE_NAME = os.getenv("PIPER_VOICE_NAME")

TARGET_OUTPUT_NAME = os.getenv("TARGET_OUTPUT_NAME")
VOICEVOX_URL = "http://127.0.0.1:50021"

VOICEVOX_SPEED_SCALE = os.getenv("VOICEVOX_SPEED_SCALE")
VOICEVOX_PITCH_SCALE = os.getenv("VOICEVOX_PITCH_SCALE")
VOICEVOX_INTONATION_SCALE = os.getenv("VOICEVOX_INTONATION_SCALE")
VOICEVOX_VOLUME_SCALE = os.getenv("VOICEVOX_VOLUME_SCALE")

SAMPLE_RATE = 22050  # Piper native sample rate
CHANNELS = 1
FORMAT = pyaudio.paInt16
USE_CUDA_IF_AVAILABLE = True

WORD_REPLACEMENTS = {
    "tachi": "tatchy",
}

# PyAudio setup
pa = pyaudio.PyAudio()

# Thread-safe queue for audio chunks
audio_queue = queue.Queue()

def find_device_index_by_name(target_name, is_output=True):
    target_name_lower = target_name.lower()
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        name = info["name"].lower()
        if is_output and info["maxOutputChannels"] > 0:
            if target_name_lower in name:
                print(f"Found output device: {info['name']} at index {i}")
                return i
        elif not is_output and info["maxInputChannels"] > 0:
            if target_name_lower in name:
                print(f"Found input device: {info['name']} at index {i}")
                return i
    raise RuntimeError(f"No {'output' if is_output else 'input'} device found containing '{target_name}'")

OUTPUT_DEVICE_INDEX = find_device_index_by_name(TARGET_OUTPUT_NAME, is_output=True)

def replace_words(text: str) -> str:
    for src, dst in WORD_REPLACEMENTS.items():
        pattern = r"\b" + re.escape(src) + r"\b"
        text = re.sub(pattern, dst, text, flags=re.IGNORECASE)
    return text

if TTS_MODE == "piper":
    # Piper specific setup
    PIPER_EXE = os.path.join(BASE_DIR, "../piper/piper.exe")

    # Full paths to model/config
    PIPER_MODEL_PATH = os.path.join(BASE_DIR, "../voice_models/piper/" + PIPER_VOICE_NAME + "/medium/en_US-" + PIPER_VOICE_NAME + "-medium.onnx")
    PIPER_CONFIG_PATH = os.path.join(BASE_DIR, "../voice_models/piper/" + PIPER_VOICE_NAME + "/medium/en_US-" + PIPER_VOICE_NAME + "-medium.onnx.json")

    # Start Piper subprocess once, keep it alive
    cmd = [
        PIPER_EXE,
        "--model", PIPER_MODEL_PATH,
        "--config", PIPER_CONFIG_PATH,
        "--output-raw",
        "--length-scale", "0.7"
    ]

    # Detect CUDA
    providers = ort.get_available_providers()
    if "CUDAExecutionProvider" in providers and USE_CUDA_IF_AVAILABLE:
        cmd.append("--cuda")
        print("[INFO] CUDA supported, using GPU mode")
    else:
        print("[INFO] Using CPU mode")

    # Start the persistent Piper subprocess
    piper_proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0
    )

    # Background thread to read Piper stdout continuously
    def piper_stdout_reader():
        while True:
            chunk = piper_proc.stdout.read(65536)
            if not chunk:
                break
            audio_queue.put(chunk)

    threading.Thread(target=piper_stdout_reader, daemon=True).start()

    # Background thread to feed PyAudio
    def audio_worker():
        stream = pa.open(format=FORMAT,
                         channels=CHANNELS,
                         rate=SAMPLE_RATE,
                         output=True,
                         output_device_index=OUTPUT_DEVICE_INDEX)
        while True:
            chunk = audio_queue.get()
            if chunk is None:  # Sentinel to stop
                break
            stream.write(chunk)
        stream.stop_stream()
        stream.close()

    threading.Thread(target=audio_worker, daemon=True).start()

elif TTS_MODE == "voicevox":
    # VoiceVox specific setup
    print("[INFO] Using VoiceVox TTS mode")

    SAMPLE_RATE = 24000   # VOICEVOX native

    # Thread-safe audio queue (already declared globally)
    # audio_queue = queue.Queue()

    # Background audio thread (already declared globally)
    # threading.Thread(target=audio_worker, daemon=True).start()

    def voicevox_speak(text: str):
        try:
            # Optional unidecode/word replacements
            text = unidecode.unidecode(text)
            text = replace_words(text)

            # 1️⃣ Create audio query
            q = requests.post(
                f"{VOICEVOX_URL}/audio_query",
                params={
                    "text": text,
                    "speaker": VOICEVOX_VOICE_ID,
                },
                timeout=5,
            )
            q.raise_for_status()
            query = q.json()

            # Optional tuning
            query["speedScale"] = VOICEVOX_SPEED_SCALE
            query["pitchScale"] = VOICEVOX_PITCH_SCALE
            query["intonationScale"] = VOICEVOX_INTONATION_SCALE
            query["volumeScale"] = VOICEVOX_VOLUME_SCALE

            # 2️⃣ Synthesize
            s = requests.post(
                f"{VOICEVOX_URL}/synthesis",
                params={"speaker": VOICEVOX_VOICE_ID},
                json=query,
                timeout=10,
            )
            s.raise_for_status()

            # Convert WAV to PCM16 and queue for playback
            with wave.open(io.BytesIO(s.content), "rb") as wf:
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                    raise RuntimeError("VOICEVOX returned incompatible audio")
                pcm = wf.readframes(wf.getnframes())
                audio_queue.put(pcm)

        except Exception as e:
            print(f"[ERROR][VOICEVOX] {e}")

        # Background audio thread for VoiceVox
        def audio_worker():
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=24000,  # VOICEVOX native sample rate
                output=True,
                output_device_index=OUTPUT_DEVICE_INDEX
            )

            while True:
                chunk = audio_queue.get()
                if chunk is None:  # Sentinel to stop
                    break
                stream.write(chunk)

            stream.stop_stream()
            stream.close()

        threading.Thread(target=audio_worker, daemon=True).start()

else:
    # Invalid TTS_MODE
    print(f"[ERROR] Invalid TTS_MODE: {TTS_MODE}")

# Flask endpoint
@app.route("/speak", methods=["POST"])
def speak():
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' field"}), 400

        text = data["text"]
        print(f"[TTS RECEIVED] {text}")
        text = unidecode.unidecode(text)
        text = replace_words(text)

        start_time = time.time()

        if TTS_MODE == "piper":
            if piper_proc.poll() is not None:
                # Piper has crashed
                print("[ERROR] Piper subprocess dead...")

            # Send text to Piper stdin
            piper_proc.stdin.write(text.encode("utf-8"))
            piper_proc.stdin.write(b"\n")
            piper_proc.stdin.flush()

        elif TTS_MODE == "voicevox":
            voicevox_speak(text)

        else:
            return jsonify({"error": f"Invalid TTS_MODE: {TTS_MODE}"}), 400

        elapsed = time.time() - start_time
        print(f"[TTS TIMING] Text sent in {elapsed:.3f} seconds")

        return jsonify({"status": "sent", "elapsed_seconds": round(elapsed, 3)})

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500

# Graceful shutdown
@atexit.register
def cleanup():
    print("[INFO] Shutting down TTS subprocess")
    try:
        if TTS_MODE == "piper":
            audio_queue.put(None)  # Stop audio thread
            if piper_proc:
                piper_proc.stdin.close()
                piper_proc.terminate()
                piper_proc.wait(timeout=5)
        elif TTS_MODE == "voicevox":
            # TODO: Stop VoiceVox audio threads if needed
            pass
    except Exception:
        pass

if __name__ == "__main__":
    app.run(debug=False, port=5005)
