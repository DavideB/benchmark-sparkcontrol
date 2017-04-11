"""
Handle the instance:
* Launch new instance with spot request
* Terminate instance
* Check instance connectivity
"""

import socket
import sys
import time

from errno import ECONNREFUSED
from errno import ETIMEDOUT
from libcloud.compute.base import NodeAuthSSHKey

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.
    :param question: is a string that is presented to the user.
    :param default:  is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).
    :return: The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def ping(host, port):
    """
    Ping the port of the host
    :param host: the host to ping
    :param port: the port of the host to ping
    :return: the port if the port is open or False if there is a connection error
    """

    try:
        socket.socket().connect((host, port))
        print(str(port) + " Open")
        return port
    except socket.error as err:
        if err.errno == ECONNREFUSED or err.errno == ETIMEDOUT:
            return False
        raise

def wait_ping(driver, instance_ips):
    """Wait that all the instance have open the ssh port (22)
    :param driver: the azure-arm driver
    :param instance_ips: ip of all the instance to ping
    :return: Exit when all the instance are reachable on port 22
    """
    while True:
        for ip in instance_ips:
            if ping(ip, 22) == 22:
                instance_ips.pop(instance_ips.index(ip))
                print("instance `{}` ping ok!".format(ip))
            else:
                print("wait_ping: pinging on `{}`".format(ip))
                time.sleep(2)
        if len(instance_ips) == 0:        
            print("wait_ping: all instances running!")
            return

def wait_for_running(driver, pending_nodes):
    """Wait until all the node instances are in RUNNING state
    :param driver: the azure-arm driver
    :param pending_nodes: list of started nodes to check until running
    :return: Exit when all the nodes are running
    """
    pending_node_names = [n.name for n in pending_nodes]
    print("Waiting for {} nodes to run:  {}".format(len(pending_node_names), pending_node_names))
    ret_running_nodes = []
    while True:
        nodes = driver.list_nodes()
        running_node_names = [n.name for n in nodes if n.state == "running"]
        just_running_node_names = list(set(pending_node_names) & set(running_node_names))
        for n in just_running_node_names:
            print("Node `{}` running!".format(n))
        pending_node_names = list(set(pending_node_names) - set(just_running_node_names))
        ret_running_nodes += [n for n in nodes if n.name in just_running_node_names]
        time.sleep(10)
        if len(pending_node_names) == 0:        
            print("all instances running!")
            return ret_running_nodes

def launch(driver, num_instances, config):
    """
    Launch num_instance on Azure VM with create request
    :param driver: the Azure arm driver
    :param num_instance: number of instance to launch
    :param config: the configuration dictionary of the user
    :return: the list of instances created
    """
    response = []
    if query_yes_no("Are you sure to launch " + str(num_instances) + " new instance?", "no"):
        name_prefix = config["Azure"]["NamePrefix"]
        dns_name_prefix = config["Azure"]["DNSNamePrefix"]
        size = [x for x in driver.list_sizes() if x.id == config["Azure"]["Size"]][0]            
        image = driver.get_image(config["Azure"]["ImageId"], location=None)
        ex_user_name = config["Azure"]["UserName"]
        auth = NodeAuthSSHKey(config["Azure"]["Auth"]) 
        ex_resource_group = config["Azure"]["ResourceGroup"]
        ex_storage_account = config["Azure"]["StorageAccount"]
        ex_network = config["Azure"]["Network"]
        #location = NodeLocation()         
        names = [x.name for x in driver.list_nodes()]
        suffix = 0
        for _ in range(num_instances):
            while name_prefix + str(suffix) in names: 
                suffix += 1
            vmName = name_prefix + str(suffix)
            dns_name = dns_name_prefix + str(suffix)
            network = [x for x in driver.ex_list_networks() if x.name == config["Azure"]["Network"]][0]
            subnet = [x for x in driver.ex_list_subnets(network) if x.name == config["Azure"]["Subnet"]][0]
            public_ip = driver.ex_create_public_ip(vmName + "-ip", ex_resource_group)
            #public_ip.extra = {'dnsSettings': {'domainNameLabel': dns_name}}
            ex_nic = driver.ex_create_network_interface(vmName + "-nic", 
                                                        subnet, 
                                                        ex_resource_group, 
                                                        location=None, 
                                                        public_ip=public_ip) 
            response.append(driver.create_node(vmName, 
                                               size, 
                                               image, 
                                               auth, 
                                               ex_resource_group, 
                                               ex_storage_account=ex_storage_account, 
                                               ex_user_name=ex_user_name, 
                                               ex_network=ex_network, 
                                               ex_nic=ex_nic))
            suffix += 1
   
    return response
    