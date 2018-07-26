# Accession Automated Testing Framework test and reference mods
# Danny Maclean
import ned 

import peck
import os
import shutil
import sys
import logging
import audioanalysis as latency
import yaml
log = logging.getLogger('ATAT')

"""
This tool is for testing Accession Mobile voice quality. It plays
audio recordings into one phone, programs network disruption on a router
the phones are connected to, and records the output audio (which has 
been sent over the disrupted network) to disk. It then calculates the audio
latency and produces a manual test plan for evaluating the audio quality 
offline. The program flow is as follows:

Create Log
Parse the 2 seperate config files
Concatenate silence to end of files
Set up the hardware ie connect to router and start stream
Create the output directory 
Confirm audio 
Create subdirectory
Play and record audio 
Calculate latency
Save and repeat
Terminate and Exit
"""

"""
# all variables used: 
# output_path, status, network_parameters, subdirectory_name, create_subdirectory, subdirectory_path
# output_path, recordings_directory
# log, fh, conditions, input_path, output_path, max_jitter_buffer_size, padded_audio_location, recordings_directory, subdirectory_path, 
# cross_correlation_latency, cross_correlation_coefficient, dict_key, latency_data

# setup_recording_directory(): you had mentioned that we should change this to not have a output directory withing the output path
I think it should becuse atat.py has the potential to create a lot of subdirectories. If the outpath given was to a directory with someother files then you would have a mess
for now I will leave this in unless you strongly disagree

"""
#magic vars
root_directory=os.getcwd()
max_jitter_buffer_size = 1000

def parse_config():
    """Parse config file. This initiates the input and 
    output global vaariables with paths for audio. This will also create 
    a directory of input files with silence padded onto the end to prevent
    the end of any files from being clipped
    Parameters None
    Returns input_path, output_path, max_jitter_buffer_size
    """
    global max_jitter_buffer_size
    with open("audio_config.yml") as config:
        config_data = yaml.load(config)
        input_path = config_data["input_path"]
        if input_path == None:
            input_path = os.getcwd + "\\Audio"
            log.info("Default audio path used: {}".format(input_path))
        else:
            if not os.path.exists(input_path):
                log.debug("input path is invalid: {}".format(input_path))
                print("Input path is invalid...Exiting...")
                log.debug("Input path is invalid...Exiting...")
                sys.exit()
        log.info("Input audio path is valid")
        output_path = config_data["output_path"]
        if output_path == None:
            output_path = os.getcwd()+"\\output"
            log.info("Default audio path used: {}".format(output_path))
        else:
            if not os.path.exists(output_path):
                log.debug("input path is invalid: {}".format(output_path))
                print("Output path is invalid...Exiting...")
                log.debug("Output path is invalid...Exiting...")
                sys.exit()
        log.info("output path entered valid")
        delay = config_data["delay"]
        if delay == None:
            log.info("No delay parameter specifed, default: 1000ms used")
            delay = max_jitter_buffer_size
            log.info("default delay used")
    return input_path, output_path, delay


def network_conditions_string(command):
    loss_string=""
    delay_string=""
    if command["loss"]["type"]=="gemodel":
        loss_string = "lossg{}".format(command["loss"]["value"])
    if command["loss"]["type"]=="random":
        loss_string = "lossr{}".format(command["loss"]["value"])
    if command["delay"]["time"]!=None:
        delay_string = "dly{}".format(command["delay"]["time"])
        if command["delay"]["jitter"]!=None:
            delay_string = delay_string + "_{}{}".format(command["delay"]["jitter"], command["delay"]["distribution"])
    return loss_string + "_" + delay_string


def setup_recording_directory(command, output_path):
    """Create a subdirectory within the output_path variable. The subdirectory name will
    be a combination of attributes from the status object
    Parameters 
    status - Network parameter class created by network disruption module
    output_path - the location to create the subdirectory within
    Returns subdirectory_path this is the path to the new directory that has been created 
    """
    network_parameters = network_conditions_string(command)
    subdirectory_name = "output_"+network_parameters
    try:
        os.mkdir(output_path+"\\"+subdirectory_name)
    except FileExistsError:
        pass    
    subdirectory_path = output_path+"\\"+subdirectory_name
    return subdirectory_path


