


import os
import yaml
import openpyxl
import sys
import argparse
import manualtest
import logging

"""
grade.py 

Script to grade the response excel sheets collected from a manual test
generated using manualtest.py. If a file path is given as a command line parameter,
the program will crawl all files in this directory and grade files with 2 
regular expression keywords: “responses” and .xlsx. A individual test_results file
will be created for each respsones.xlsx file graded and a master_test_results file 
will be created in the root directory

Required:
responses.xlsx located in root directory or use -fp from the command line to specify a location
answer_key.yml generated from manual_test.py

Responsibilites Include
Grading the responses.xlsx excel sheet 
creating test_results.yml containing the results

"""

parser = argparse.ArgumentParser(description="Script to grade listening tests, specify a file to grade a collection of tests. Default setting is to search root directory for responses.xlsx. See manual for details on grading multiple responses")
parser.add_argument("-fp", dest="file_path", help="(optional) Absolute directory path to a collection of tests results from a variety of users. The program will crawl all files in this directory and grade files with 2 regular expression keywords: “responses” and .xlsx. Default: The root directory")
parser.add_argument("-o", dest="output_path", help="(optional) Absolute file path to location for test results documents. Default: The root directory")

root_directory=os.getcwd()

EXCEL_SHEET_STARTING_ROW=21
EXCEL_SHEET_ENDING_ROW=46

USER_ANSWER_KEY="user_answer"
USER_PREFERENCE_KEY="user_preference_weight"
USER_X_VALUE_KEY="user_X_value"
USER_CONFIDENCE_KEY="user_answer_confidence"
X_ANSWER_KEY="x_answer_alpha"
A_VALUE_KEY="A_value"
B_VALUE_KEY="B_value"
EXCEL_QUESTION_LOC="A"
EXCEL_USER_ANSWER_LOC="B"
EXCEL_USER_PREFERENCE_LOC="C"
EXCEL_X_VALUE_LOC="D"
EXCEL_USER_CONFIDENCE_LOC="E"
ANSWER_KEY_NAME="answer_key.yml"
ANSWER_KEY_QUESTION_KEY="Q_"
ANSWER_KEY_SCENARIO_ONE="scenario one"
ANSWER_KEY_SCENARIO_TWO="scenario two"
SCENARIO_ONE_DATA_FILE_KEY="Scenario One"
SCENARIO_TWO_DATA_FILE_KEY="Scenario Two"
RESPONSES_KEY_WORD="responses"
XLSX_KEY_WORD="xlsx"
USER_ANSWER_CASE_A="A"
USER_ANSWER_CASE_B="B"
TOTAL_CORRECT_KEY="Total Correct"
TEST_RESULTS_FILE_NAME="test_results.yml"
TOTAL_QUESTIONS_KEY="Total Questions"
SCENARIO_ONE_PREFERENCE_KEY="Total Preference For Scenario One"
SCENARIO_TWO_PREFERENCE_KEY="Total Preference For Scenario Two"
SCENARIO_ONE_AVERAGE_PREFERENCE_KEY="Degree of Preference For Scenario One"
SCENARIO_TWO_AVERAGE_PREFERENCE_KEY="Degree of Preference For Scenario Two"
QUESTIONS_KEY="Questions"
CORRECT_KEY="Correct"
CORRECT_ANSWER_KEY="Correct Answer"
KEY_ANSWER="Answer"
SCENARIO_KEY="Scenario"
USER_ANSWER_KEY_ANSWER_KEY="User Answer"
MASTER_TEST_RESULTS_FILE_NAME="master_test_results.yml"
MASTER_SCENARIO_ONE_AVERAGE_PREFERENCE_KEY="Average Degree of Preference for Scenario One"
MASTER_SCENARIO_TWO_AVERAGE_PREFERENCE_KEY="Average Degree of Preference for Scenario Two"


