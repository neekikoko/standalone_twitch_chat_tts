# Installation Part 1

1. Copy the file ``.env.example``  and name it ``.env``
2. Install python 3.12 and pip on your system.
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

## Please ensure the piper part works before continuing with installation part 2. Test it like so:
1. In .env, set ``TEST_WITHOUT_REDEEMS=true``
2. Double-click the file ``start.bat``.
   1. This should open a Windows terminal that is split vertically. Type something into the right pane.
   If everything works correctly, the audio is generated, sent to OBS and you should be able to hear it.

# Installation Part 2
1. In .env, set ``TEST_WITHOUT_REDEEMS=false``
2. In .env set TWITCH_CHANNEL_NAME to your channel name.
3. In .env set TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET. Please acquire it like so:
   1. Visit https://dev.twitch.tv/console and log in. 
   2. Click on the menu point “Applications” 
   3. Click on “+ Register Your Application” 
   4. Enter “Chat Overlay” into the field “Name” 
   5. Enter “http://localhost:8787/callback” into the field “OAuth Redirect URLs”. 
   6. Enter “Application Integration” into the field “Category” 
   7. As “Client Type” set “Confidential” 
   8. Click on “Create” 
   9. You will be redirected to a page where you see your newly created application. Click on “Manage”. 
   10. Copy the text inside the field titled “Client ID” and set it as TWITCH_CLIENT_ID inside the .env file.
   11. At the bottom of this page, you'll see a button labeled "New Secret".
   Press it and a text string similar to your Client ID will be displayed. Copy this and set it as TWITCH_CLIENT_SECRET inside the .env file.
4. In .env set TWITCH_OAUTH_TOKEN. Please acquire it like so:
   1. Open a terminal window inside the helper_scripts folder.
   2. In the terminal, enter ``py .\get_twitch_token.py``.
   3. Your browser will open and an OAuth authentication process will start, requiring you to login. Please do so.
   4. After successful OAuth authentication, the terminal window will display ``Access Token:`` and underneath your newly generated OAuth access token.
   5. Copy this and set it as TWITCH_OAUTH_TOKEN inside the .env file.
5. In .env set TWITCH_BROADCASTER_ID. Please acquire it like so:
   1. Open a terminal window inside the helper_scripts folder.
   2. In the terminal, enter ``py .\get_twitch_broadcaster_id.py``.
   3. Your terminal will display ``Broadcaster ID:`` and after that your Broadcaster ID.
   4. Copy this and set it as TWITCH_BROADCASTER_ID inside the .env file.
6. In .env set REWARD_TITLE to the name of your point redeem.

