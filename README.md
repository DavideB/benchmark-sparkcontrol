# Spark Control Benchmark

Spark Control Benchmark is a benchmarking suite specific for testing the perfomance of the planning controller in [cSpark](https://github.com/ElfoLiNk/spark).

The tool is composed by five principal component: **launch.py**, **run.py**, **log.py**, **plot.py**, **metrics.py** in addition to the configuration file **config.py**. The **launch.py** module manages the startup of the virtual machine instances on *Azure VM* and waits for the instance to be created and exposed to the internet. Subsequently the **run.py** module receives as input the instances on which to configure the cluster (*HDFS* or *Spark*), configures the benchmarks to be executed and waits for the benchmarks  to end. The module **log.py** downloads and saves the log produced by the benchmarks. The **plot.py** and **metrics.py** modules respectively generate graphs and calculate metrics.


## Microsoft Azure support implementation
Based on the *Apache Libcloud APIs*, the current version implements the first of the following two-step approach:
1) Implementation of an Azure-only version, exploiting to the maximum extent the usage of vendor-agnostic code provided by Libcloud.
2) Extend support to other Cloud Providers, like AWS, leveraging the vendor-agnostic core implementation, and developing Provider specific code only if strictly necessary.

The documentation of the API can be found [here](https://github.com/DavideB/benchmark-sparkcontrol).


## Download & Requirements
Checkout the "Azure-only" branch from: https://github.com/DavideB/benchmark-sparkcontrol

```bash
git clone https://github.com/DavideB/benchmark-sparkcontrol
cd benchmark-sparkcontrol
pip install -r requirements.txt
```

### Apache Libcloud and Microsoft Azure reference documentation 
- API Libcloud documentation @: https://libcloud.readthedocs.org/en/latest/
- Azure SDK for Python documentation @:  http://azure-sdk-for-python.readthedocs.io/en/latest/resourcemanagementcomputenetwork.html


## Azure VM Credentials
Open the credential file for Azure VM:

```bash
nano ~/.aws/credentials
```

and add the credential for cspark:

```nano
{ 
  "cspark":	{ "tenant_id": "< TENANT-ID >", 
			  "client_id": "< CLIENT-ID>", 
			  "application_id": "< APPLICATION-ID >", 
			  "secret": "< SECRET >", 
			  "subscription_id": "< SUBSCRIPTION >" }
}
```

## Configuration
See [config.py]https://github.com/DavideB/benchmark-sparkcontrol/config.html) 


## Example: Test PageRank
After addition of the Azure credentials to create a cluster with, open the file config.py and change these settings:

```python
AZURE_DATA_IMAGE = # The name of the KeyPair for the instance
KEY_PAIR_PATH = # The local path of the KeyPair 
NUM_INSTANCE = 7 # 1 NameNode + 6 DataNode
CLUSTER_ID = "HDFS" # We first create an HDFS cluster
```
After editing the config.py, launch the file main.py. After setup and launch of the HDFS cluster copy the HDFS Master dns address.

Now to launch PageRank on a new cSpark cluster setup the config.py file as follows:
```python
AZURE_DATA_IMAGE = # The name of the KeyPair for the instance
KEY_PAIR_PATH = # The local path of the KeyPair 
NUM_INSTANCE = 7 # 1 MasterNode + 6 WorkerNode
CLUSTER_ID = "CSPARK" # We first create an HDFS cluster
HDFS_MASTER = # The HDFS master dns address
PREV_SCALE_FACTOR = 0 # This is needed for generate new data
BENCHMARK_BENCH = ["PageRank"]
```

```
### TODO
- [ ] Add commandline parameters in main.py to override config.py
- [ ] Add support for AWS-EC2 back into the tool