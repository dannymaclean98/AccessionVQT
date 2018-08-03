
import os 
import yaml
import sys
import random
import shutil
import openpyxl
import yaml
import audioanalysis as aa
import numpy as np
import argparse
import logging
"""
manualtest.py

Script to create a listeneing test. The output, test 
case directory and answer_key.yml file, can be 
found in the root directory.

manual test creation
responsibilities:
1) directory of directories that each contain two files to compare(a,b) and a duplicated one (x)
    example scenarios to test:
        JITTER_BUFFER_INIT_X VS. JITTER_BUFFER_INIT_Y
        dev version vs dev version
        need to come up with more
2) an output yaml file labeled answer_key.yml that says which (a,b) is x 

"""
# command line parse
help_string = ("\nPlease note that manual_test.py makes 3 assumptions about "
                "these file paths. " 
            "\n1.Both scenarios contain the same amount of wav files."
            "\n2.The wav files in both scenarios have a one to one "
            "correspondence between each other. Each test case contains a "
            "pair of files, one from each scenario. This pair is made by "
            "matching files between scenarios with the same names 3."
            "There are no more than 25 audio file pairs")

parser = argparse.ArgumentParser(description="Script to create a listening test. The output, test case directory and answer_key.yml file, can be found in the root directory."+help_string)
parser.add_argument("-o", dest="output_base_path", default= os.getcwd(),help="(optional)Absolute file path to locatin to save test directory and answer key (default: root directory)")
parser.add_argument("scenario_one", help="Absolute file path to location of first scenario. Required")
parser.add_argument("scenario_two", help="Absolute file path to location of second scenario. Required")
args=parser.parse_args()

# globals
output_base_path=args.output_base_path
root_directory = os.getcwd()
# first scenario
scenario_one = args.scenario_one
scenario_one_latency=0
scenario_one_correlation_coefficient=0
# second scenario
scenario_two = args.scenario_two
scenario_two_latency=0
scenario_two_correlation_coefficient=0
output_path=""
answer_key=[]

USER_ANSWER_KEY="user_answer"
USER_PREFERENCE_KEY="user_preference_weight"
USER_X_VALUE_KEY="user_X_value"
USER_CONFIDENCE_KEY="user_answer_confidence"
X_ANSWER_KEY="x_answer_alpha"
A_VALUE_KEY="A_value"
B_VALUE_KEY="B_value"
TESTCASES_SUBDIR="testcases"
A_CASE_NAME="A_"
B_CASE_NAME="B_"
X_CASE_NAME="X_"
WNDWS_COPY_CMD="copy"
AUDIO_TYPE=".wav"
SCNEARIO_ONE_DATA_FILE="output_data.yml"
SCENARIO_ONE_DATA_FILE_KEY="Scenario One"
SCENARIO_TWO_DATA_FILE="output_data.yml"
SCENARIO_TWO_DATA_FILE_KEY="Scenario Two"
ANSWER_KEY_NAME="answer_key.yml"
USER_ANSWER_CASE_A="A"
USER_ANSWER_CASE_B="B"
ANSWER_KEY_SCENARIO_ONE="scenario one"
ANSWER_KEY_SCENARIO_TWO="scenario two"
ANSWER_KEY_QUESTION_KEY="Q_"
MAX_CASE_NUM=24
ADJUSTED_AUDIO_SUBDIR="adjusted_audio"
SCENARIO_ONE_SUBDIR="scenario_one"
SCENARIO_TWO_SUBDIR="scenario_two"

