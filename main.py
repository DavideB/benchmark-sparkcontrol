import launch
import run

from config import NUM_INSTANCE, TAG, REBOOT, TERMINATE, RUN, NUM_RUN, \
    CONFIG_DICT, AZURE_TENANT_ID, AZURE_SECRET, AZURE_SUBSCRIPTION_ID, \
    AZURE_LOCATION, AZURE_APPLICATION_ID
   
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver

def main():
    """ Main function;
    * Launch spot request of NUMINSTANCE
    * Run Benchmark
    * Download Log
    * Plot data from log
    """
 
    AzureDriver = get_driver(Provider.AZURE_ARM)
    
    driver = AzureDriver(tenant_id = AZURE_TENANT_ID,
               subscription_id = AZURE_SUBSCRIPTION_ID, 
               key = AZURE_APPLICATION_ID, secret = AZURE_SECRET,
               region = AZURE_LOCATION)
    nodes = driver.list_nodes()
    
    if NUM_INSTANCE > 0:
        nodes = driver.list_nodes()
        stopped_nodes = [n for n in nodes if n.state=="stopped"]
        num_inst = NUM_INSTANCE
        nodes_to_start =[]
        pending_nodes = []       
        if  len(stopped_nodes) < NUM_INSTANCE:
            print("Existing capacity exceeded") 
            if len(stopped_nodes) > 0:
                print("Running stopped instance(s)")
                nodes_to_start = stopped_nodes 
        else:
            print("Existing pool has capacity - Running stopped instance(s)")          
            nodes_to_start = stopped_nodes[:num_inst]
        
        num_inst -= len(nodes_to_start)
          
        for n in nodes_to_start:
            print("Starting instance:"+str(n.name))
            driver.ex_start_node(n)
            print("Instances started")
            pending_nodes.append(n)
        
        if num_inst > 0:        
            print("Creating node(s)")        
            created_nodes = launch.launch(driver, num_inst, CONFIG_DICT)
            print("Nodes created and started")
            pending_nodes += created_nodes
        
        print("Creating Tags")
        for n in pending_nodes:
            driver.ex_create_tags(n, TAG[0], replace=True)    
        print("Tags created")
        
        print("CHECK SECURITY GROUP ALLOWED IP SETTINGS!!!")

        # Wait Running
        running_nodes = launch.wait_for_running(driver, pending_nodes)
        instance_ips = [x.public_ips[0] for x in running_nodes]
        launch.wait_ping(driver, instance_ips)
        
    
    if REBOOT:
        print("Rebooting instances...")
        nodes = driver.list_nodes()
        nodes_to_reboot = [n for n in nodes if n.state=="running" 
             and n.extra["tags"]["Key"]==TAG[0]["Key"] 
             and n.extra["tags"]["Value"]==TAG[0]["Value"]]
       
        nodes_rebooted = [n for n in nodes_to_reboot if driver.reboot_node(n)]
        nodes_rebooted_names = [n.name for n in nodes_rebooted]
       
        if len(set(nodes_to_reboot) - set(nodes_rebooted)) == 0:
            print("All nodes successfully rebooted!")
        else: 
            print("WARNING: reboot FAILED for one or more nodes!")
        
        print("Rebooted nodes: {}".format(nodes_rebooted_names))
        
        instance_ips = [x.public_ips[0] for x in nodes_rebooted]
        launch.wait_ping(driver, instance_ips)

    
    if RUN:
        for i in range(NUM_RUN):
            print("{}{}{}{}".format("benchmark run #: ", i+1, " of ", NUM_RUN))
            run.run_benchmark()
            
    if TERMINATE:
        print("Terminating instances...")
        nodes = driver.list_nodes()
        nodes_to_terminate = [n for n in nodes if n.state=="running" 
             and n.extra["tags"]["Key"]==TAG[0]["Key"] 
             and n.extra["tags"]["Value"]==TAG[0]["Value"]]
        
        nodes_terminated = [n for n in nodes_to_terminate if driver.destroy_node(n, 
                                                                              ex_destroy_nic=True, 
                                                                              ex_destroy_vhd=True)]
        nodes_terminated_names = [n.name for n in nodes_terminated]
       
        if len(set(nodes_to_terminate) - set(nodes_terminated)) == 0:
            print("All nodes successfully terminated!")
        else: 
            print("WARNING: terminate FAILED for one or more nodes!")
            
        print("Terminated nodes: {}".format(nodes_terminated_names))  
        
          
if __name__ == "__main__":
    main()