# Installation

1. Copy the file ``.env.example``  and name it ``.env``
2. Install python and pip on your system. Application is tested with python version 3.12.9. Exact version should not matter.
3. run ``pip install -r requirements.txt`` and wait for package installation.
4. Download and install a virtual audio cable, e.g. from https://vb-audio.com/Cable/.
5. Locate your virtual audio cable name by running ``py .\helper_scripts\find_audio_devices.py``. 
   1. A list of all your audio devices is printed. If you use vb-audio the cable you are looking for should be called
         something like ``CABLE Input (VB-Audio Virtual C``
   2. Copy this audio device name and set it as ``TARGET_OUTPUT_NAME``, e.g. ``TARGET_OUTPUT_NAME = "CABLE Input (VB-Audio Virtual C"``
6. Go into OBS and add a new ``Audio Input Capture`` Source.
   1. As device, set your virtual audio cable. If you use vb-audio,
   it should be called ``CABLE Output (VB-Audio Virtual Cable)``
   2. After the source is created, right click inside the OBS Audio Mixer Dock and select ``Advanced Audio Properties``.
   In the Column ``Audio Monitoring`` select either ``Monitor Only (mute output)`` if you capture desktop audio
   or ``Monitor and Output`` otherwise (I think).

## For testing without twitch account:
1. In .env, set ``TEST_WITHOUT_REDEEMS=true``
2. Double-click the file ``start.bat``.
   1. This should open a Windows terminal that is split vertically. Type something into the right pane.
   If everything works correctly, the audio is generated, sent to OBS and you should be able to hear it.


