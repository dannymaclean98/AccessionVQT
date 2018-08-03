# Play and record Module
# Danny Maclean

import numpy as np
import scipy.io.wavfile as wf
import sounddevice as sd
import os
import yaml
import sys
import itertools
import logging 
import warnings




"""
peck.py - Play and Record Library

This method is built to play and record .wav files. It is a wrapper to sounddevice and scipy
and provides functions to make audio interfacing simple
Responsibilites
1)Parse config
2)Setup stream
3)confirm the stream
4)Play and record a directory

"""
logging.basicConfig(filename="peck.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(module)s line: %(lineno)d, %(message)s")
warnings.filterwarnings("error")
#String constants
TEST_WAV = "test_signal.wav"
MAX_INPUT_CHANNELS = "max_input_channels"
MAX_OUTPUT_CHANNELS = "max_output_channels"
NAME = "name"
USB_PNP = "USB PnP"
HOSTAPI = "hostapi"
WAV = "wav"
#Numerical constants
SAMPLE_RATE = 16000
HOSTAPI_NUM = 1
SIGNIFICANT_VALUE_FOR_AUDIO = 1000
# file globals
root_directory = os.getcwd()
stream = sd.Stream()


def audio_init():
    """Initiate an audio stream between two phones in a call connected to the computer
    Parameters: 
    None
    Returns:
    None
    """
    logging.info("Enter: audio_init")
    # If the first pair contains audio set the flag and exit
    # If the second pair contains audio set the flag and exit
    audio_initialized = False
    while not audio_initialized:
        usb_combinations = _find_USB_PnP_combinations()
        for combination in usb_combinations:    
            _open_stream(combination)
            rate, test_signal_input_array= wf.read(os.path.join(root_directory, TEST_WAV))
            rate, test_signal_output_array = play_and_rec_file(root_directory, TEST_WAV)
            # take average of absolute value of all elements in an array
            if np.average(np.absolute(test_signal_output_array)) > SIGNIFICANT_VALUE_FOR_AUDIO:
                logging.info("test signal correlation between input and output was high enough to suggest a call has been started")
                _print_device_pair_info(combination)
                audio_initialized = True
                break
        # check with the user that an error hasn't been made
        call_check_response = input("It does not appear audio is playing. Please start a call or see the trouble shooting section in README.TXT and press enter\nOr type okay to continue anyway... ")
        if "okay" in call_check_response:
            logging.info("User has opted to override audio initalizing. Now assuming a call is started")
            break
    logging.info("Exit: audio_init")


def confirm_audio(input_path):
    """Play example audio for the user. Will play repeatedly 
    until the user confirms they are happy with the audio connection
    Parameters 
    input_path:                     absolute path to a directory with at least a single wav file. 
                                    The first wav file, encountered alphabetically, will be 
                                    used to play and confirm the audio
    Returns:
    None
    """
    logging.info("Enter: confirm_audio")
    input("We’re now going to test the audio levels are acceptable. Please listen carefully to the following output recording. Press enter to continue")
    logging.info("Example message now being played")
    file_list = os.listdir(input_path)
    file_name = _find_first_wav(file_list) 
    play_file(input_path, file_name)
    while True:
        answer = str(input("Was the audio acceptable? Y/N\n"))
        if ("y" in answer) or ("Y" in answer):
            logging.info("audio was acceptable to user ear")
            break
        elif ("n" in answer) or ("N" in answer):
            input(
                "Please raise or lower your volume level or refer to the trouble"
                "shooting section in "
                "https://metacom2.metaswitch.com/confluence/display/~dm2/Accession+Testing+Automated+Tool+%28ATAT%29+Manual"
                " and press enter to listen to an example again")
            logging.info("audio was not clear, attempting to confirm audio again")
            print("An example message will now be played...")
            play_file(input_path, file_name)
    logging.info("Exit: confirm_audio")


