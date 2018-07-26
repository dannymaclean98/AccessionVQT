#Latency comparison

import numpy
import scipy
import scipy.io.wavfile as s
import sounddevice as sd
import os
import yaml
import sys
import soundfile
import warnings
warnings.filterwarnings("error")


root_directory=os.getcwd()
file_pairs = []
rate=16000

# Note: Positive offset indicates that signal 2 was delayed
    # Negative offset indicates that siganl one was delayed 

def collect_file_pairs(scenario_one, scenario_two):
    global file_pairs
    scenario_one_filenames=[]
    scenario_two_filenames=[]
    
    for dirpath,dirnames,filenames in os.walk(scenario_one):
            if(len(filenames)!=0):
                for file_ in filenames:
                    scenario_one_filenames.append(file_)

    for dirpath,dirnames,filenames in os.walk(scenario_two):
            if(len(filenames)!=0):
                for file_ in filenames:
                    scenario_two_filenames.append(file_)
                    
    file_pairs = [[file_in, file_out] for file_in, file_out in zip(scenario_one_filenames, scenario_two_filenames)]


def correlation_analysis(scenario_one, scenario_two):
    global root_directory
    global file_pairs
    global rate
    correlation_sample_log=[]
    correlation_coefficient_log=[]         
    for file_pair in file_pairs:
        rate, input_data=s.read(scenario_one+"\\"+file_pair[0])
        rate, output_data=s.read(scenario_two+"\\"+file_pair[1])
        output_data_samples=len(output_data)
        correlation_array=numpy.correlate(input_data, output_data, "full")
        max_correlation_index=0
        max_correlation=correlation_array[0]
        for index, data_point in enumerate(correlation_array):
            if data_point > max_correlation:
                max_correlation_index=index
        sample_offset = max_correlation_index - output_data_samples
        correlation_coefficient_log.append(max_correlation)
        correlation_sample_log.append(sample_offset)
    average_time_latency = numpy.mean(correlation_sample_log)/rate    # convert to seconds
    average_cross_correlation_coefficient = numpy.mean(correlation_coefficient_log)
    print("Cross Correlation Average Latency: ", average_time_latency, average_cross_correlation_coefficient)
    return average_time_latency, average_cross_correlation_coefficient


def find_latency_values(scenario_one, scenario_two):
    """Method to find average latency between two scenarios
    Parameters - Scenario one and Scenario two are absolute file paths to the directories to compare
    Returns - cross correlation lateny and cross correlation coefficient"""
    collect_file_pairs(scenario_one, scenario_two)
    cross_correlation_latency, cross_correlation_coefficient=correlation_analysis(scenario_one, scenario_two)
    return cross_correlation_latency, cross_correlation_coefficient




























