def _collect_user_answers(response_document, results):
    logging.info("Enter: collect_user_answers")
    for case_num, row_num in enumerate(range(EXCEL_SHEET_STARTING_ROW, EXCEL_SHEET_ENDING_ROW)):
        loc_question_num = EXCEL_QUESTION_LOC+str(row_num)
        question_num = response_document[loc_question_num].value
        loc_user_answer = EXCEL_USER_ANSWER_LOC+str(row_num)
        user_answer = response_document[loc_user_answer].value
        loc_user_preference_weight = EXCEL_USER_PREFERENCE_LOC+str(row_num)
        user_preference_weight = response_document[loc_user_preference_weight].value
        loc_user_X_value =EXCEL_X_VALUE_LOC+str(row_num)
        user_X_value = response_document[loc_user_X_value].value
        loc_user_answer_confidence =EXCEL_USER_CONFIDENCE_LOC+str(row_num)
        user_answer_confidence = response_document[loc_user_answer_confidence].value
        question_info = manualtest.Answer(case_num, user_answer=user_answer,user_preference_weight=user_preference_weight, user_X_value=user_X_value, user_answer_confidence=user_answer_confidence)
        results.append(question_info)
    # score the answers
    try:
        with open(ANSWER_KEY_NAME) as key:
            logging.info("Comparing user answers to answer_key.yml")
            key = yaml.load(key)
            for num, question in enumerate(results):
                num = str(ANSWER_KEY_QUESTION_KEY+str(num))
                question.x_answer_alpha=key[num][X_ANSWER_KEY]
                question.A_value=key[num][A_VALUE_KEY]
                question.B_value=key[num][B_VALUE_KEY]
                question.grade()
    except FileNotFoundError:
        print("No answer_key.yml found...Exiting now")
        logging.debug("No answer_key.yml found. answer_key.yml was found during initialization of program."
                      "The file was thus deleted during runtime")
        sys.exit()
    logging.info("Exit: collect_user_answers")
    return results


def _find_response_document(response_directory):
    logging.info("Enter: find_response_document")
    for dirpath, dirname, filenames in os.walk(response_directory):
        for file_ in filenames:
            if (RESPONSES_KEY_WORD in file_) and (XLSX_KEY_WORD in file_):
                logging.info("Exit: find_response_document, file: {}".format(file_))
                return openpyxl.load_workbook(os.path.join(dirpath, file_)).active
    logging.debug("Exit: find_response_document, no document found")


