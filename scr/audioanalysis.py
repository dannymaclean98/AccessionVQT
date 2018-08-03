#Latency comparison

import numpy as np
import scipy
import scipy.io.wavfile as wf
import sounddevice as sd
import os
import yaml
import sys
import shutil
import warnings
import logging 

"""
audioanalysis.py

This tool has 2 main purposes:
1) calculate the latency between the start time of two different scenario's 
with identical file totals
2) adjust the start times of files so they line up
Use find_latency_values() to get rate_log, correlation_sample_log and correltaion_coefficient_log
Use pair_directories() to create the file_zip 
Use adjust_audio(), file_zip, correlation_sample_log and rate_log to adjust the audio start times to line up 
Please call cleanup_scenarios() when done to cleanup files created by this library

"""
logging.basicConfig(filename="audioanalysis.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(module)s line: %(lineno)d, %(message)s")
warnings.filterwarnings("error")

#MRR A major issue with this, which we don't have time to address, is that this module and manualtest are really tightly coupled. 
root_directory=os.getcwd()
adjusted_file_path=""
file_pairs = []
WAV="wav"

# External methods 
def find_latency_values(scenario_one, scenario_two):
    """Compute the full correlation for each pair of files in file_pairs.
    The time complexity is approximately O(n^2). To compute the correlation between 
    two 10 second recordings will take 10 seconds.
    Parameters: 
    file_pairs:                 A list of absolute file path
                                pairs - [[scenario_one, scenario_two]....]
    Returns:
    correlation_rate_log:       A list containing the rate used to compute 
                                the latency between the two files
    correlation_sample_log:     A list containing the sample offset of the audio
                                start times. Note that this is computed using 
                                max_correlation_index - len(scenario_two) and thus 
                                negative values indicate scenario one started first
                                zero indicates the files start at the same sample
                                positive values indicate that scenario two started first
    correlation_coefficient_log:A list containing the max correlation coefficient between 
                                the two files compared
    """
    file_pairs=_collect_file_pairs(scenario_one, scenario_two)
    rate_log, correlation_sample_log, correlation_coefficient_log=_analyse_correlation(file_pairs)
    return rate_log, correlation_sample_log, correlation_coefficient_log


def pair_directories(first_scenario, second_scenario):
    """Helper method specific to adjust_files method. 
    This method pairs files alphabetically between two
    scenarios. Please note only .wav files will be paird
    Parameters: 
    first_scenario:     absolute file path to the 
                        first directory     
    second_scenario:    absolute file path to the 
                        second directory
    Returns:
    file_zip:           A list with the pairs of absolute 
                        file_paths
                        [[first_scenario_file, second_scenario_file]...]   
    """
    scenario_one_filenames = []
    for dirpath, dirname, filenames in os.walk(first_scenario):
            for file_ in filenames:
                if WAV in file_:
                    scenario_one_filenames.append(os.path.join(dirpath, file_))
    first_total=len(scenario_one_filenames)
    scenario_two_filenames = []
    for dirpath, dirname, filenames in os.walk(second_scenario):
                for file_ in filenames:
                    if WAV in file_:
                        scenario_two_filenames.append(os.path.join(dirpath, file_))
    second_total=len(scenario_two_filenames)
    if first_total != second_total:
        print("Error, scenarios have different file totals")
    return [[A,B] for A,B in zip(scenario_one_filenames, scenario_two_filenames)]


