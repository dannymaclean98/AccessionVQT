===README===

ATAT.py script:
Hardware Setup
1)Plug the mini router and two USB PNP devices into your laptop.
2)Connect the 2 phones and PC to the mini router wifi (GL-AR300M-219-NOR)
Note: plug the grey cable(2 rings) into the samsung and the black(3 ring) to the iphone

Software Setup
1) Open the config.yml file
	a) The login credentials for the accompanying router are already input. Please change if using a different router
2) Enter (optional) input and output paths
	a)Note: the default input and output paths are in the root directory of the repository
3) Enter some network conditions to test that call under 

4) cd into the root directory and type "ATAT.py" and hit enter

5) Next open Accession and press call #21 from the iphone

6) an example message will be played. Using Audacity, set the input to USB (2- ...) and you can listen  to the call and verify the quality

7) press "y" if acceptable and "n" to hear the message again

8) once acceptable, hitting "y" will allow all messages to be played in entirety 

Trouble shooting:
If you cannot hear the audio in audacity, verify that both phones are using the audio cables for audio. 
Try unplugging the chords and replugging them 


manual_test.py script:
1) cd to Testing directory and run manual_test.py and follow the instructions on the screen
2) The script offers two different modes: Testing or Grading
3) The testing mode will prompt you to enter two output directories and will create an ABX test from them with the corresponding answer key
4) The grading mode will take the users answers and answer key to create analytics about the test 