# Play and record Module
# Danny Maclean

import numpy
import scipy.io.wavfile as s
import sounddevice as sd
import os
import yaml
import sys
import itertools
import logging 
import warnings
warnings.filterwarnings("error")
log = logging.getLogger('ATAT')
# Responsibilites
# 1)Parse config
# 2)Setup stream
# 3)confirm the stream
# 4)Play and record a directory

"""
line 133
"""


# file globals
root_directory = os.getcwd()
stream = sd.Stream()

def audio_init():
    """Initiate an audio stream between two phones in a call, connected via USB PnP cables
    Parameters: None
    Returns None
    """
    # If the first pair contains audio set the flag and exit
    # If the second pair contains audio set the flag and exit
    audio_initialized = False
    try:
        while True:
            usb_combinations = find_USB_PnP_combinations()
            for combination in usb_combinations:    
                open_stream(combination)
                rate, test_signal_input_array= s.read(root_directory+"\\test_signal.wav")
                rate, test_signal_output_array = play_and_rec_file(root_directory, "test_signal.wav")
                # cross correlate the signals, if correlation coefficient above 0 exists, they are correlated
                test_signal_correlation_array=numpy.correlate(test_signal_input_array, test_signal_output_array, "full")
                for data_point in test_signal_correlation_array:
                    if data_point > 0:
                        log.info("test signal correlation between input and output was high enough to suggest a call has been started")
                        audio_initialized=True
                        raise StopIteration
            # check with the user that an error hasn't been made
            call_check_response = input("It doesn't seem a call has been started. Please start a call and press any key\nOr type okay to continue anyway... ")
            if "okay" in call_check_response:
                log.info("User has opted to override audio initalizing. Now assuming a call is started")
                raise StopIteration
    except StopIteration:
        log.info("Audio initialized, contining")


def confirm_audio(input_path, file_name):
    """Play example audio for the user. Will play repeatedly until the user confirms they are happy with the audio connection
    Parameters None
    Returns None
    """
    while True:
        user_ready=input("We’re now going to test the audio levels are acceptable. Please listen carefully to the following output recording. Ready? Y/N\n")
        if ("y" in user_ready) or ("Y" in user_ready):
            log.info("Example message now being played")
            break
    play_file(input_path, file_name)
    while True:
        answer = str(input("Was the audio acceptable? Y/N\n"))
        if ("y" in answer) or ("Y" in answer):
            log.info("audio was acceptable to user ear")
            break
        elif ("n" in answer) or ("N" in answer):
            input(
                "Please raise or lower your volume level and press enter to listen to an example again")
            log.info("audio was not clear, attempting to confirm audio again")
            print("An example message will now be played...")
            play_file(input_path, file_name)

# coding problem to be addressed!
# os.walk crawls all files in a dir. even if they are created in the for loop that is crawling the directory
# so if the input_path and output_path are the same then new files will be added as the space is crawled
# thus files I don't want crawled...get crawled! 
# to cope I use the if statement in line 151 which looks out for a keyword "padded". 
# Any objections/ suggestions?
# Note: Same problem encountered in adjust_files() in audiotesting\wav_tuner.py
def concatenate_silence(input_path, output_path, silence_in_ms):
    """Append a buffer of silence to each of the corresponding inputs.
    Files in output can be found as "padded_" + original file name
    Paramters: None
    Returns None
    """
    padded_buffer_size = int(silence_in_ms * 16)
    silence_array = numpy.zeros((padded_buffer_size,), dtype=numpy.int16)
    for dirpath, dirnames, filenames in os.walk(input_path):
        for file_ in filenames:
            if ("wav" not in file_):
                log.info("A non wav file was encountered and thus not processed: {}".format(file_))
                continue
            rate, data = s.read(dirpath+"\\"+file_)
            res = numpy.concatenate((data, silence_array))
            output_location = output_path+"\\padded_"+file_               
            s.write(output_location, rate, res)
                