def concatenate_silence(input_path, output_path, silence_in_ms):
    """Append a buffer of silence to each of the corresponding 
    inputs.Files in output can be found as "padded_" + original file
    name in output_path
    Paramters:
    input_path:         the directory or audio in which to append
                        silence to the end
    output_path:        the directory to write the new audio too
    silence_in_ms:      the size of silence, in seconds, to write
                        to the end of the input directory
    Returns:
    None
    """
    logging.info("Enter: concatenate_silence")
    if input_path==output_path:
        logging.debug("input and output paths passed in are identical. "
        "Please save the audio to a different location. Exititng")
        print("input and output paths passed in are identical. "
        "Please save the audio to a different location. Exititng")
        sys.exit()
    padded_buffer_size = int(silence_in_ms * SAMPLE_RATE / 1000)
    silence_array = np.zeros((padded_buffer_size,), dtype=np.int16)
    for dirpath, dirnames, filenames in os.walk(input_path):
        for file_ in filenames:
            if (WAV not in file_):
                logging.info("A non wav file was encountered and thus not processed: {}".format(file_))
                continue
            rate, data = wf.read(os.path.join(dirpath, file_))
            res = np.concatenate((data, silence_array))           
            wf.write(os.path.join(output_path, "padded_"+file_), rate, res)
    logging.info("Exit: concatenate_silence")
                

def play_and_rec_directory(input_path, output_path):
    """Play each .wav file specified in the input directory 
    and record the output simultaneously
    Parameters: 
    input_path:         Location of input .wav files to be transmitted
    output_path:        Location for output .wav files 
                        that are recorded with output_ appended to 
                        the start of the string
    Returns None
    """
    # DAM_MRR - output keyword and hard coded string, come back and visit
    logging.info("Enter: play_and_rec_directory")
    for dirpath, dirnames, filenames in os.walk(input_path):
        for file_ in filenames:
            if WAV not in file_:
                logging.info("A non .wav file was encountered and thus not used:"
                " {}".format(file_))
                continue
            print("processing... ", file_)
            rate, data = wf.read(os.path.join(dirpath, file_))
            output_array = sd.playrec(
                data, rate, channels=1, blocking=True)
            sd.wait()
            output_location = output_path+"\\"+str("output_"+file_)
            print(output_location, "\nSuccess...\n")
            wf.write(output_location, int(rate), output_array)
    logging.info("Exit: play_and_rec_directory")


def terminate():
    """Close the audio stream
    and delete the folder of padded wav 
    files that was created
    Parameters:
    None
    Returns:
    None 
    """
    logging.info("Enter: terminate")
    global stream
    logging.info("stream closed")
    stream.close()
    logging.info("Exit: terminate")


def play_file(input_path, file_name):
    """Play a .wav file in the current 
    working directory
    Parameters: 
    input_path:         the location of the file to 
                        be played
    file_name:          the name of the file in the 
                        input_path to be played
    Returns None
    """
    logging.info("Enter: play_file")
    print("playing file...")
    rate, data = wf.read(os.path.join(input_path, file_name))
    sd.play(data, rate)
    sd.wait()
    logging.info("Exit: play_file")


def play_and_rec_file(file_path, file_):
    """Plays a .wav file in the current working directory and 
    records/saves the output in the current directory
    Parameters: 
    file_path:      absolute path to dir location of file_
    file_:          name of file in current working directory
    Returns:
    output_array:   numpy array of the recording of the file
    """
    logging.info("Enter: play_and_rec_file")
    rate, data = wf.read(os.path.join(file_path, file_))
    output_array = sd.playrec(data, rate, channels=1, blocking=True)
    sd.wait()
    wf.write(os.path.join(file_path, "test_"+file_), rate, output_array)
    rate, output_array = wf.read(os.path.join(file_path, "test_"+file_))
    os.remove(os.path.join(file_path, "test_"+file_))
    logging.info("Exit: play_and_rec_file")
    return rate, output_array
    

# Internal Methods
def _find_first_wav(file_list):
    logging.info("Enter: find_first_wav")
    for file_ in file_list:
        if WAV in file_:
            logging.info("Exit: first_first_wav")
            return file_


