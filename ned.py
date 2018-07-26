# ned
# Network Disruption module

import paramiko
import yaml
import sys
import logging
log = logging.getLogger('ATAT')
# Responsibilites
# 1) Parse Config
# 2) Create SSH with the router
# 3) execute commands
# 4) terminate connection with the router
"""
lines 140 and 155

"""
# file globals
login_info = {}
device_type=""
network_parameter_list = []
SSH = None
current_network_condition=None
network_generator=None
# External Methods
def parse():
    global login_info
    global network_parameter_list
    global device_type
    with open("router_config.yml") as cfg_data:
        cfg = yaml.load(cfg_data)
        login_info = {"IP_Address": cfg["Login_info"]["IP_address"],
                      "Username": cfg["Login_info"]["Username"], "Password": cfg["Login_info"]["Password"]}
        device_type = cfg["Device"]
        network_parameter_list = cfg["Commands"]
        log.info("router_config.yml successfully parsed")


def init():
    # parse
    # check
    # login
    # clear
    """Initiate connection to mini router and delete all existing commands
    Parameters: IPaddress - string
    Username=string to login to the router
    Password=string to login to the router
    Return SSH client object"""
    global login_info
    global SSH
    global device_type
    parse()
    check_cfg()
    try:
        print("Connecting to router, will take just a second...\nIf program does not continue in several seconds, please double check that the router is on and your PC is on the right network")
        SSH = paramiko.SSHClient()
        SSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        SSH.connect(hostname=login_info["IP_Address"],
                    username=login_info["Username"], password=login_info["Password"])
        print("Connected!")
        SSH.exec_command("modprobe sch_netem")
        in_, out, error = SSH.exec_command("tc q")
        out = list(out)
        for item in out:
            if "qdisc netem" in item:
                print("Current netem conditions to be deleted: ", item)
                print("Deleting this condition... ")
                in_, out, error = SSH.exec_command(
                    "tc qdisc del dev {} root".format(device_type))
        print("Setting control conditions...")
        in_, out, error = SSH.exec_command(
            "tc qdisc add dev {} root netem loss 0%".format(device_type))
        error = list(error)
        if(len(error) > 0):
            print("there has been an error: ", error)
            log.debug("Error encountered while resetting router: {}".format(error))
    except TimeoutError:
        log.debug("Time out error encountered during ssh to router")
        print("Could not connect to router, program will now exit")
        log.debug("Time out Error encountered when trying to log on")
        sys.exit()


def execute_next_command():
    global current_network_condition
    global network_generator
    try:
        current_network_condition = next(get_command_generator())
        log.info("Current condition: {}".format(current_network_condition))
    except:
        log.info("command generator has raised stop iteration")
        return False
    linux_command = build_command(current_network_condition)
    execute_command(linux_command)
    return True


def get_current_conditions():
    global current_network_condition
    log.info("Request for current network conditions")
    return current_network_condition


def terminate():
    # exception: timeout error or if router doesn't get to log off 
    """Close SSH connection and delete any netem parameters currently on device
    Parameters: SSH - object with SSH connection to the desired device 
    Return None
    """
    global SSH
    print("Resetting router...")
    in_, out, error = SSH.exec_command("tc q")
    out = list(out)
    for item in out:
        if "qdisc netem" in item:
            print("Current netem conditions to be deleted: ", item)
            print("Deleting this condition... ")
            in_, out, error = SSH.exec_command(
                "tc qdisc del dev wlan-sta root")
    in_, out, error = SSH.exec_command(
        "tc qdisc add dev wlan-sta root netem loss 0%")
    error = list(error)
    if(len(error) > 0):
        log.debug("There was an error executing this command: {}".format(error))
        print("there has been an error: ", error)
    SSH.close()


# Internal Methods
def get_next_command():
    """Generate the next command in the command list
    Parameters None
    Returns None
    """
    global network_parameter_list
    for command in network_parameter_list:
        log.info("call to generator object")
        yield command


def get_command_generator():
    global network_generator
    if network_generator is None:
        log.info("command generator object not initialized, not initializing")
        network_generator = get_next_command()
    return network_generator