class Answer():
    """
    Wrapper for A_B_X directory containing all associated attributes. 
    Populate all fields of the class and call grade to determine if the 
    question was correct
    **user_answers
    user_answer                 either "A" or "B" indicating which file sounded better
    user_preference_weight      numeric value between 1-5 indicating how much better the 
                                preferred value was. 5 being significant and 1 minimal
    user_X_value                either "A" or "B" denoting which file the user believes
                                X was a duplicate of 
    user_answer_confidence      numeric value between 1-5 indicating how easy it was to 
                                distinguish between A and B and pick X
    x_answer_alpha              the answer to which file X was a duplicate of. Either 
                                "A" or "B"
    A_value                     String field denoting which scenario A belonged to. Either
                                scenario_one or SCENARIO_TWO_SUBDIR
    B_value                     String field denoting which scenario B belonged to. Either
                                scenario_one or SCENARIO_TWO_SUBDIR
    correct                     Call self.grade to populate this field. Compares user_X_value
                                and x_answer_alpha to determine if question was correct. 
                                Populates with boolean
    """
    def __init__(self, question_num, **user_answers):
        self.question_num=question_num
        self.correct = None
        try:
            self.user_answer=user_answers[USER_ANSWER_KEY]
        except KeyError:
            self.user_answer=None
        try:
            self.user_preference_weight=user_answers[USER_PREFERENCE_KEY]
        except KeyError: 
            self.user_preference_weight=None
        try:
            self.user_X_value=user_answers[USER_X_VALUE_KEY]
        except KeyError:
            self.user_X_value=None
        try:
            self.user_answer_confidence=user_answers[USER_CONFIDENCE_KEY]
        except KeyError:
            self.user_answer_confidence=None
        try:
            self.x_answer_alpha=user_answers[X_ANSWER_KEY]
        except KeyError:
            self.x_answer_alpha=None
        try:        
            self.A_value=user_answers[A_VALUE_KEY]
        except KeyError:
            self.A_value=None    
        try:
            self.B_value=user_answers[B_VALUE_KEY]
        except KeyError:
            self.B_value=None

    def grade(self):
        if self.x_answer_alpha==self.user_X_value:
            self.correct=True
        else:
            self.correct=False


def _collect_locations():
    # Method to pair all the files for comparison in the two scenarios the user has elected to compare 
    logging.info("Enter: _collect_locations")
    global scenario_one
    global scenario_two
    global output_base_path
    if not os.path.exists(scenario_one):
        print("Scenario One file path does not exist. Exiting")
        sys.exit()
    if not os.path.exists(scenario_two):
        print("Scenario Two file path does not exist. Exiting")
        sys.exit()
    print("Creating listening test...")
    logging.info("Exit: _collect_locations")
    return scenario_one, scenario_two, output_base_path
    

def _cleanup_scenarios(adjusted_file_path):
    # Delete the adjusted audio created for this module
    try:
        shutil.rmtree(adjusted_file_path)
    except:
        print("The system could not delete the temporary audio files that "
        "were created for this test. This directory can be removed "
        "at {}".format(adjusted_file_path))


def _create_output_directory(output_base_path):
    # From the base path create a testcases subdirectory
    # Return the subdirectory full path
    logging.info("Enter: _create_output_directory")
    global output_path 
    output_path = os.path.join(output_base_path, TESTCASES_SUBDIR)
    if os.path.exists(output_path):
        try:
            input("Please note there is already a Testcases directory at - {} .\nPress enter to continue and remove it. Press CNTRL-C to exit.".format(output_path))
            shutil.rmtree(output_path)
        except PermissionError:
            print("There is a test directory located in the same location as the test directory location you specified")
            print("It cannot be removed becase another process is still using it. Please close the process or delete yourself.")
            sys.exit()
        except KeyboardInterrupt:
            print("Exiting...")
            sys.exit()
    os.mkdir(output_path)
    logging.info("Exit: _create_output_directory")
    return output_path


def _create_answer_key(output_path):
    # Parse the data file from scenario one and two if it exists and add too answer key
    # Dump data from processes to ANSWER_KEY_NAME in output_path
    logging.info("Enter: _create_answer_key")
    global answer_key
    global scenario_one
    global scenario_two
    scenario_one_latency_data={}
    if os.path.exists(os.path.join(scenario_one, SCNEARIO_ONE_DATA_FILE)):
        with open(os.path.join(scenario_one, SCNEARIO_ONE_DATA_FILE)) as output_data:
            scenario_one_latency_data[SCENARIO_ONE_DATA_FILE_KEY]=yaml.load(output_data)
    scenario_two_latency_data={}
    if os.path.exists(os.path.join(scenario_two, SCENARIO_TWO_DATA_FILE)):
        with open(os.path.join(scenario_two, SCENARIO_TWO_DATA_FILE)) as output_data:
            scenario_two_latency_data[SCENARIO_TWO_DATA_FILE_KEY]=yaml.load(output_data)

    with open(os.path.join(output_path, ANSWER_KEY_NAME), "w") as answer_key_yml:
        yaml.dump(scenario_one_latency_data, answer_key_yml, default_flow_style=False)
        yaml.dump(scenario_two_latency_data, answer_key_yml, default_flow_style=False)
        for question in answer_key:
            yaml_dict={}
            Key = str(ANSWER_KEY_QUESTION_KEY+str(question.question_num))
            yaml_dict[Key] = {X_ANSWER_KEY: question.x_answer_alpha,A_VALUE_KEY: question.A_value,B_VALUE_KEY: question.B_value}
            yaml.dump(yaml_dict, answer_key_yml, default_flow_style=False)
    logging.info("Exit: _create_answer_key")


