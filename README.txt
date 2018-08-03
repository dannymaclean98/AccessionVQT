===README===

Install Dependecies 
Run "pip install -r REQUIREMENTS.txt"
Or alternatively pip install numpy, scipy, sounddevice, openpyxl


ATAT.py script:
Hardware Setup
1)Plug the mini router and two USB PNP devices into your laptop.
2)Connect the 2 phones and PC to the mini router wifi (GL-AR300M-219-NOR)
Note: plug the grey cable(2 rings) into the samsung and the black(3 ring) to the iphone

Software Setup
1) Open the router_config.yml file
	a) The login credentials for the accompanying router are already input. Please change if using a different router
2) In router_config.yml file, enter network parameters to test under

3)  Open audio_config.yml file and enter (optional) input and output paths
	a)Note: the default input and output paths are in the root directory
of the repository. See the spec for details on default audio

4) cd into the root directory and type "atat.py" and hit enter

5) Start a call between the two phones plugged in.

6) an example message will be played. The input and output devices are printed
to the screen. To listen to the audio, open Audacity and set the 'microphone'
device to the input device that is printed to the screen. If audio cannot be
heard, please see the trouble shooting section below

7) press "y" if acceptable and "n" to hear the message again

8) once acceptable, hitting "y" will allow all messages to be played in entirety 

Trouble shooting:
If you cannot hear the audio in audacity, verify that both phones are using the audio cables for audio. 
Is your computer using the correct output device for audio
Is your computer using the correct input device for audio
Try unplugging the chords and replugging them 
There is a button on each USB PnP chord, click this button if the phones are
not using the cables for audio


manual_test.py script:
1) cd to audiotesting and run manualtest.py with the two command line
arguments, -s1 and -s2.
2) use manualtest.py -h for help with optional command line arguments

grade.py
1) cd to audiotesting and run grade.py
2) use grade.py -h for help with optional command line arguments








