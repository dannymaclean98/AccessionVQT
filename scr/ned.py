# ned
# Network Disruption module

import paramiko
import yaml
import sys
import logging
import socket

"""
ned.py - Network Disruption Module 

This method is built to ssh onto a linux machine, run a list of 
linux traffic control commands and terminate connection with the 
linux machine. Please refer to router_config.yml to fill in the details 
of the linux machine to ssh onto. router_config.yml also contains 
a list of parameters where commands can be specified.
init() should be called to initialize the environment and 
execute_next_command() can be called to iterate through a 
list of specified commands.
Responsibilites
1) Parse Config
2) Create SSH with the router
3) execute commands
4) terminate connection with the router
"""

logging.basicConfig(filename="ned.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(module)s line: %(lineno)d, %(message)s")
# file globals
login_info = {}
device_type=""
network_parameter_list = []
SSH = None
current_network_condition=None
network_generator=None

#Global strings
CONFIG_FILE = "router_config.yml"
NORMAL="normal"
PARETO="pareto"
PARETONORMAL="paretonormal"
#Linux traffic control commands
MODPROBE_CMD  = "modprobe sch_netem"
DEL_NETEM="tc qdisc del dev {} root"
ADD_NETEM="tc qdisc add dev {} root netem "
LOSS_NETEM_SUBSTRING= "loss {} {} "
DELAY_NETEM_SUBSTRING="delay {}ms"
DELAY_DISTRIBUTION_NETEM_SUBSTRING=" {}ms distribution {}"

#Dictionary keys
IP_ADDRESS = "IP_address"
NETWORK_INTERFACE="Network_Interface"
LOGIN="Login_info"
USERNAME="Username"
PASSWORD="Password"
COMMANDS="Commands"
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


# External Methods
def init():
    # parse
    # check
    # login
    # clear
    """
    Parse router_config.yml for IP_address, username and password to SSH to the 
    accompanying router. Parse list of network commands in router_config.yml.
    Initiate connection to mini router and delete all existing commands.
    """
    logging.info("Enter: init")
    global login_info
    global SSH
    global device_type
    _parse_config()
    _check_cfg()
    try:
        print("Connecting to router, will take just a second...\nIf program does not continue in several seconds, please double check that the router is on and your PC is on the right network")
        SSH = paramiko.SSHClient()
        SSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        SSH.connect(hostname=login_info[IP_ADDRESS],
                    username=login_info[USERNAME], password=login_info[PASSWORD])
        print("Connected!")
        SSH.exec_command(MODPROBE_CMD)
        in_, out, error = SSH.exec_command("tc q")
        out = list(out)
        for item in out:
            if "qdisc netem" in item:
                print("Current netem conditions to be deleted: ", item)
                print("Deleting this condition... ")
                in_, out, error = SSH.exec_command(
                    DEL_NETEM.format(device_type))
        error = list(error)
        if(len(error) > 0):
            print("there has been an error: ", error)
            logging.debug("Error encountered while resetting router: {}".format(error))
    except paramiko.BadHostKeyException:
        logging.debug("BadHostKeyException raised during SSH connection. Server’s host key could not be verified")
        print("BadHostKeyException raised during SSH connection. Server’s host key could not be verified, program will now exit")
        sys.exit()
    except paramiko.AuthenticationException:
        logging.debug("AuthenticationException raised during SSH connection. authentication failed")
        print("AuthenticationException raised during SSH connection. authentication failed, program will now exit")
        sys.exit()
    except paramiko.SSHException:
        logging.debug("SSHException raised during SSH connection. there was any other error connecting or establishing an SSH session")
        print("SSHException raised during SSH connection. there was any other error connecting or establishing an SSH session, program will now exit")
        sys.exit()
    except socket.error:
        logging.debug("socket.error raised during SSH connection. a socket error occurred while connecting")
        print("socket.error raised during SSH connection. a socket error occurred while connecting, program will now exit")
        sys.exit()
    logging.info("Exit: init")


def execute_next_command():
    """Execute the next command in the list of commands from router_config.yml
    When all commands have been executed, calls to the function will return a null
    Parameters:
    None
    Returns:
    True/False:         True indicates that the command was processed, 
                        False indicates there are no more commands to 
                        iterate through
    """
    logging.info("Enter: execute_next_command")
    global current_network_condition
    global network_generator
    try:
        # Store the state in a temporary state variable until the state is actually updated
        next_current_network_condition = next(_get_command_generator())
        logging.info("Current condition: {}".format(current_network_condition))
    except:
        logging.info("Exit: execute_next_command, command generator has raised stop iteration")
        return False
    linux_command = _build_command(current_network_condition)
    _execute_command(linux_command)
    current_network_condition=next_current_network_condition
    logging.info("Exit: execute_next_command")
    return True