def _collect_analytics(results, response_directory):
    logging.info("Enter: collect_analytics")
    # Count corect questions and grade
    total_correct=0
    total_questions=0
    for question_num, question in enumerate(results):
        print(question_num, ": ", question.correct)
        total_questions = total_questions+1
        if question.correct:
            total_correct = total_correct + 1
    print("total correct: ", total_correct)
    print("grade: ", float(total_correct/total_questions))
    # Collect preference scores and total preference for each question
    total_preference_for_scenario_one=0
    scenario_one_preference_score=0
    degree_of_preference_scenario_one=0
    total_preference_for_scenario_two=0
    scenario_two_preference_score=0
    degree_of_preference_scenario_two=0
    for analytics in results:
        print(analytics.question_num,": answer: ", analytics.x_answer_alpha, "listener: ",
              analytics.user_answer, analytics.user_preference_weight, analytics.user_X_value,
              analytics.user_answer_confidence)
        # If question is correct, find which scenario the person prefered and by how much
        if analytics.correct:
            if analytics.user_answer == USER_ANSWER_CASE_A:
                if analytics.A_value==ANSWER_KEY_SCENARIO_ONE:
                    total_preference_for_scenario_one = total_preference_for_scenario_one + 1
                    scenario_one_preference_score = scenario_one_preference_score + analytics.user_preference_weight
                if analytics.A_value==ANSWER_KEY_SCENARIO_TWO:
                    total_preference_for_scenario_two = total_preference_for_scenario_two + 1       
                    scenario_two_preference_score = scenario_two_preference_score + analytics.user_preference_weight
            if analytics.user_answer == USER_ANSWER_CASE_B:
                if analytics.B_value==ANSWER_KEY_SCENARIO_ONE:
                    total_preference_for_scenario_one = total_preference_for_scenario_one + 1
                    scenario_one_preference_score = scenario_one_preference_score + analytics.user_preference_weight
                if analytics.B_value==ANSWER_KEY_SCENARIO_TWO:
                    total_preference_for_scenario_two = total_preference_for_scenario_two + 1       
                    scenario_two_preference_score = scenario_two_preference_score + analytics.user_preference_weight
    print("Points for Scenario One: ", total_preference_for_scenario_one)
    print("Points for Scenario Two: ", total_preference_for_scenario_two)
    if total_preference_for_scenario_one == 0:
        print("Degree of seperation for Scenario One: 0")
    else:
        print("Degree of seperation for Scenario One: ", scenario_one_preference_score/total_preference_for_scenario_one)
        degree_of_preference_scenario_one=scenario_one_preference_score/total_preference_for_scenario_one
    if total_preference_for_scenario_two == 0:
        print("Degree of seperation for Scenario Two: 0")
    else:
        print("Degree of seperation for Scenario Two: ", scenario_two_preference_score/total_preference_for_scenario_two)
        degree_of_preference_scenario_two=scenario_two_preference_score/total_preference_for_scenario_two
    # Output everything to test_results.yml in the response directory
    # Save data to dictionary and return yaml_answer_key
    with open(os.path.join(response_directory, TEST_RESULTS_FILE_NAME), "w") as test_results:  
        yaml_answer_key={}
        response_directory_key = response_directory.replace(":", "_")
        yaml_answer_key[response_directory_key]={}
        yaml_answer_key[response_directory_key][TOTAL_CORRECT_KEY]=total_correct
        yaml_answer_key[response_directory_key][TOTAL_QUESTIONS_KEY]=len(results)
        yaml_answer_key[response_directory_key][SCENARIO_ONE_PREFERENCE_KEY]=total_preference_for_scenario_one
        yaml_answer_key[response_directory_key][SCENARIO_TWO_PREFERENCE_KEY]=total_preference_for_scenario_two
        yaml_answer_key[response_directory_key][SCENARIO_ONE_AVERAGE_PREFERENCE_KEY]=degree_of_preference_scenario_one
        yaml_answer_key[response_directory_key][SCENARIO_TWO_AVERAGE_PREFERENCE_KEY]=degree_of_preference_scenario_two
        yaml_answer_key[response_directory_key][QUESTIONS_KEY]={}
        # Save question by question results
        for question in results:
            yaml_answer_key[response_directory_key][QUESTIONS_KEY][question.question_num]={}
            yaml_answer_key[response_directory_key][QUESTIONS_KEY][question.question_num][CORRECT_KEY]=question.correct
            yaml_answer_key[response_directory_key][QUESTIONS_KEY][question.question_num][CORRECT_ANSWER_KEY]= {}
            yaml_answer_key[response_directory_key][QUESTIONS_KEY][question.question_num][CORRECT_ANSWER_KEY][KEY_ANSWER]=question.x_answer_alpha
            if question.x_answer_alpha==USER_ANSWER_CASE_A:
                yaml_answer_key[response_directory_key][QUESTIONS_KEY][question.question_num][CORRECT_ANSWER_KEY][SCENARIO_KEY]=question.A_value
            elif question.x_answer_alpha==USER_ANSWER_CASE_B:
                yaml_answer_key[response_directory_key][QUESTIONS_KEY][question.question_num][CORRECT_ANSWER_KEY][SCENARIO_KEY]=question.B_value
            yaml_answer_key[response_directory_key][QUESTIONS_KEY][question.question_num][USER_ANSWER_KEY_ANSWER_KEY]={}
            yaml_answer_key[response_directory_key][QUESTIONS_KEY][question.question_num][USER_ANSWER_KEY_ANSWER_KEY][KEY_ANSWER]=question.user_X_value
            if question.user_X_value==USER_ANSWER_CASE_A:
                yaml_answer_key[response_directory_key][QUESTIONS_KEY][question.question_num][USER_ANSWER_KEY_ANSWER_KEY][SCENARIO_KEY]=question.A_value
            elif question.user_X_value==USER_ANSWER_CASE_B:
                yaml_answer_key[response_directory_key][QUESTIONS_KEY][question.question_num][USER_ANSWER_KEY_ANSWER_KEY][SCENARIO_KEY]=question.B_value
        yaml.dump(yaml_answer_key, test_results, default_flow_style=False)
    print("graded: ", response_directory)
    logging.info("Exit: collect_analytics")
    return yaml_answer_key


def _grade(response_directory): 
    logging.info("Enter: grade")
    global root_directory
    results=[]
    # Find responses excel sheet in the provided directory 
    response_doc = _find_response_document(response_directory)
    # Parse excel spread sheet
    results = _collect_user_answers(response_doc, results)
    # print and output data to test_results  
    logging.info("Exit: grade")
    return _collect_analytics(results, response_directory)