def play_and_rec_directory(input_path, output_path):
    """Play each .wav file specified in the input directory and record the output simultaneously
    Parameters: 
    output_location_specification - this is a list of the network parameters that the input experienced 
    format: [[loss value, delay value],...]
    input_path - Location of input .wav files to be transmitted
    output_path - Location for output .wav files that are recorded
    Returns None
    """
    for dirpath, dirnames, filenames in os.walk(input_path):
        for file_ in filenames:
            if "wav" not in file_:
                log.info("A non .wav file was encountered and thus not used: {}".format(file_))
                continue
            print("processing... ", file_)
            rate, data = s.read(input_path+"\\"+file_)
            output_array = sd.playrec(
                data, rate, channels=1, blocking=True)
            sd.wait()
            output_location = output_path+"\\"+str("output_"+file_)
            print(output_location, "\nSuccess...\n")
            s.write(output_location, int(rate), output_array)


def terminate():
    """Close the audio stream
    and delete the folder of padded wav files that was created
    Parameters: None
    Returns: None 
    """
    global stream
    log.info("stream closed")
    stream.close()


def play_file(input_path, file_name):
    """Play a .wav file in the current working directory
    Parameters: file_ - name of file to be played
    Returns None
    """
    print("playing file...")
    rate, data = s.read(input_path+"\\"+file_name)
    sd.play(data, rate)
    sd.wait()


def play_and_rec_file(file_path, file_):
    """Plays a .wav file in the current working directory and records/saves the output in the current directory
    Parameters: 
    file_path - absolute path to dir location of file_
    file_ - name of file in current working directory
    Returns output_array - numpy array of the recording of the file
    """
    rate, data = s.read(file_path+"\\"+file_)
    output_array = sd.playrec(data, rate, channels=1, blocking=True)
    sd.wait()
    s.write(file_path+"\\"+"test_"+file_, rate, output_array)
    rate, output_array = s.read(file_path+"\\"+"test_"+file_)
    os.remove(file_path+"\\"+"test_"+file_)
    return rate, output_array
    

def sub_string_match(first,second):
    first_start = first.index("(")
    second_start = second.index("(")
    if first[first_start:]==second[second_start:]:
        return True
    else: 
        return False


def find_USB_PnP_combinations():
    """Internal Method to search through device list and find USB PnP device combinations
    Parameters None
    Returns first_pair, second pair
    format: [input_device_number, output_device_number]"""
    devices = sd.query_devices()
    # first add all USB PnP devices to a list. the index needs to be saved to initiate stream
    usb_pnp=[]
    for index, device in enumerate(devices):
        if ("USB PnP" in device["name"]) and (device["hostapi"] == 1):
            log.info("usb pnp device detected, device: {}".format(device))
            usb_pnp.append([index, device])
    if len(usb_pnp)==0:
        print("No phones are plugged in, please plug in the USB PnP devices and try again\nNow exiting...")
        log.debug("No USB PnP devices were detected, program exiting")
        sys.exit()
    # remove combinations from the list that are 1) both inputs 2) both outputs 3) have the same name
    usb_combinations_all = list(itertools.combinations(usb_pnp, 2))
    usb_combinations_to_remove=[]
    for i, combination in enumerate(usb_combinations_all):
        if sub_string_match(str(combination[0][1]["name"]),str(combination[1][1]["name"])):
            usb_combinations_to_remove.append(i)
        elif combination[0][1]["max_input_channels"]==combination[1][1]["max_input_channels"]:
            usb_combinations_to_remove.append(i)
        elif combination[0][1]["max_output_channels"]==combination[1][1]["max_output_channels"]:
            usb_combinations_to_remove.append(i)
    log.info("usb combinations that will not be checked at indices: {}".format(usb_combinations_to_remove))
    usb_combinations=[[relevant_combination[0][0], relevant_combination[1][0]] for index, relevant_combination in enumerate(usb_combinations_all) if index not in usb_combinations_to_remove]
    log.info("Usb pnp combinations to be tested: {}".format(usb_combinations))
    print(usb_combinations)
    return usb_combinations


def open_stream(pair):
    """Internal Method to query devices and initiate stream with USB PnP output channel and USB PnP input channel
    Parameters: pair - list of input/output objects to initiate stream [input_device_num, output_device_num]
    Returns: None
    """
    global stream
    log.info("Stream opened at {}".format(pair))
    stream = sd.Stream(samplerate=16000, device=(pair[0], pair[1]), channels=1)
    stream.start()





