def adjust_files(correlation_sample_log, rate_log, file_zip):
    """
    Method to lineup the start time of the audio in 2 batches of values,
    And pad silence to end to match run time lengths
    A positive latency value will positive time shift the first scenario
    A negative latency value will positive time shift the second scenario
    Please note that all 3 parameters should be lists of the same length
    Parameters:
    correlation_sample_log:     A list of latency values to shift each 
                                pair of files in file_zip by
                                
    rate_log:                   List of rates used for each file pair
    file_zip:                   A list with the pairs of absolute 
                                file_paths
                                [[first_scenario_file, second_scenario_file]...]  
 
    """
    for index, sample_delay in enumerate(correlation_sample_log):
        cross_correlation_latency = sample_delay/(rate_log[index])
        # if latency is positive, the first directory is delayed
        if cross_correlation_latency>0:
            _delay_file(sample_delay, file_zip[index][0])
            _match_lengths(file_zip[index][0], file_zip[index][1])
        # if latency is negative then the second directory is delayed
        elif cross_correlation_latency<0:
            _delay_file(sample_delay, file_zip[index][1])
            _match_lengths(file_zip[index][0], file_zip[index][1])
        # if latency is zero then neither directory is delayed and the file pairs are made directly
        else:
            _match_lengths(file_zip[index][0], file_zip[index][1])



# Internal Methods
def _collect_file_pairs(scenario_one, scenario_two):
    scenario_one_filenames=[]
    scenario_two_filenames=[]
    for dirpath,dirnames,filenames in os.walk(scenario_one):
                for file_ in filenames:
                    if WAV in file_:
                        scenario_one_filenames.append(os.path.join(dirpath, file_))
    for dirpath,dirnames,filenames in os.walk(scenario_two):
                for file_ in filenames:
                    if WAV in file_:
                        scenario_two_filenames.append(os.path.join(dirpath, file_))
    return [[file_in, file_out] for file_in, file_out in zip(scenario_one_filenames, scenario_two_filenames)]


def _match_lengths(scenario_one, scenario_two):
    # Find which one is longer and append silence to shorter array
    # read data
    rate, scenario_one_data=wf.read(scenario_one)
    rate, scenario_two_data=wf.read(scenario_two)
    
    if len(scenario_one_data)>len(scenario_two_data):
        diff = int(len(scenario_one_data) - len(scenario_two_data))
        diff_array = np.zeros((int(diff),), dtype=np.int16)
        res_two = np.concatenate((scenario_two_data, diff_array))
        wf.write(scenario_two, rate, res_two)
    elif len(scenario_one_data)<len(scenario_two_data):
        diff = int(len(scenario_two_data) - len(scenario_one_data))
        diff_array = np.zeros((int(diff),), dtype=np.int16)
        res_one = np.concatenate((scenario_one_data, diff_array))
        wf.write(scenario_one, rate, res_one)


def _delay_file(latency_value, file_path):
    # Add an array of zeros to the end of the audio 
    # file specified in file_path
    sample_latency_array = np.zeros((abs(latency_value),), dtype=np.int16)
    rate, data = wf.read(file_path)
    res = np.concatenate((data, sample_latency_array))
    res = np.delete(res, res[int(len(res)-latency_value):])
    wf.write(file_path, rate, res)


def _analyse_correlation(file_pairs):
    # Refer to doc comment in find_latency_values() for 
    # implementation details for this function
    correlation_sample_log=[]
    correlation_coefficient_log=[] 
    correlation_rate_log=[]        
    for file_pair in file_pairs:
        print("Calculating: ", file_pair)
        # get file data
        rate, input_data=wf.read(file_pair[0])
        rate, output_data=wf.read(file_pair[1])
        output_data_samples=len(output_data)
        correlation_array=np.correlate(input_data, output_data, "full")
        max_correlation_index=np.argmax(correlation_array)
        max_correlation = np.amax(correlation_array)  
        # the correlate function and the way in which np.correlate shifts the arrays relative to each other. 
        sample_offset = max_correlation_index - output_data_samples
        correlation_coefficient_log.append(max_correlation)
        correlation_sample_log.append(sample_offset)
        correlation_rate_log.append(rate)
        print("Latency: {}, Rate: {}, Correlation Coefficient: {}".format(sample_offset/rate, rate, max_correlation))
    # return the average
    return correlation_rate_log, correlation_sample_log, correlation_coefficient_log

