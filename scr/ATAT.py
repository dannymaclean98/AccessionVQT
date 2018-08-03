# Accession Automated Testing Framework test and reference mods
# Danny Maclean
import ned 
import peck
import os
import shutil
import sys
import logging
import audioanalysis as aa
import yaml
import numpy as np


"""
atat.py - Accession Testing Automated Tool

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
root_directory=os.getcwd()
DEFAULT_DELAY = 1000

#Global Constants
CONFIG_FILE = "audio_config.yml"
INPUT_SUBDIR = "input"
OUTPUT_SUBDIR="output"
TEMP_PADDED_AUDIO_LOCATION="temp_padded_audio"

#Config file field names
INPUT_PATH = "input_path"
DELAY="delay"
LOSS="loss"
TYPE="type"
GEMODEL="gemodel"
RANDOM="random"
VALUE="value"
TIME="time"
JITTER="jitter"
DISTRIBUTION="distribution"
LOSS_GEMODEL_NETWORK_STRING="lossg{}"
LOSS_RANDOM_NETWORK_STRING="lossr{}"
DELAY_NETWORK_STRING="dly{}"
DELAY_NETWORK_STRING_SUBSTRING="_{}{}"
LOSS_STRING_DELAY_STRING_SEPERATOR="_"


def _network_conditions_string(command):
    # Use to create a unique string based on netem conditions. 
    # strong format - loss{}{}_{}_dly{}_{}{}.format(loss type, loss value, delay time, delay distribution, distribution value)
    logging.info("Enter: _network_conditions_string")
    loss_string=""
    delay_string=""
    if command[LOSS][TYPE]==GEMODEL:
        gemodel_string = command[LOSS][VALUE].replace(" ", LOSS_STRING_DELAY_STRING_SEPERATOR)
        loss_string = LOSS_GEMODEL_NETWORK_STRING.format(gemodel_string)
    if command[LOSS][TYPE]==RANDOM:
        loss_string = LOSS_RANDOM_NETWORK_STRING.format(command[LOSS][VALUE])
    if command[DELAY][TIME]!=None:
        delay_string = DELAY_NETWORK_STRING.format(command[DELAY][TIME])
        if command[DELAY][DISTRIBUTION]!=None:
            delay_string = delay_string + DELAY_NETWORK_STRING_SUBSTRING.format(command[DELAY][DISTRIBUTION], command[DELAY][JITTER])
    return loss_string + LOSS_STRING_DELAY_STRING_SEPERATOR + delay_string
    logging.info("Exit: _network_conditions_string")


def _create_recording_directory(command, output_path):
    # Create subdirectory for specific conditons
    logging.info("Enter: _network_conditions_string")
    network_parameters = _network_conditions_string(command)
    subdirectory_name = "output_"+network_parameters
    try:
        os.mkdir(os.path.join(output_path, subdirectory_name))
    except FileExistsError:
        pass    
    subdirectory_path = os.path.join(output_path, subdirectory_name)
    logging.info("Exit: _network_conditions_string")
    return subdirectory_path


def _remove_dir_keep_head_folder(output_path):
    # remove all elements below the node specified
    logging.info("Enter: _remove_dir_keep_head_folder")
    for path in os.listdir(output_path):
        if os.path.isdir(os.path.join(output_path, path)):
            shutil.rmtree(os.path.join(output_path, path))
        else:
            os.remove(os.path.join(output_path, path))
    logging.info("Exit: _remove_dir_keep_head_folder")


def _create_output_directory(output_path):
    # Delete everything in output_path and make a subdirectory labeled 'output_path' 
    # If the directory doesn't exist, make the directory. If it does exist, clear it
    logging.info("Enter: _create_output_directory")
    try:
        recordings_directory = os.path.join(output_path, OUTPUT_SUBDIR)
        os.mkdir(recordings_directory)
    except FileExistsError:
        try:
            input("The contents of - " + output_path + " - will be deleted. Press enter if you are okay with this or CTRL-C to exit")
            _remove_dir_keep_head_folder(output_path)
            recordings_directory = os.path.join(output_path, OUTPUT_SUBDIR)
            os.mkdir(recordings_directory)
        except KeyboardInterrupt:
            logging.debug("Keyboard Interrupt encountered")
            print("Exiting...")
            ned.terminate()
            sys.exit()
    except FileNotFoundError:
        print("The output path entered is not valid...Program will now exit...")
        logging.debug("The outpath path entered cannot be traced")
        sys.exit()
    except PermissionError:
        print("Permission error encountered while trying to delete output directory")
        logging.debug("Encountered permission error when using output path")
        sys.exit()
    logging.info("Exit: _create_output_directory")
    return recordings_directory


def _calculate_average_latency(correlation_sample_log, rate_log):
    # Divde each sample latency by it's corresponding rate
    # return the average of all points
    average_array=[]
    for index, data_point in enumerate(correlation_sample_log):
        latency_time_value= data_point/(rate_log[index])
        average_array.append(latency_time_value)
    return np.mean(average_array)
    

def parse_config():
    """Parse config file. This initiates the input and 
    output global variables with paths for audio. This 
    will also create a directory of input files with silence 
    padded onto the end to prevent the end of any files from being 
    truncated  

    Parameters:
    None
    Returns:
    input_path:         The input path for audio specified in audio_config.yml
                        If nothing is specified, the default audio directory in 
                        the root directory is returned          
    output_path:        The output path for saving recorded audio. If nothing
                        is specified then the root directory is used
    delay:              The max delay that can be introduced in the  call. If 
                        nothing is specified then the default of 1000ms is used
    """
    logging.info("Enter: parse_config")
    with open(CONFIG_FILE) as config:
        config_data = yaml.load(config)
        input_path = config_data[INPUT_PATH]
        if input_path == None:
            input_path = os.path.join(os.getcwd, INPUT_SUBDIR) 
            logging.info("Default audio path used: {}".format(input_path))
        else:
            if not os.path.exists(input_path):
                logging.debug("input path is invalid: {}".format(input_path))
                print("Input path is invalid...Exiting...")
                logging.debug("Input path is invalid...Exiting...")
                sys.exit()
        logging.info("Input audio path is valid")
        output_path = config_data["output_path"]
        if output_path == None:
            output_path = os.path.join(os.getcwd(), OUTPUT_SUBDIR)
            logging.info("Default audio path used: {}".format(output_path))
        elif os.path.exists(output_path):
                try: 
                    os.mkdir(output_path)
                except:
                    print("Output path is invalid...Exiting...")
                    logging.debug("Output path is invalid...Exiting...")
                sys.exit()
        if output_path==input_path:
            logging.debug("output path and input path were identical")
            print("output path and input path were identical")
            sys.exit()
        logging.info("output path entered valid")
        delay = config_data[DELAY]
        if delay == None:
            logging.info("No delay parameter specifed, default: 1000ms used")
            delay = DEFAULT_DELAY
            logging.info("default delay used")
        elif type(delay) is not int:
            print("Non integer input for delay in audio_config.yml. Exiting")
            logging.debug("Non integer input for delay in audio_config.yml. Exiting")
            sys.exit()
        elif delay < 0:
            print("A negative delay value was entered. Exiting")
            logging.debug("A negative delay value was entered")
            sys.exit()
    logging.info("Exit: parse_config")
    return input_path, output_path, delay


def atat():
    # Parse Config data
    input_path, output_path, max_jitter_buffer_size = parse_config()

    # Setting up hardware, connecting to router and initiating audio stream
    logging.info("Trying to connect to router")
    ned.init()
    logging.info("Logged in to router")
    logging.info("Creating audio stream")
    peck.audio_init()
    logging.info("Created stream")
    
    # Pad silence to end of designated input data, store in root directory
    # this is done so files are not double crawled
    try:
        os.mkdir(os.path.join(root_directory+TEMP_PADDED_AUDIO_LOCATION))
    except FileExistsError:
        shutil.rmtree(os.path.join(root_directory+TEMP_PADDED_AUDIO_LOCATION))
        os.mkdir(os.path.join(root_directory+TEMP_PADDED_AUDIO_LOCATION))
    padded_audio_location = os.path.join(root_directory+TEMP_PADDED_AUDIO_LOCATION)
    logging.info("concatenating {}ms of silence to input".format(max_jitter_buffer_size))
    peck.concatenate_silence(input_path, padded_audio_location, max_jitter_buffer_size)
    logging.info("Concatenated Silence to end of input files, location: {}".format(padded_audio_location))

    # Create output directory at specified location
    output_directory=_create_output_directory(output_path)
    logging.info("output directory setup at {}".format(output_directory))

    # Confirm with user that the audio is acceptable
    peck.confirm_audio(padded_audio_location)
    calculate_latency=False
    while True:
        answer=input("During processing, latency between files is calculcated for analytical purposes.\n" 
        "Doing so takes roughly 20 minutes per 20 audio files. Would you like to do so? y/n \n"
        "(typing 'n' will simply play and record files without calculating latency)\n")
        if "Y" or "y" in answer:
            calculate_latency=True
            break
        if "N" or "n" in answer:
            calculate_latency=False
            break

    # Begin processing
    while ned.execute_next_command():
        command = ned.get_current_conditions()
        # Create subdirectory
        subdirectory_path = _create_recording_directory(command, output_directory)
        # Play and record the directory 
        peck.play_and_rec_directory(padded_audio_location, subdirectory_path)
        logging.info("Played and recored audio")
        # Calculate the latency and log to output_data.yml in subdirectory  
        if calculate_latency:
            print("calculating latency")
            logging.info("Calculating latency")
            rate_log, correlation_sample_log, correlation_coefficient_log = aa.find_latency_values(padded_audio_location, subdirectory_path)
            cross_correlation_latency = _calculate_average_latency(correlation_sample_log,rate_log)
            cross_correlation_coefficient = np.mean(correlation_coefficient_log)
            logging.info("cross correlation latency: {}, cross correlation coefficient: {}".format(cross_correlation_latency, cross_correlation_coefficient))
            dict_key = _network_conditions_string(command)
            latency_data = {}
            latency_data[dict_key]={}
            latency_data[dict_key]["Time Latency"]=float(cross_correlation_latency)
            latency_data[dict_key]["Cross Correlation Coefficient"]=float(cross_correlation_coefficient)
            with open(os.path.join(output_path, "output_data.yml"), "a") as output_data:
                yaml.dump(latency_data, output_data, default_flow_style=False)
    # Delete the padded input the program created 
    shutil.rmtree(padded_audio_location)
    # Terminate hardware connection
    ned.terminate()
    peck.terminate()
    logging.info("End Process")


if __name__ == "__main__":
    # instantiate ATAT.log
    logging.basicConfig(filename="atat.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(module)s line: %(lineno)d: %(message)s")
    logging.info("Enter: main")
    atat()
