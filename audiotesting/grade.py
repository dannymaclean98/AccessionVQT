# Grade Script
# Required:
# responses.xlsx located in root directory
# answer_key.yml generated from manual_test.py

# Responsibilites Include
# Grading the responses.xlsx excel sheet 
# creating test_results.yml containing the results

# Bugs: 
# Answer Key and excel sheet mismatch in question numbers

import os
import yaml
import openpyxl
import sys
import argparse

parser = argparse.ArgumentParser(description="Script to grade listening tests, specify a file to grade a collection of tests. Default setting is to search root directory for responses.xlsx. See manual for details on grading multiple responses")
parser.add_argument("-fp", dest="file_path", help="the absolute file path to the files to be graded")

# args=parser.parse_args()


root_directory=os.getcwd()


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

def grade(response_directory): 
    global root_directory
    answer_key=[]
    #collect answers
    os.chdir(response_directory)
    try:
        response_doc = openpyxl.load_workbook(filename="responses.xlsx").active
        for case_num, row_num in enumerate(range(21, 37)):
            loc_question_num = "A"+str(row_num)
            question_num = response_doc[loc_question_num].value
            loc_user_answer = "B"+str(row_num)
            user_answer = response_doc[loc_user_answer].value
            loc_user_preference_weight = "C"+str(row_num)
            user_preference_weight = response_doc[loc_user_preference_weight].value
            loc_user_X_value ="D"+str(row_num)
            user_X_value = response_doc[loc_user_X_value].value
            loc_user_answer_confidence ="E"+str(row_num)
            user_answer_confidence = response_doc[loc_user_answer_confidence].value
            question_info = answer(case_num, user_answer=user_answer,user_preference_weight=user_preference_weight, user_X_value=user_X_value, user_answer_confidence=user_answer_confidence)
            answer_key.append(question_info)
    except FileNotFoundError:
        print("No responses.xlsx file found...Exiting now")
        sys.exit()
    # score the answers
    os.chdir(root_directory)
    try:
        with open("answer_key.yml") as Key:
            Key = yaml.load(Key)
            for num, question in enumerate(answer_key):
                num = str("Q_"+str(num))
                question.x_answer_alpha=Key[num]["x_answer_alpha"]
                question.A_value=Key[num]["A_value"]
                question.B_value=Key[num]["B_value"]
                question.grade()
            total_correct=0
        # count how many are correct 
        for question_num, question in enumerate(answer_key):
            print(question_num, ": ", question.correct)
            if question.correct:
                total_correct = total_correct + 1
    except FileNotFoundError:
        print("No answer_key.yml found...Exiting now")
        sys.exit()    
    # print and output data to test_results
    print("total correct: ", total_correct)
    print("grade: ", float(total_correct/16))
    total_preference_for_scenario_one=0
    scenario_one_preference_score=0
    total_preference_for_scenario_two=0
    scenario_two_preference_score=0
    for analytics in answer_key:
        print(analytics.question_num,": answer: ", analytics.x_answer_alpha, "listener: ", analytics.user_answer, analytics.user_preference_weight, analytics.user_X_value, analytics.user_answer_confidence)
        if analytics.correct:
            if analytics.user_answer == "A":
                if analytics.A_value=="scenario one":
                    total_preference_for_scenario_one = total_preference_for_scenario_one + 1
                    scenario_one_preference_score = scenario_one_preference_score + analytics.user_preference_weight
                if analytics.A_value=="scenario two":
                    total_preference_for_scenario_two = total_preference_for_scenario_two + 1       
                    scenario_two_preference_score = scenario_two_preference_score + analytics.user_preference_weight
            if analytics.user_answer == "B":
                if analytics.B_value=="scenario one":
                    total_preference_for_scenario_one = total_preference_for_scenario_one + 1
                    scenario_one_preference_score = scenario_one_preference_score + analytics.user_preference_weight
                if analytics.B_value=="scenario two":
                    total_preference_for_scenario_two = total_preference_for_scenario_two + 1       
                    scenario_two_preference_score = scenario_two_preference_score + analytics.user_preference_weight
    print("Points for Scenario One: ", total_preference_for_scenario_one)
    print("Points for Scenario Two: ", total_preference_for_scenario_two)
    if total_preference_for_scenario_one == 0:
        print("Degree of seperation for Scenario One: 0")
    else:
        print("Degree of seperation for Scenario One: ", scenario_one_preference_score/total_preference_for_scenario_one)
    if total_preference_for_scenario_two == 0:
        print("Degree of seperation for Scenario Two: 0")
    else:
        print("Degree of seperation for Scenario Two: ", scenario_two_preference_score/total_preference_for_scenario_two)
    os.chdir(response_directory)
    with open("test_results.yml", "w") as test_results:  
        yaml_answer_key={}
        response_directory_key = response_directory.replace(":", "_")
        yaml_answer_key[response_directory_key]={}
        yaml_answer_key[response_directory_key]["Total Correct"]=total_correct
        yaml_answer_key[response_directory_key]["Total Questions"]=len(answer_key)
        yaml_answer_key[response_directory_key]["Total Preference For Scenario One"]=total_preference_for_scenario_one
        yaml_answer_key[response_directory_key]["Total Preference For Scenario Two"]=total_preference_for_scenario_two
        if total_preference_for_scenario_one==0:
            yaml_answer_key[response_directory_key]["Degree of Preference For Scenario One"]=0
        else:
            yaml_answer_key[response_directory_key]["Degree of Preference For Scenario One"]=scenario_one_preference_score/total_preference_for_scenario_one
        if total_preference_for_scenario_two==0:
            yaml_answer_key[response_directory_key]["Degree of Preference For Scenario Two"]=0
        else:
            yaml_answer_key[response_directory_key]["Degree of Preference For Scenario Two"]=scenario_two_preference_score/total_preference_for_scenario_two
        yaml_answer_key[response_directory_key]["Questions"]={}
        for question in answer_key:
            yaml_answer_key[response_directory_key]["Questions"][question.question_num]={}
            yaml_answer_key[response_directory_key]["Questions"][question.question_num]["Correct"]=question.correct
            yaml_answer_key[response_directory_key]["Questions"][question.question_num]["Correct Answer"]= {}
            yaml_answer_key[response_directory_key]["Questions"][question.question_num]["Correct Answer"]["Answer"]=question.x_answer_alpha
            if question.x_answer_alpha=="A":
                yaml_answer_key[response_directory_key]["Questions"][question.question_num]["Correct Answer"]["Scenario"]=question.A_value
            elif question.x_answer_alpha=="B":
                yaml_answer_key[response_directory_key]["Questions"][question.question_num]["Correct Answer"]["Scenario"]=question.B_value
            yaml_answer_key[response_directory_key]["Questions"][question.question_num]["User Answer"]={}
            yaml_answer_key[response_directory_key]["Questions"][question.question_num]["User Answer"]["Answer"]=question.user_X_value
            if question.user_X_value=="A":
                yaml_answer_key[response_directory_key]["Questions"][question.question_num]["User Answer"]["Scenario"]=question.A_value
            elif question.user_X_value=="B":
                yaml_answer_key[response_directory_key]["Questions"][question.question_num]["User Answer"]["Scenario"]=question.B_value
        yaml.dump(yaml_answer_key, test_results, default_flow_style=False)
    print("graded: ", response_directory)
    return yaml_answer_key

