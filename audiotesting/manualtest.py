# manual test creation

# responsibilities:
# 1) directory of directories that each contain two files to compare(a,b) and a duplicated one (x)
    # Scenarios to test:
        # JITTER_BUFFER_INIT_X VS. JITTER_BUFFER_INIT_Y
        # dev version vs dev version
        # need to come up with more
# 2) an output csv that says which (a,b) is x 
# 3) a scoring algorithm


# testing flow 
# select mode 1 or 2
# 1)
# take input for 2 scenarios to test
# pair them and calculate latency between the pairs
# trim the latency from begginging of one file 
# add samples to end of shorter so they match up
# create files and anwer key
# 2)
# parse the answer key and user answers
# grade and give analytics!

import os 
import yaml
import sys
import random
import shutil
import openpyxl
import yaml
import wav_tuner as w 
import scipy.io.wavfile as s
import numpy
import argparse

# command line parse
parser = argparse.ArgumentParser(description="Script to create a listening test. The test directory and answer_key.yml file can be found in the root directory.")
parser.add_argument("-o", dest="output_base_path", default= os.getcwd(),help="(optional)Absolute file path to location to save test directory and answer key (default: root directory)")
parser.add_argument("-s1", dest="scenario_one", help="Absolute file path to location of first scenario. See manual for details")
parser.add_argument("-s2", dest="scenario_two", help="Absolute file path to location of second scenario. See manual for details")
args=parser.parse_args()

# globals
output_base_path=args.output_base_path
root_directory = os.getcwd()
# first scenario
# scenario_one=args.scenario_one
scenario_one = "C:\\Users\\dm2\\AccessionATF\\ATAT_GitLab\\atat\master_branch\\audiotesting\\examples_directories_for_testing\\output_1_2_3_4_gemodel_None_PL_None_delay_150_jitter"
scenario_one_latency=0
scenario_one_correlation_coefficient=0
# second scenario
# scenario_two=args.scenario_two
scenario_two = "C:\\Users\\dm2\\AccessionATF\\ATAT_GitLab\\atat\\master_branch\\audiotesting\\examples_directories_for_testing\\output_2_3_4_5_gemodel_None_PL_None_delay_1000_jitter"
scenario_two_latency=0
scenario_two_correlation_coefficient=0
output_path=""
answer_key=[]
# tips for using optional keyword dictionaries? is there a better way to do so?
class answer():
    """Wrapper for A_B_X directory containing all associated attributes 
    """
    def __init__(self, question_num, **user_answers):
        self.question_num=question_num
        self.correct = None
        try:
            self.user_answer=user_answers["user_answer"]
        except KeyError:
            self.user_answer=None
        try:
            self.user_preference_weight=user_answers["user_preference_weight"]
        except KeyError: 
            self.user_preference_weight=None
        try:
            self.user_X_value=user_answers["user_X_value"]
        except KeyError:
            self.user_X_value=None
        try:
            self.user_answer_confidence=user_answers["user_answer_confidence"]
        except KeyError:
            self.user_answer_confidence=None
        try:
            self.x_answer_alpha=user_answers["x_answer_alpha"]
        except KeyError:
            self.x_answer_alpha=None
        try:        
            self.A_value=user_answers["A_value"]
        except KeyError:
            self.A_value=None    
        try:
            self.B_value=user_answers["B_value"]
        except KeyError:
            self.B_value=None

    def grade(self):
        if self.x_answer_alpha==self.user_answer:
            self.correct=True
        else:
            self.correct=False


def collect_locations():
    """Method to pair all the files for comparison in the two scenarios the user has elected to compare 
    """
    global scenario_one
    global scenario_two
    global output_base_path
    if (scenario_one==None) or (scenario_two==None):
        print("Please specify file paths. Type 'manual_test.py -h' for help or refer to the documentation")
        sys.exit()
    print("Creating listening test...")
    if output_base_path == None:
        output_base_path=os.getcwd()
    return scenario_one, scenario_two, output_base_path
    

def create_output_directory(output_base_path):
    global output_path 
    output_path = output_base_path + "\\" + "testcases"
    if os.path.exists(output_path):
        try:
            input("Please note there is already a Testcases directory here.\nPress enter to continue and remove it. Press CNTRL-C to exit.")
            shutil.rmtree(output_path)
        except PermissionError:
            print("There is a test directory located in the same location as the test directory location you specified")
            print("It cannot be removed becase another process is still using it. Please close the process or delete yourself.")
            sys.exit()
        except KeyboardInterrupt:
            print("Exiting...")
            sys.exit()
    os.mkdir(output_path)
    return output_path