# okay to assume ms for everything?
def build_command(command):
    global device_type
    string_base = "tc qdisc add dev {} root netem ".format(device_type)
    loss_string=""
    delay_string=""
    if command["loss"]["type"]!=None:
        loss_string = "loss {} {} ".format(command["loss"]["type"], command["loss"]["value"])
    if command["delay"]["time"]!=None:
        delay_string = "delay {}ms".format(command["delay"]["time"])
        if command["delay"]["jitter"]!=None:
            delay_string = delay_string + " {}ms distribution {}".format(command["delay"]["distribution"], command["delay"]["jitter"])
    return string_base + loss_string + delay_string
 

# uh oh I used a magic word here! wlan-sta, should I pass it in or what!?
def execute_command(command):
    """Execute command on linux machine
    Parameters:
    ssh - object with SSH permission to machine
    condition - string of command to be executed
    Returns Bool: True=Command executed, no error
    False=Error, command not executed"""
    global SSH
    global device_type
    print(command)
    log.info("command: {}".format(command))
    in_, out, error = SSH.exec_command("tc qdisc del dev {} root".format(device_type))
    in_, out, error = SSH.exec_command(command)
    error = list(out)
    if(len(error) != 0):
        log.debug("There was an error executing this command: {}".format(error))
        print("There was an error executing this command: ", error)
    return in_, out, error


def nums_in_string(string):
    num_count=0
    try:
        for char in string:
            if char == " ":
                num_count = num_count + 1
        return num_count
    except TypeError:
        # the type was thus an int and there is only a single int
        return 1


def check_cfg():
    global login_info
    global network_parameter_list
    global device_type
    commands_to_remove=[]
    if (login_info["IP_Address"]==None) or (login_info["Username"]==None) or (login_info["Password"]==None):
        print("Please fill in the login information in router_config.yml. Now exiting...")
        sys.exit()
    for index, command in enumerate(network_parameter_list):
        # Don't execute if every value is none!
        if (command["loss"]["type"]==None) and (command["delay"]["time"]==None):
            commands_to_remove.append(index)
        # Confirm loss config is valid
        if (command["loss"]["type"]==None) and (command["loss"]["value"]!=None):
            print("A loss type was not specifed, please fill this field in the config. Exiting")
            sys.exit()
        if command["loss"]["type"]!=None:
            if (command["loss"]["type"]=="random"):
                if (nums_in_string(command["loss"]["value"]) > 1):
                    print("Uniform loss only takes a single number for input, please check this field in the config. Exiting")
                    sys.exit()
            elif (command["loss"]["type"]=="gemodel"):
                if nums_in_string(command["loss"]["value"]) > 4:
                    print("Gemodel loss takes 1 - 4 numbers as input, please check this field in the config file. Exiting")
                    sys.exit()
            else:
                print("Unrecognized loss type value, please check this field in the config file. Exiting")
                sys.exit()
        # Confirm delay config is valid
        if (command["delay"]["time"]==None) and (command["delay"]["distribution"]!=None):
            print("Jitter distribution was specified with a zero second delay, please check this field in the config file. Exiting")
            sys.exit()
        if command["delay"]["time"]!= None:
            if nums_in_string(command["delay"]["time"]) > 1:
                print("Too many numbers are specified in the jitter distribution field. Exiting")
                sys.exit()
            if command["delay"]["jitter"]!= None:
                if (command["delay"]["jitter"]!="paretonormal") and (command["delay"]["jitter"]!="normal") and (command["delay"]["jitter"]!="pareto"):
                    print("Invalid delay jitter type, please check this field in the config file. Exiting")
                    sys.exit()
                elif command["delay"]["distribution"]==None:
                    print("A jitter type was specified but no value was given, please check this field in the config. Exiting")
                    sys.exit()
                elif (command["delay"]["distribution"]!=None):
                    if nums_in_string(command["delay"]["distribution"]) > 1:
                        print("Too many numbers are specified in the jitter distribution field. Exiting")
                        sys.exit()
    # Remove the commands that were all null
    network_parameter_list = [network_parameter for index, network_parameter in enumerate(network_parameter_list) if index not in commands_to_remove]
        