def setup_output_directory(output_path):
    """Create an output directory in the location specified in the accompanying config file
    Parameters: output_path
    Returns recordings_directory
    """
    # If the directory doesn't exist, make the directory. If it does exist, clear it
    try:
        input("The directory - " + output_path + " - will be deleted. Press enter if you are okay with this or CTRL-C to exit")
    except KeyboardInterrupt:
        log.debug("Keyboard Interrupt encountered")
        print("Exiting...")
        ned.terminate()
        sys.exit()
    try:
        os.chdir(output_path)
        recordings_directory = output_path+"\\output"
        if not os.path.exists(recordings_directory):
            os.mkdir(recordings_directory)
        else:
            shutil.rmtree(recordings_directory)
            os.mkdir("output")
    except FileNotFoundError:
        print("The output path entered is not valid...Program will now exit...")
        log.debug("The outpath path entered cannot be traced")
        sys.exit()
    except PermissionError:
        print("The output path entered is not valid...Program will now exit...")
        log.debug("Encountered permission error when using output path")
        sys.exit()
    return recordings_directory


def ATAT():
    # instantiate ATAT.log
    try:
        os.remove("ATAT.log")
    except:
        pass
    log.setLevel(logging.DEBUG)
    fh = logging.FileHandler('ATAT.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    log.info('atat.log')

    # Parse Config data
    input_path, output_path, max_jitter_buffer_size = parse_config()


    # Setting up hardware, connecting to router and initiating audio stream
    log.info("Trying to connect to router")
    ned.init()
    log.info("Logged in to router")
    log.info("Creating audio stream")
    peck.audio_init()
    log.info("Created stream")
    
    # Pad silence to end of designated input data
    try:
        os.mkdir(root_directory+"\\temp_padded_audio")
    except FileExistsError:
        shutil.rmtree(root_directory+"\\temp_padded_audio")
        os.mkdir(root_directory+"\\temp_padded_audio")
    padded_audio_location = root_directory + "\\temp_padded_audio"
    log.info("concatenating {}ms of silence to input".format(max_jitter_buffer_size))
    peck.concatenate_silence(input_path, padded_audio_location, max_jitter_buffer_size)
    log.info("Concatenated Silence to end of input files, location: {}".format(padded_audio_location))

    # Create output directory at specified location
    recordings_directory=setup_output_directory(output_path)
    log.info("recordings directory setup at {}".format(recordings_directory))

    # Confirm with user that the audio is acceptable
    #peck.confirm_audio(padded_audio_location, "padded_A_eng_f1.wav")

    # Begin processing
    while ned.execute_next_command():
        command = ned.get_current_conditions()
        # Create subdirectory
        subdirectory_path = setup_recording_directory(command, recordings_directory)
        # Play and record the directory 
        peck.play_and_rec_directory(padded_audio_location, subdirectory_path)
        log.info("Played and recored audio")
        # Calculate the latency and log to output_data.yml in subdirectory  
        print("calculating latency")
        log.info("Calculating latency")
        cross_correlation_latency, cross_correlation_coefficient = latency.find_latency_values(padded_audio_location, subdirectory_path)
        log.info("cross correlation latency: {}, cross correlation coefficient: {}".format(cross_correlation_latency, cross_correlation_coefficient))
        dict_key = network_conditions_string(command)
        latency_data = {}
        latency_data[dict_key]={}
        latency_data[dict_key]["Time Latency"]=float(cross_correlation_latency)
        latency_data[dict_key]["Cross Correlation Coefficient"]=float(cross_correlation_coefficient)
        with open("output_data.yml", "w") as output_data:
            yaml.dump(latency_data, output_data, default_flow_style=False)
    # Delete the padded input the program created 
    shutil.rmtree(padded_audio_location)
    # Terminate hardware connection
    ned.terminate()
    peck.terminate()
    log.info("End Process")


if __name__ == "__main__":
    ATAT()