def create_A_B_X_cases(A_B_cases_zip_list, output_path):
    """Method to create A_B_X testing directories and return the corresponding answer key
    Parameters None
    Returns None
    """
    global scenario_one
    global scenario_two
    global answer_key
    # create listening directories and record answer to each in answer_log
    for case_num, case in enumerate(A_B_cases_zip_list):
        test_case_path = output_path+"\\"+str(case_num)
        os.mkdir(test_case_path)
        switch_A_B = random.randint(0,1)        #If one then A and B are switched. This is so scenario one and two alternate thier A and B positions roughly 50% of the time
        # add the wav files
        # pick one to duplicate
        x_answer=random.randint(0,1)
        if switch_A_B:
            # add A
            cmd_command_copy_a = "copy " + case[1] + " "+test_case_path + "\\A_"+str(case_num)+".wav"
            os.system(cmd_command_copy_a)
 
            # add B 
            cmd_command_copy_b = "copy " + case[0] + " "+test_case_path+"\\"+"B_"+str(case_num)+".wav"
            os.system(cmd_command_copy_b)

            # add X
            if x_answer==1:
                x_answer_alpha="A"
                cmd_command_copy_a = "copy " + case[1] + " "+test_case_path + "\\X_"+str(case_num)+".wav"
                os.system(cmd_command_copy_a)

            if x_answer==0:
                x_answer_alpha="B"
                cmd_command_copy_b = "copy " + case[0] + " "+test_case_path+"\\"+"X_"+str(case_num)+".wav"
                os.system(cmd_command_copy_b)
               
            A_value="scenario two"
            B_value="scenario one"
        else:
            # add A
            cmd_command_copy_a = "copy " + case[0] + " "+test_case_path+"\\"+"B_"+str(case_num)+".wav"
            os.system(cmd_command_copy_a)
            # add B 
            cmd_command_copy_b = "copy " + case[1] + " "+test_case_path + "\\B_"+str(case_num)+".wav"
            os.system(cmd_command_copy_b)
            # add X
            if x_answer==0:
                x_answer_alpha="A"
                cmd_command_copy_a = "copy " + case[0] + " "+test_case_path+"\\"+"B_"+str(case_num)+".wav"
                os.system(cmd_command_copy_a)
            if x_answer==1:
                x_answer_alpha="B"
                cmd_command_copy_b = "copy " + case[1] + " "+test_case_path + "\\B_"+str(case_num)+".wav"
            os.system(cmd_command_copy_b)
            A_value="scenario one"
            B_value="scenario two"
            
        question_info = answer(case_num, x_answer_alpha=x_answer_alpha,A_value=A_value, B_value=B_value)
        answer_key.append(question_info)
        # jump out a level
        os.chdir("..")
    
    
def create_answer_key(output_path):
    global answer_key
    global scenario_one
    global scenario_two
    scenario_one_latency_data={}
    if os.path.exists(scenario_one+"\\output_data.yml"):
        os.chdir(scenario_one)
        with open("output_data.yml") as output_data:
            scenario_one_latency_data["Scenario One"]=yaml.load(output_data)
    scenario_two_latency_data={}
    if os.path.exists(scenario_two+"\\output_data.yml"):
        os.chdir(scenario_two)
        with open("output_data.yml") as output_data:
            scenario_two_latency_data["Scenario Two"]=yaml.load(output_data)
    os.chdir(output_path)
    if os.path.exists(output_path + "\\answer_key.yml"):
        os.remove("answer_key.yml")
    with open("answer_key.yml", "w") as answer_key_yml:
        yaml.dump(scenario_one_latency_data, answer_key_yml, default_flow_style=False)
        yaml.dump(scenario_two_latency_data, answer_key_yml, default_flow_style=False)
        for question in answer_key:
            yaml_dict={}
            Key = str("Q_"+str(question.question_num))
            yaml_dict[Key] = {"x_answer_alpha": question.x_answer_alpha,"A_value": question.A_value,"B_value": question.B_value}
            yaml.dump(yaml_dict, answer_key_yml, default_flow_style=False)
            

def create_manual_tests():
    global root_directory
    scenario_one, scenario_two, output_base_path=collect_locations()
    output_path = create_output_directory(output_base_path)
    print("calculating latency")
    # rate, cross_correlation_latency, cross_correlation_coefficient = w.find_latency_values(scenario_one, scenario_two)
    # Negative value indicates that scenario one signal was delayed. Positive value indicates that scenario two signal was delayed
    cross_correlation_latency=1
    rate=16000
    file_zip=w.adjust_files(cross_correlation_latency, rate, scenario_one, scenario_two, root_directory)
    create_A_B_X_cases(file_zip, output_path)
    w.cleanup_scenarios()
    create_answer_key(output_base_path)
    print("done!")


if __name__ =="__main__":
    create_manual_tests()

















