import pyaudio

p = pyaudio.PyAudio()

# get all
#for i in range(p.get_device_count()):
#    info = p.get_device_info_by_index(i)
#    if info['maxOutputChannels'] > 0:
#        print(f"Device {i}: {info['name']}")
#p.terminate()

# get vb-audio
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    #if "Potato Virtual Cable" in info['name']:
    print(f"Device {i}: {info['name']} (input: {info['maxInputChannels']}, output: {info['maxOutputChannels']})")
p.terminate()