def _create_temp_dir(root_directory, scenario_one, scenario_two):
    logging.info("Enter: _create_temp_dir")
    # Will create exact copies of both directories specified so files may be altered later
    adjusted_file_path = os.path.join(root_directory, ADJUSTED_AUDIO_SUBDIR)
    scenario_one_temp = os.path.join(adjusted_file_path, SCENARIO_ONE_SUBDIR)
    scenario_two_temp = os.path.join(adjusted_file_path, SCENARIO_TWO_SUBDIR)
    try:
        os.mkdir(adjusted_file_path)
    except FileExistsError:
        print("To properly create ABX tests, the audio files are modified so audio begins play at the same time")
        print("In order to do this, a new directory called 'adjusted_audio' is temproarily created to hold the adjusted audio.")
        input("This directory already exists. Press enter to remove and continue or CTRL-C to quit")
        shutil.rmtree(adjusted_file_path)
        os.mkdir(adjusted_file_path)
    shutil.copytree(scenario_one, scenario_one_temp)
    shutil.copytree(scenario_two, scenario_two_temp)
    logging.info("Exit: _create_temp_dir")
    return adjusted_file_path, scenario_one_temp, scenario_one_temp


def create_A_B_X_cases(A_B_cases_zip_list, output_path):
    """
    Method to create A_B_X testing directories and return the corresponding answer key
    An A file is chosen from either the scenario one or two with a 50/50 probability. 
    The B file is then from the scenario not chosen for A. An X file is then created with a 50/50
    probability of being either a duplicate of A or B
    Parameters:
    A_B_cases_zip_list:         A list containing absolute file pairs
                                [[scenario_one, scenario_two]...]
    output_path:                absolute file path to store testcase directory 

    Returns:
    None
    """
    logging.info("Enter: create_A_B_X_cases ")
    global scenario_one
    global scenario_two
    global answer_key
    # create listening directories and record answer to each in answer_log
    for case_num, case in enumerate(A_B_cases_zip_list):
        #MRR I really don't like silently dropping audio pairs. Please just create multiple ABX tests, each with up to 25. Up to you whether you have 3 of 25 and one of 21 or 4 of 24.
        if case_num > MAX_CASE_NUM:
            logging.info("The amount of cases has exceeded 25. Please note that "
            "the accompanying excel sheet only has 25 answer slots and that it will need to "
            "be restructured") 
            print("The amount of cases has exceeded 25. Please note that "
            "the accompanying excel sheet only has 25 answer slots and that it will need to "
            "be restructured")
        test_case_path = os.path.join(output_path, str(case_num))
        try:
            os.mkdir(test_case_path)
        except FileExistsError:
            logging.debug("Could not create test case directory at {} - encountered FileExistsError".format(test_case_path))
            print("Could not create test case directory at {} - encountered FileExistsError".format(test_case_path))
            sys.exit()
        switch_A_B = random.randint(0,1)        #If one then A and B are switched. This is so scenario one and two alternate thier A and B positions roughly 50% of the time
        # add the wav files
        # pick one to duplicate
        x_answer=random.randint(0,1)
        if switch_A_B:
            # add A
            cmd_command_copy_a = WNDWS_COPY_CMD+" " + case[1] + " "+ os.path.join(test_case_path, A_CASE_NAME+str(case_num)+AUDIO_TYPE)
            os.system(cmd_command_copy_a)
            # add B 
            cmd_command_copy_b = WNDWS_COPY_CMD+" " + case[0] + " "+ os.path.join(test_case_path, B_CASE_NAME+str(case_num)+AUDIO_TYPE)
            os.system(cmd_command_copy_b)
            # add X
            if x_answer==1:
                x_answer_alpha=USER_ANSWER_CASE_A
                cmd_command_copy_a = WNDWS_COPY_CMD+" " + case[1] + " "+ os.path.join(test_case_path, X_CASE_NAME+str(case_num)+AUDIO_TYPE)
                os.system(cmd_command_copy_a)
            if x_answer==0:
                x_answer_alpha=USER_ANSWER_CASE_B
                cmd_command_copy_b = WNDWS_COPY_CMD+" " + case[0] + " "+ os.path.join(test_case_path, X_CASE_NAME+str(case_num)+AUDIO_TYPE)
                os.system(cmd_command_copy_b)
            A_value=ANSWER_KEY_SCENARIO_TWO
            B_value=ANSWER_KEY_SCENARIO_ONE
        else:
            # add A
            cmd_command_copy_a = WNDWS_COPY_CMD+" " + case[0] + " "+ os.path.join(test_case_path, A_CASE_NAME+str(case_num)+AUDIO_TYPE)
            os.system(cmd_command_copy_a)
            # add B 
            cmd_command_copy_b = WNDWS_COPY_CMD+" " + case[1] + " "+ os.path.join(test_case_path, B_CASE_NAME+str(case_num)+AUDIO_TYPE)
            os.system(cmd_command_copy_b)
            # add X
            if x_answer==0:
                x_answer_alpha=USER_ANSWER_CASE_A
                cmd_command_copy_a = WNDWS_COPY_CMD+" " + case[0] + " "+ os.path.join(test_case_path, X_CASE_NAME+str(case_num)+AUDIO_TYPE)
                os.system(cmd_command_copy_a)
            if x_answer==1:
                x_answer_alpha=USER_ANSWER_CASE_B
                cmd_command_copy_b = WNDWS_COPY_CMD+" " + case[1] + " "+ os.path.join(test_case_path, X_CASE_NAME+str(case_num)+AUDIO_TYPE)
            os.system(cmd_command_copy_b)
            A_value=ANSWER_KEY_SCENARIO_ONE
            B_value=ANSWER_KEY_SCENARIO_TWO
        question_info = Answer(case_num, x_answer_alpha=x_answer_alpha,A_value=A_value, B_value=B_value)
        answer_key.append(question_info)
    logging.info("Exit: create_A_B_X_cases")
        