# External Methods
def main():
    root_directory=os.getcwd()
    args=parser.parse_args()
    # collect data on two scenario's from answer_key.yml
    scenario_one_latency_data={}
    scenario_two_latency_data={}
    logging.info("collecting Scenario One and Scenario Two Data from answer_key.yml")
    try:
        with open(ANSWER_KEY_NAME) as answer_key:
            logging.info("answer_key.yml found")
            key=yaml.load(answer_key)
            scenario_one_latency_data=key[SCENARIO_ONE_DATA_FILE_KEY]
            scenario_two_latency_data=key[SCENARIO_TWO_DATA_FILE_KEY]
            logging.info("File successfully opened and parsed")
    except FileNotFoundError:
        print("answer_key.yml was not found in root directory. Exiting")
        logging.debug("No Answer_key.yml found")
        sys.exit()
    # If no file_path argument then just grade root directory
    # If file_path is given then all directories in file_path need to be graded and master key needs to be made 
    if args.file_path == None:
        logging.info("No file_path argument given")
        _grade(root_directory)
        logging.info("exiting")
        print("done")
    else:
        logging.info("file_path to be searched: {}".format(args.file_path))
        master_answer_key = []
        master_total_correct=0
        master_total_questions=0
        master_total_preference_scenario_one=0
        master_total_preference_scenario_two=0
        master_preference_score_scenario_one=0
        master_preference_score_scenario_two=0
        master_files_graded_count=0
        # Crawl file path for all responses.xlsx files
        for dirpath, dirnames, filenames in os.walk(args.file_path):
            for file_ in filenames:
                if (RESPONSES_KEY_WORD in file_ ) and (XLSX_KEY_WORD in file_):
                    logging.info("file found to be graded at {}".format(os.path.join(dirpath, file_)))
                    master_files_graded_count = master_files_graded_count + 1 
                    print(dirpath)
                    user_test_score_data=_grade(dirpath)
                    response_directory_key = dirpath.replace(":", "_")
                    # take the response results, delete the question by question answers and add results to master key
                    del user_test_score_data[response_directory_key][QUESTIONS_KEY]
                    master_total_correct=master_total_correct + user_test_score_data[response_directory_key][TOTAL_CORRECT_KEY]
                    master_total_questions=master_total_questions + user_test_score_data[response_directory_key][TOTAL_QUESTIONS_KEY]
                    master_total_preference_scenario_one=master_total_preference_scenario_one + user_test_score_data[response_directory_key][SCENARIO_ONE_PREFERENCE_KEY]
                    master_total_preference_scenario_two=master_total_preference_scenario_two + user_test_score_data[response_directory_key][SCENARIO_TWO_PREFERENCE_KEY]
                    master_preference_score_scenario_one=master_preference_score_scenario_one + user_test_score_data[response_directory_key][SCENARIO_ONE_AVERAGE_PREFERENCE_KEY]
                    master_preference_score_scenario_two=master_preference_score_scenario_two + user_test_score_data[response_directory_key][SCENARIO_TWO_AVERAGE_PREFERENCE_KEY]
                    logging.info("{} file was graded and added to master_key.yml".format(os.path.join(dirpath, file_)))
                    master_answer_key.append(user_test_score_data)
        # Take master variables and yaml dump to master_test_results.yml in root directory
        master_total_correct_dict={TOTAL_CORRECT_KEY:master_total_correct}
        master_total_questions_dict={TOTAL_QUESTIONS_KEY:master_total_questions}
        master_total_preference_scenario_one_dict={SCENARIO_ONE_PREFERENCE_KEY:master_total_preference_scenario_one}
        master_total_preference_scenario_two_dict={SCENARIO_TWO_PREFERENCE_KEY:master_total_preference_scenario_two}
        master_preference_score_scenario_one_dict={MASTER_SCENARIO_ONE_AVERAGE_PREFERENCE_KEY:master_preference_score_scenario_one/master_files_graded_count}
        master_preference_score_scenario_two_dict={MASTER_SCENARIO_TWO_AVERAGE_PREFERENCE_KEY:master_preference_score_scenario_two/master_files_graded_count}
        with open(MASTER_TEST_RESULTS_FILE_NAME, "w") as master_test_results:
            logging.info("master results file created at {}".format(MASTER_TEST_RESULTS_FILE_NAME))
            yaml.dump(scenario_one_latency_data, master_test_results, default_flow_style=False)
            yaml.dump(scenario_two_latency_data, master_test_results, default_flow_style=False)
            yaml.dump(master_total_correct_dict, master_test_results, default_flow_style=False)
            yaml.dump(master_total_questions_dict, master_test_results, default_flow_style=False)
            yaml.dump(master_total_preference_scenario_one_dict, master_test_results, default_flow_style=False)
            yaml.dump(master_total_preference_scenario_two_dict, master_test_results, default_flow_style=False)
            yaml.dump(master_preference_score_scenario_one_dict, master_test_results, default_flow_style=False)
            yaml.dump(master_preference_score_scenario_two_dict, master_test_results, default_flow_style=False)            
            yaml.dump(master_answer_key, master_test_results, default_flow_style=False)
        logging.info("information output to YAML at {}".format(MASTER_TEST_RESULTS_FILE_NAME))
        print("done")

if __name__ == "__main__":
    # instantiate grade.log
    logging.basicConfig(filename="manualtest.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(module)s line: %(lineno)d, %(message)s")
    main()

   