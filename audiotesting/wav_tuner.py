#Latency comparison

import numpy
import scipy
import scipy.io.wavfile as s
import sounddevice as sd
import os
import yaml
import sys
import shutil
import soundfile
import warnings
warnings.filterwarnings("error")

root_directory=os.getcwd()
adjusted_file_path=""
file_pairs = []

# Note: Positive offset indicates that signal 2 was delayed
    # Negative offset indicates that siganl one was delayed 

def collect_file_pairs(scenario_one, scenario_two):
    global file_pairs
    scenario_one_filenames=[]
    scenario_two_filenames=[]
    for dirpath,dirnames,filenames in os.walk(scenario_one):
            if(len(filenames)!=0):
                for file_ in filenames:
                    if "wav" in file_:
                        scenario_one_filenames.append(file_)

    for dirpath,dirnames,filenames in os.walk(scenario_two):
            if(len(filenames)!=0):
                for file_ in filenames:
                    if "wav" in file_:
                        scenario_two_filenames.append(file_)
    file_pairs = [[file_in, file_out] for file_in, file_out in zip(scenario_one_filenames, scenario_two_filenames)]


def match_lengths(scenario_one, scenario_two, file_zip):
    for file_pair in file_zip:
        # read data
        rate, scenario_one_data=s.read(file_pair[0])
        rate, scenario_two_data=s.read(file_pair[1])
        # find which one is longer and append silence to shorter array
        if len(scenario_one_data)>len(scenario_two_data):
            diff = int(len(scenario_one_data) - len(scenario_two_data))
            diff_array = numpy.zeros((int(diff),), dtype=numpy.int16)
            res_two = numpy.concatenate((scenario_two_data, diff_array))
            s.write(file_pair[1], rate, res_two)
        elif len(scenario_one_data)<len(scenario_two_data):
            diff = int(len(scenario_two_data) - len(scenario_one_data))
            diff_array = numpy.zeros((int(diff),), dtype=numpy.int16)
            res_one = numpy.concatenate((scenario_one_data, diff_array))
            s.write(file_pair[0], rate, res_one)
        else:
            continue
    return file_zip


def delay_directory(latency_value, input_directory, output_directory):
    sample_latency_array = numpy.zeros((latency_value,), dtype=numpy.int16)
    for dirpath, dirnames, filenames in os.walk(input_directory):
            if(len(filenames) != 0):
                for file_ in filenames:
                    if ("adjusted" in file_) or ("wav" not in file_):
                        continue
                    rate, data = s.read(dirpath+"\\"+file_)
                    res = numpy.concatenate((data, sample_latency_array))
                    res = numpy.delete(res, res[int(len(res)-latency_value):])
                    output_location = "adjusted_"+file_
                    s.write((output_directory+"\\"+output_location), rate, res)


def pair_directories(first_scenario, second_scenario):
    """Helper method specific to adjust_files method. 
    This method pairs files based on the order they are passed.
    the directory second_scenario will only scanned for files 
    containing the keyword "adjusted". 
    """
    scenario_one_filenames = []
    for dirpath, dirname, filenames in os.walk(first_scenario):
        if(len(filenames))!=0:
            for file_ in filenames:
                if "wav" in file_:
                    scenario_one_filenames.append(dirpath+"\\"+file_)
    first_total=len(scenario_one_filenames)
    scenario_two_filenames = []
    for dirpath, dirname, filenames in os.walk(second_scenario):
        if(len(filenames))!=0:
                for file_ in filenames:
                    if "wav" in file_:
                        scenario_two_filenames.append(dirpath+"\\"+file_)
    second_total=len(scenario_two_filenames)
    if first_total != second_total:
        print("Error, scenarios have different file totals")
    return scenario_one_filenames, scenario_two_filenames