def get_current_conditions():
    """Query network status on the router. 
    Parameters None 
    Returns:
    current_network_condition dictionary:   current_network_dictionary keys:
                                            command[LOSS][TYPE]=string - gemodel or random
                                            command[LOSS][VALUE]=1-4 space separated 
                                            integers depending on loss type
                                            command[DELAY][TIME]=single integer representing
                                            uniform delay
                                            command[DELAY][DISTRIBUTION]=string-jitter
                                            distribution type
                                            command[DELAY][JITTER]= integer for jitter
                                            distributions
    """
    logging.info("Enter: get_current_conditions")
    global current_network_condition
    logging.info("Request for current network conditions")
    logging.info("Exit: get_current_conditions")
    return current_network_condition


def terminate():
    """Close SSH connection and delete any netem parameters currently on device
    Parameters:
    None
    Return:
    None
    """
    logging.info("Enter: terminate")
    global SSH
    print("Resetting router...")
    in_, out, error = SSH.exec_command("tc q")
    out = list(out)
    for item in out:
        if "qdisc netem" in item:
            print("Current netem conditions to be deleted: ", item)
            print("Deleting this condition... ")
            try:
                in_, out, error = SSH.exec_command(
                    DEL_NETEM.format(device_type))
            except paramiko.SSHException:
                logging.debug("SSHException encountered, the server failed to execute the command, exiting")
                print("SSHException encountered, the server failed to execute the command, exiting")
                sys.exit()
    error = list(error)
    if(len(error) > 0):
        logging.debug("There was an error executing this command: {}".format(error))
        print("there has been an error: ", error)
    SSH.close()
    logging.info("Exit: terminate")


# Internal Methods
def _get_next_command():
    """Generate the next command in the command list
    Parameters:
    None
    Returns:
    None
    """
    logging.info("Enter: get_next_command")
    global network_parameter_list
    for command in network_parameter_list:
        logging.info("call to generator object")
        yield command
    logging.info("Exit: get_next_command")


def _get_command_generator():
    # First call to this function initiates the command generator variable
    # Each call after returns the next element in the generator
    logging.info("Enter: get_command_generator")
    global network_generator
    if network_generator is None:
        logging.info("command generator object not initialized, not initializing")
        network_generator = _get_next_command()
    logging.info("Exit: get_command_generator")
    return network_generator


def _build_command(command):
    # Turn the command dictionary into a linux traffic control compatible string
    logging.info("Enter: build_command")
    global device_type
    string_base = ADD_NETEM.format(device_type)
    loss_string=""
    delay_string=""
    if command[LOSS][TYPE]!=None:
        loss_string = LOSS_NETEM_SUBSTRING.format(command[LOSS][TYPE], command[LOSS][VALUE])
    if command[DELAY][TIME]!=None:
        delay_string = DELAY_NETEM_SUBSTRING.format(command[DELAY][TIME])
        if command[DELAY][JITTER]!=None:
            delay_string = delay_string +DELAY_DISTRIBUTION_NETEM_SUBSTRING.format(command[DELAY][JITTER], command[DELAY][DISTRIBUTION])
    logging.info("Exit: build_command")
    return string_base + loss_string + delay_string
 

def _execute_command(command):
    """Execute command on linux machine
    Parameters:
    command:    A dictionary with the following dictionary keys:
                command[LOSS][TYPE]=string - gemodel or random
                command[LOSS][VALUE]=1-4 space separated 
                integers depending on loss type
                command[DELAY][TIME]=single integer representing
                uniform delay
                command[DELAY][DISTRIBUTION]=string-jitter
                distribution type
                command[DELAY][JITTER]= integer for jitter
                distributions     
    Returns:
    None
    """
    logging.info("Enter: execute_command")
    global SSH
    global device_type
    logging.info("command: {}".format(command))
    try:
        in_, out, error = SSH.exec_command(DEL_NETEM.format(device_type))
    except paramiko.SSHException:
        logging.debug("SSHException encountered, the server failed to execute the command, exiting")
        print("SSHException encountered, the server failed to execute the command, exiting")
        sys.exit()
    try:
        in_, out, error = SSH.exec_command(command)
    except paramiko.SSHException:
        logging.debug("SSHException encountered, the server failed to execute the command, exiting")
        print("SSHException encountered, the server failed to execute the command, exiting")
        sys.exit()
    error = list(out)
    if(len(error) != 0):
        logging.debug("There was an error executing this command: {}".format(error))
        print("There was an error executing this command: ", error)
    logging.info("Exit: execute_command")


def _nums_in_string(string):
    # Count the number of space separated numbers in a string
    logging.info("Enter: nums_in_string")
    num_count=0
    string_list = str(string).split(" ")
    for elem in string_list:
        if elem.isnumeric():
            num_count = num_count + 1
    logging.info("Exit: nums_in_string, nums: {}".format(num_count))
    return num_count, string_list