if __name__ == "__main__":
    root_directory=os.getcwd()
    args=parser.parse_args()
    # collect data on two scenario's from answer_key.yml
    scenario_one_latency_data={}
    scenario_two_latency_data={}
    with open("answer_key.yml") as answer_key:
        key=yaml.load(answer_key)
        scenario_one_latency_data=key["Scenario One"]
        scenario_two_latency_data=key["Scenario Two"]

    # If no file_path argument then just grade root directory
    # If file_path is given then all directories in file_path need to be graded and master key needs to be made 
    if args.file_path == None:
        grade(root_directory)
    else:
        # what happens if multiple responses in same directory?
        # final addition is to collect data on everything at top of file in nice conclusion readable format
        master_answer_key = []
        master_total_correct=0
        master_total_questions=0
        master_total_preference_scenario_one=0
        master_total_preference_scenario_two=0
        master_preference_score_scenario_one=0
        master_preference_score_scenario_two=0
        master_files_graded_count=0
        for dirpath, dirnames, filenames in os.walk(args.file_path):
            if (len(filenames)!=0):
                for file_ in filenames:
                    if ("responses" in file_ ) and ("xlsx" in file_):
                        master_files_graded_count = master_files_graded_count + 1 
                        print(dirpath)
                        user_test_score_data=grade(dirpath)
                        response_directory_key = dirpath.replace(":", "_")
                        del user_test_score_data[response_directory_key]["Questions"]#
                        master_total_correct=master_total_correct + user_test_score_data[response_directory_key]["Total Correct"]
                        master_total_questions=master_total_questions + user_test_score_data[response_directory_key]["Total Questions"]
                        master_total_preference_scenario_one=master_total_preference_scenario_one + user_test_score_data[response_directory_key]["Total Preference For Scenario One"]
                        master_total_preference_scenario_two=master_total_preference_scenario_two + user_test_score_data[response_directory_key]["Total Preference For Scenario Two"]
                        master_preference_score_scenario_one=master_preference_score_scenario_one + user_test_score_data[response_directory_key]["Degree of Preference For Scenario One"]
                        master_preference_score_scenario_two=master_preference_score_scenario_two + user_test_score_data[response_directory_key]["Degree of Preference For Scenario Two"]
                        master_answer_key.append(user_test_score_data)
        os.chdir(root_directory)
        master_total_correct_dict={"Total Correct":master_total_correct}
        master_total_questions_dict={"Total Questions":master_total_questions}
        master_total_preference_scenario_one_dict={"Total Preference For Scenario One":master_total_preference_scenario_one}
        master_total_preference_scenario_two_dict={"Total Preference For Scenario Two":master_total_preference_scenario_two}
        master_preference_score_scenario_one_dict={"Average Degree of Preference for Scenario One":master_preference_score_scenario_one/master_files_graded_count}
        master_preference_score_scenario_two_dict={"Average Degree of Preference for Scenario Two":master_preference_score_scenario_two/master_files_graded_count}
        with open("master_test_results.yml", "w") as master_test_results:
            yaml.dump(scenario_one_latency_data, master_test_results, default_flow_style=False)
            yaml.dump(scenario_two_latency_data, master_test_results, default_flow_style=False)
            yaml.dump(master_total_correct_dict, master_test_results, default_flow_style=False)
            yaml.dump(master_total_questions_dict, master_test_results, default_flow_style=False)
            yaml.dump(master_total_preference_scenario_one_dict, master_test_results, default_flow_style=False)
            yaml.dump(master_total_preference_scenario_two_dict, master_test_results, default_flow_style=False)
            yaml.dump(master_preference_score_scenario_one_dict, master_test_results, default_flow_style=False)
            yaml.dump(master_preference_score_scenario_two_dict, master_test_results, default_flow_style=False)            
            yaml.dump(master_answer_key, master_test_results, default_flow_style=False)
        print("done!")