def correlation_analysis(scenario_one, scenario_two):
    global file_pairs
    correlation_sample_log=[]
    correlation_coefficient_log=[]         
    for file_pair in file_pairs:
        print("Calculating: ", file_pair)
        # get file data
        rate, input_data=s.read(scenario_one+"\\"+file_pair[0])
        rate, output_data=s.read(scenario_two+"\\"+file_pair[1])
        output_data_samples=len(output_data)
        # compute the correlation between the two files and find thte max point
        correlation_array=numpy.correlate(input_data, output_data, "full")
        max_correlation_index=0
        max_correlation=correlation_array[0]
        for index, data_point in enumerate(correlation_array):
            if data_point > max_correlation:
                max_correlation_index=index
        # convert to time and save the most correlated time to a correlation log
        sample_offset = max_correlation_index - output_data_samples
        correlation_coefficient_log.append(max_correlation)
        correlation_sample_log.append(sample_offset)
    # return the average
    average_time_latency = numpy.mean(correlation_sample_log)/rate     # convert to seconds
    average_cross_correlation_coefficient = numpy.mean(correlation_coefficient_log)
    print("Cross Correlation Average Latency: ", average_time_latency, average_cross_correlation_coefficient)
    return rate, average_time_latency, average_cross_correlation_coefficient


def copy_and_flatten_files(input_path, output_path):
    for dirpath, dirname, filenames in os.walk(input_path):
        for file_ in filenames:
            cmd_command_copy = "copy " + dirpath + "\\" + file_ + " "+output_path
            os.system(cmd_command_copy)



# External methods 
def find_latency_values(scenario_one, scenario_two):
    collect_file_pairs(scenario_one, scenario_two)
    rate, cross_correlation_latency, cross_correlation_coefficient=correlation_analysis(scenario_one, scenario_two)
    return rate, cross_correlation_latency, cross_correlation_coefficient


def adjust_files(cross_correlation_latency, rate, scenario_one, scenario_two, root_directory):
    """Method to lineup the start time of the audio in 2 batches of values,
    And pad silence to end to match run time lengths
    A positive latency value will positive time shift the first scenario
    A negative latency value will positive time shift the second scenariod
    Parameters cross_correlation_latency: time to shift the files by
    scenario_one: absolute file path to first scenario
    scenario_two: absolute file path to second scenario
    Return zip_file_names: this is a list of [[scenario_one_file_name, scenario_two_file_name],...]
    """
    global adjusted_file_path
    # This temporary directory holds copies of all files that will be paired. This is done to alleviate
    # The complexity of pairing files across directories of varied structures
    adjusted_file_path =root_directory + "\\" + "adjusted_audio"
    scenario_one_temp = adjusted_file_path + "\\" + "scenario_one"
    scenario_two_temp = adjusted_file_path + "\\" + "scenario_two"
    try:
        os.mkdir(adjusted_file_path)
    except FileExistsError:
        print("To properly create ABX tests, the audio files are modified so audio begins play at the same time")
        print("In order to do this, a new directory called 'adjusted_audio' is temproarily created to hold the adjusted audio.")
        input("This directory already exists. Press enter to remove and continue or CNTRL -C to quit")
        shutil.rmtree(adjusted_file_path)
        os.mkdir(adjusted_file_path)
    os.mkdir(scenario_one_temp)
    os.mkdir(scenario_two_temp)
    sample_latency_value=int(cross_correlation_latency*rate)
    # if latency is positive, the first directory is delayed
    if cross_correlation_latency>0:
        delay_directory(sample_latency_value, scenario_one, scenario_one_temp)
        copy_and_flatten_files(scenario_two, scenario_two_temp)
        scenario_one_filenames, scenario_two_filenames = pair_directories(scenario_one_temp, scenario_two_temp)
        return match_lengths(scenario_one_temp, scenario_two_temp, [[A,B] for A,B in zip(scenario_one_filenames, scenario_two_filenames)])

    # if latency is negative then the second directory is delayed
    elif cross_correlation_latency<0:
        delay_directory(sample_latency_value, scenario_two, scenario_two_temp)
        copy_and_flatten_files(scenario_one, scenario_one_temp)
        scenario_one_filenames, scenario_two_filenames = pair_directories(scenario_one_temp, scenario_two_temp)
        return match_lengths(scenario_one, scenario_two, [[A,B] for A,B in zip(scenario_one_filenames, scenario_two_filenames)])
    # if latency is zero then neither directory is delayed and the file pairs are made directly
    else:
        scenario_one_filenames, scenario_two_filenames = pair_directories(scenario_one, adjusted_file_path)
        return match_lengths(scenario_one, scenario_two, [[A,B] for A,B in zip(scenario_one_filenames, scenario_two_filenames)])


def cleanup_scenarios():
    global adjusted_file_path
    try:
        shutil.rmtree(adjusted_file_path)
    except:
        print("The system could not delete the temporary audio files that were created for this test. This directory can be removed at {}".format(adjusted_file_path))


























































