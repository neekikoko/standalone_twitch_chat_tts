import os
import subprocess
import pyaudio
from flask import Flask, request, jsonify
import threading
import queue
import time
import atexit
import onnxruntime as ort
import unidecode
import re

app = Flask(__name__)

# Base directory of the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Full paths to model/config
MODEL_PATH = os.path.join(BASE_DIR, "../../plugins/piper-voices/en/en_US/amy/medium/en_US-amy-medium.onnx")
CONFIG_PATH = os.path.join(BASE_DIR, "../../plugins/piper-voices/en/en_US/amy/medium/en_US-amy-medium.onnx.json")

#MODEL_PATH = os.path.join(BASE_DIR, "../../plugins/piper-voices/de/de_DE/eva_k/x_low/de_DE-eva_k-x_low.onnx")
#CONFIG_PATH = os.path.join(BASE_DIR, "../../plugins/piper-voices/de/de_DE/eva_k/x_low/de_DE-eva_k-x_low.onnx.json")

SAMPLE_RATE = 22050  # Piper native sample rate
CHANNELS = 1
FORMAT = pyaudio.paInt16
TARGET_OUTPUT_NAME = "CABLE-A Input"
USE_CUDA_IF_AVAILABLE = True

WORD_REPLACEMENTS = {
    "tachi": "tatchy",
}

# PyAudio setup
pa = pyaudio.PyAudio()

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

# -------------------------------------------------------------
# Start Piper subprocess once, keep it alive
# -------------------------------------------------------------
cmd = [
    "piper",
    "--model", MODEL_PATH,
    "--config", CONFIG_PATH,
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

# Thread-safe queue for audio chunks
audio_queue = queue.Queue()

# -------------------------------------------------------------
# Background thread to read Piper stdout continuously
# -------------------------------------------------------------
def piper_stdout_reader():
    while True:
        chunk = piper_proc.stdout.read(65536)
        if not chunk:
            break
        audio_queue.put(chunk)

threading.Thread(target=piper_stdout_reader, daemon=True).start()

# -------------------------------------------------------------
# Background thread to feed PyAudio
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# Flask endpoint
# -------------------------------------------------------------
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

        if piper_proc.poll() is not None:
            # Piper has crashed
            print("[ERROR] Piper subprocess dead...")

        # Send text to Piper stdin
        piper_proc.stdin.write(text.encode("utf-8"))
        piper_proc.stdin.write(b"\n")
        piper_proc.stdin.flush()

        elapsed = time.time() - start_time
        print(f"[TTS TIMING] Text sent in {elapsed:.3f} seconds")

        return jsonify({"status": "sent", "elapsed_seconds": round(elapsed, 3)})

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------------
# Graceful shutdown
# -------------------------------------------------------------
@atexit.register
def cleanup():
    print("[INFO] Shutting down Piper subprocess")
    try:
        audio_queue.put(None)  # Stop audio thread
        if piper_proc:
            piper_proc.stdin.close()
            piper_proc.terminate()
            piper_proc.wait(timeout=5)
    except Exception:
        pass

# -------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=False, port=5005)