def _print_device_pair_info(pair):
    logging.info("Enter: print_device_pair_info")
    device_list = sd.query_devices()
    for device_index, device in enumerate(device_list):
        if device_index == pair[0]:
            if device[MAX_INPUT_CHANNELS] > 0:
                print("The device being used for input is: {}".format(device[NAME]))
                print("If audio is not playing, please confirm that you are listening to this device on Audacity\n")
        if device_index == pair[1]:
            if device[MAX_OUTPUT_CHANNELS] > 0:
                print("The device being used for output is: {}".format(device[NAME]))
                print("If audio is not playing, please confirm that your computer's audio output is set to this device\n")
    logging.info("Exit: print_device_pair_info")


def _sub_string_match(first,second):
    #Helper method to truncate the start of the two device ID strings. The start contains the words 
    #Speakers and Microphones and in parenthesis the actual device name. 
    #To check if the two devices are the same device (and not the same device with a different label), 
    #use this method 
    logging.info("Enter: sub_string_match")
    first_start = first.index("(")
    second_start = second.index("(")
    if first[first_start:]==second[second_start:]:
        logging.info("Exit: sub_string_match, True")
        return True
    else: 
        logging.info("Exit: sub_string_match, False")
        return False


def _find_USB_PnP_combinations():
    #Internal Method to search through device list and find USB PnP device combinations
    #Parameters None
    #Returns first_pair, second pair
    #format: [input_device_number, output_device_number]
    logging.info("Enter: find_USB_PnP_combinations")
    devices = sd.query_devices()
    # first add all USB PnP devices to a list. the index needs to be saved to initiate stream
    usb_pnp=[]
    for index, device in enumerate(devices):
        if (USB_PNP in device[NAME]) and (device[HOSTAPI] == HOSTAPI_NUM):
            logging.info("usb pnp device detected, device: {}".format(device))
            usb_pnp.append([index, device])
    if len(usb_pnp)==0:
        print("No phones are plugged in, please plug in the USB PnP devices and"
        " try again\nNow exiting...")
        logging.debug("No USB PnP devices were detected, program exiting")
        sys.exit()
    # remove combinations from the list that are 1) both inputs 2) both outputs 3) have the same name
    # Next remove USB combinations that will never create a valid connection
    # When pairing USB devices, every device is listed twice, once as a speaker and once as a microphone
    # Thus creating three invalid device combinations
    # 1) Device One Speakers to Device Two Speakers
    # 2) Device One Microphone to Device Two Microphone
    # 3) Device One Speakers to Device One Microphone
    usb_combinations_all = list(itertools.combinations(usb_pnp, 2))
    usb_combinations_to_remove=[]
    for i, combination in enumerate(usb_combinations_all):
        if _sub_string_match(str(combination[0][1][NAME]),str(combination[1][1][NAME])):
            logging.info("Invalid USB PnP combination removed: {}".format(combination))
            usb_combinations_to_remove.append(i)
        elif combination[0][1][MAX_INPUT_CHANNELS]==combination[1][1][MAX_INPUT_CHANNELS]:
            logging.info("Invalid USB PnP combination removed: {}".format(combination))
            usb_combinations_to_remove.append(i)
        elif combination[0][1][MAX_OUTPUT_CHANNELS]==combination[1][1][MAX_OUTPUT_CHANNELS]:
            logging.info("Invalid USB PnP combination removed: {}".format(combination))
            usb_combinations_to_remove.append(i)
    logging.info("usb combinations that will not be checked at indices: {}".format(usb_combinations_to_remove))
    usb_combinations=[[relevant_combination[0][0], relevant_combination[1][0]] for index, relevant_combination in enumerate(usb_combinations_all) if index not in usb_combinations_to_remove]
    logging.info("Usb pnp combinations to be tested: {}".format(usb_combinations))
    logging.info("Exit: find_USB_PnP_devices")
    return usb_combinations


def _open_stream(pair):
    #Internal Method to query devices and initiate stream with USB PnP output channel and USB PnP input channel
    #Parameters: pair - list of input/output objects to initiate stream [input_device_num, output_device_num]
    #Returns: None
    logging.info("Enter: open_stream")
    global stream
    logging.info("Stream opened at {}".format(pair))
    stream = sd.Stream(samplerate=SAMPLE_RATE, device=(pair[0], pair[1]), channels=1)
    stream.start()
    logging.info("Exit: open_stream")





