def create_manual_tests():
    logging.info("Enter: create_manual_tests")
    global root_directory
    scenario_one, scenario_two, output_base_path=_collect_locations()
    output_path = _create_output_directory(output_base_path)
    # Confirm another answer key does not already exist
    if os.path.exists(os.path.join(output_path, ANSWER_KEY_NAME)):
        input("An answer_key.yml file already exists at - "+output_path+" - this file will be deleted. Press enter if this is okay of CNTRL-C to exit")
        os.remove(os.path.join(output_path, ANSWER_KEY_NAME))
    adjusted_file_path, scenario_one_temp, scenario_two_temp= _create_temp_dir(root_directory, scenario_one, scenario_two)
    print("Please note that to create the manual tests, the latency of each file must be calculated. This takes roughly 30 minutes per 25 recordings. Press Enter to continue.")
    rate_log, correlation_sample_log, correlation_coefficient_log = aa.find_latency_values(scenario_one_temp, scenario_two_temp)
    # Negative value indicates that scenario one signal was delayed. Positive value indicates that scenario two signal was delayed
    file_zip = aa.pair_directories(scenario_one_temp, scenario_two_temp)
    aa.adjust_files(correlation_sample_log, rate_log, file_zip)
    create_A_B_X_cases(file_zip, output_path)
    _cleanup_scenarios(adjusted_file_path)
    _create_answer_key(output_base_path)
    print("done")
    logging.info("Exit: create_manual_tests")


if __name__ =="__main__":
    logging.basicConfig(filename="manualtest.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(module)s line: %(lineno)d, %(message)s")
    logging.info("Enter: main")
    create_manual_tests()
    logging.info("Exit: main")

















