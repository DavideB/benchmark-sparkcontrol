#import boto3
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

import log
import plot
from config import *

AzureDriver = get_driver(Provider.AZURE_ARM)
driver = AzureDriver(tenant_id = AZURE_TENANT_ID,
               subscription_id = AZURE_SUBSCRIPTION_ID, 
               key = AZURE_APPLICATION_ID, secret = AZURE_SECRET,
               region = AZURE_LOCATION)
    
nodes = driver.list_nodes()
instances = [n for n in nodes if n.state=="running" 
             and n.extra["tags"]["Key"]==TAG[0]["Key"] 
             and n.extra["tags"]["Value"]==TAG[0]["Value"]]

logfolder = "./spark-bench/num"
#master_dns = "ec2-35-165-203-239.us-west-2.compute.amazonaws.com"
master_dns ="40.71.187.234"
# master_dns = "ec2-54-70-77-95.us-west-2.compute.amazonaws.com"
output_folder = "./spark-bench/num/"
output_folder = log.download(logfolder, instances, master_dns, output_folder, CONFIG_DICT)

if output_folder[-1] != "/":
    output_folder += "/"

# PLOT LOGS
plot.plot(output_folder)
