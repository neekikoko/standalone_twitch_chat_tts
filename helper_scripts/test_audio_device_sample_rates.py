import pyaudio

pa = pyaudio.PyAudio()

print("Available output devices:")
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    if info["maxOutputChannels"] > 0:
        print(f"Device {i}: {info['name']}")

print("\nTesting sample rates for each device:")
sample_rates = [22050, 32000, 44100, 48000]
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    if info["maxOutputChannels"] > 0:
        print(f"\nDevice {i}: {info['name']}")
        for rate in sample_rates:
            try:
                stream = pa.open(format=pyaudio.paInt16,
                                 channels=1,
                                 rate=rate,
                                 output=True,
                                 output_device_index=i)
                stream.close()
                print(f"  Supports {rate} Hz")
            except Exception:
                print(f"  Does NOT support {rate} Hz")

pa.terminate()