def _check_cfg():
    # Confirm the value in the config are vaild
    # No entries in the config will default to a linux command with no disruptions
    logging.info("Enter: check_cfg")
    global login_info
    global network_parameter_list
    global device_type
    if (login_info[IP_ADDRESS]==None) or (login_info[USERNAME]==None) or (login_info[PASSWORD]==None):
        logging.debug("Please fill in the login information in {}. Now exiting...".format(CONFIG_FILE))
        print("Please fill in the login information in {}. Now exiting...".format(CONFIG_FILE))
        sys.exit()
    for index, command in enumerate(network_parameter_list):
        if (command[LOSS][TYPE]==None) and (command[DELAY][TIME]==None):
            # DAM - MRR solution just overriding values to zero so the command gets executed. How does this look?
            command[LOSS][TYPE]=RANDOM
            command[LOSS][VALUE]=0

        # Confirm loss config is valid
        if (command[LOSS][TYPE]==None) and (command[LOSS][VALUE]!=None):
            logging.debug("A loss type was not specifed, please fill this field in the config. Exiting")
            print("A loss type was not specifed, please fill this field in the config. Exiting")
            sys.exit()
        if (command[LOSS][TYPE]!=None):
            # number_list is a list of the individual numbers in the list 
            num_of_nums, number_list = _nums_in_string(command[LOSS][VALUE])
            if max(number_list) > 99:
                logging.debug("A number 100 or greater was specified, exiting")
                print("A number 100 or greater was specified, exiting")
                sys.exit()
            if min(number_list) < 0:
                logging.debug("A number less than zero was specified, exiting")
                print("A number less than zero was specified, exiting")
                sys.exit()
            if (command[LOSS][TYPE]==RANDOM):
                if (num_of_nums > 1) or (num_of_nums==0):
                    logging.debug("Uniform loss only takes a single number for input, please check this field in the config. Exiting")
                    print("Uniform loss only takes a single number for input, please check this field in the config. Exiting")
                    sys.exit()
            elif (command[LOSS][TYPE]==GEMODEL):
                if (num_of_nums > 4) or (num_of_nums==0):
                    logging.debug("Gemodel loss takes 1 - 4 numbers as input, please check this field in the config file. Exiting")
                    print("Gemodel loss takes 1 - 4 numbers as input, please check this field in the config file. Exiting")
                    sys.exit()
            else:
                logging.debug("Unrecognized loss type value, please check this field in the config file. Exiting")
                print("Unrecognized loss type value, please check this field in the config file. Exiting")
                sys.exit()
        # Confirm delay config is valid
        if (command[DELAY][TIME]==None) and (command[DELAY][JITTER]!=None):
            logging.debug("Jitter distribution was specified with a zero second delay, please check this field in the config file. Exiting")
            print("Jitter distribution was specified with a zero second delay, please check this field in the config file. Exiting")
            sys.exit()
        if command[DELAY][TIME]!= None:
            num_of_nums, number_list = _nums_in_string(command[DELAY][TIME])
            if num_of_nums > 1:
                logging.debug("Too many numbers are specified in the jitter distribution field. Exiting")
                print("Too many numbers are specified in the jitter distribution field. Exiting")
                sys.exit()
            if min(number_list) < 0:
                logging.debug("A number less than zero was specified, exiting")
                print("A number less than zero was specified, exiting")
                sys.exit()
            if command[DELAY][DISTRIBUTION]!= None:
                if (command[DELAY][DISTRIBUTION]!=PARETONORMAL) and (command[DELAY][DISTRIBUTION]!=NORMAL) and (command[DELAY][DISTRIBUTION]!=PARETO):
                    logging.debug("Invalid delay jitter type, please check this field in the config file. Exiting")
                    print("Invalid delay jitter type, please check this field in the config file. Exiting")
                    sys.exit()
                elif command[DELAY][JITTER]==None:
                    logging.debug("A jitter type was specified but no value was given, please check this field in the config. Exiting")
                    print("A jitter type was specified but no value was given, please check this field in the config. Exiting")
                    sys.exit()
                elif (command[DELAY][JITTER]!=None):
                    num_of_nums, number_list = _nums_in_string(command[DELAY][JITTER])
                    if num_of_nums > 1:
                        logging.debug("Too many numbers are specified in the jitter distribution field. Exiting")
                        print("Too many numbers are specified in the jitter distribution field. Exiting")
                        sys.exit()
                    if min(number_list) < 0:
                        logging.debug("A number less than zero was specified, exiting")
                        print("A number less than zero was specified, exiting")
                        sys.exit()
    logging.info("Exit: check_cfg")
        

def _parse_config():
    # Load the accompanying yaml file. This is
    # automatically called from init()
    global login_info
    global network_parameter_list
    global device_type
    with open(CONFIG_FILE) as cfg_data:
        cfg = yaml.load(cfg_data)
        login_info = {IP_ADDRESS: cfg[LOGIN][IP_ADDRESS],
                      USERNAME: cfg[LOGIN][USERNAME], PASSWORD: cfg[LOGIN][PASSWORD]}
        device_type = cfg[NETWORK_INTERFACE]
        network_parameter_list = cfg[COMMANDS]
        logging.info("{} successfully parsed".format(CONFIG_FILE))









