"""
Configuration module of cSpark test benchmark
"""

# AWS
DATA_AMI = {"eu-west-1": {"ami": 'ami-d3225da0',
                          "az": 'eu-west-1c',
                          "keypair": "giovanni2",
                          "price": "0.3"},
            "us-west-2": {"ami": 'ami-7f5ff81f',
                          "snapid": "snap-4f38bf1c",
                          "az": 'us-west-2c',
                          "keypair": "giovanni2",
                          "price": "0.3"}}
"""AMI id for region and availability zone"""

CREDENTIAL_PROFILE = 'cspark'
"""Credential profile name of AWS"""
REGION = "us-west-2"
"""Region of AWS to use"""
KEY_PAIR_PATH = "/Users/Giovanni/Desktop/" + DATA_AMI[REGION]["keypair"] + ".pem"
"""KeyPair path for the instance"""
SECURITY_GROUP = "spark-cluster"
"""Secutiry group of the instance"""
PRICE = DATA_AMI[REGION]["price"]
INSTANCE_TYPE = "r3.4xlarge"
"""Instance type"""
NUM_INSTANCE = 0
"""Number of instance to use"""
EBS_OPTIMIZED = True if "r3" not in INSTANCE_TYPE else False
REBOOT = 0
"""Reboot the instances of the cluster"""
KILL_JAVA = 1
"""Kill every java application on the cluster"""
NUM_RUN = 1
"""Number of run to repeat the benchmark"""

CLUSTER_ID = "CSPARK"
"""Id of the cluster with the launched instances"""
print("Cluster ID : " + str(CLUSTER_ID))
TAG = [{
    "Key": "ClusterId",
    "Value": CLUSTER_ID
}]

# HDFS
HDFS_MASTER = "ec2-35-161-111-116.us-west-2.compute.amazonaws.com"
"""Url of the HDFS NameNode if not set the cluster created is an HDFS Cluster"""
# Spark config
SPARK_2_HOME = "/opt/spark/"
C_SPARK_HOME = "/usr/local/spark/"
SPARK_HOME = C_SPARK_HOME
"""Location of Spark in the ami"""

LOG_LEVEL = "INFO"
UPDATE_SPARK = 0
"""Git pull and build Spark of all the cluster"""
UPDATE_SPARK_MASTER = 0
"""Git pull and build Spark only of the master node"""
UPDATE_SPARK_DOCKER = 0
"""Pull the docker image in each node of the cluster"""
ENABLE_EXTERNAL_SHUFFLE = "true"
LOCALITY_WAIT = 0
LOCALITY_WAIT_NODE = 0
LOCALITY_WAIT_PROCESS = 1
LOCALITY_WAIT_RACK = 0
CPU_TASK = 1
RAM_DRIVER = "50g"
RAM_EXEC = '"60g"' if "r3" not in INSTANCE_TYPE else '"100g"'
OFF_HEAP = False
if OFF_HEAP:
    RAM_EXEC = '"30g"' if "r3" not in INSTANCE_TYPE else '"70g"'
OFF_HEAP_BYTES = 30720000000

# Core Config
CORE_VM = 8
CORE_HT_VM = 16
DISABLE_HT = 1
if DISABLE_HT:
    CORE_HT_VM = CORE_VM

# CONTROL
ALPHA = 0.95
DEADLINE = 284375
# SVM
# 0%  217500
# 20% 261000
# 40% 304500
# KMeans
# 0%  166250
# 20% 199500
# 40% 232750
# PageRank
# 0%  209062
# 20% 250874
# 40% 284375
MAX_EXECUTOR = 9
OVER_SCALE = 2
K = 50
TI = 12000
T_SAMPLE = 1000
CORE_QUANTUM = 0.05
CORE_MIN = 0.0
CPU_PERIOD = 100000

# BENCHMARK
RUN = 1
SYNC_TIME = 1
PREV_SCALE_FACTOR = 1000
"""*Important Settings* if it is equals to SCALE_FACTOR no need to generate new data on HDFS"""
BENCH_NUM_TRIALS = 1

BENCHMARK_PERF = [
    # "scala-agg-by-key",
    # "scala-agg-by-key-int",
    # "scala-agg-by-key-naive",
    # "scala-sort-by-key",
    # "scala-sort-by-key-int",
    # "scala-count",
    # "scala-count-w-fltr",
]
"""Spark-perf benchmark to execute"""

BENCHMARK_BENCH = [
    "PageRank",
    # "DecisionTree",
    # "KMeans",
    # "SVM"
]
"""Spark-bench benchmark to execute"""

if len(BENCHMARK_PERF) + len(BENCHMARK_BENCH) > 1 or len(BENCHMARK_PERF) + len(
        BENCHMARK_BENCH) == 0:
    print("ERROR BENCHMARK SELECTION")
    exit(1)

# config: (line, value)
BENCH_CONF = {
    "scala-agg-by-key": {
        "ScaleFactor": 10
    },
    "scala-agg-by-key-int": {
        "ScaleFactor": 5
    },
    "scala-agg-by-key-naive": {
        "ScaleFactor": 10
    },
    "scala-sort-by-key": {
        "ScaleFactor": 100
    },
    "scala-sort-by-key-int": {
        "ScaleFactor": 50
    },
    "scala-count": {
        "ScaleFactor": 10
    },
    "scala-count-w-fltr": {
        "ScaleFactor": 10
    },
    "PageRank": {
        "NUM_OF_PARTITIONS": (3, 1000),
        "numV": (2, 2000000),
        "mu": (4, 5.0),
        "MAX_ITERATION": (8, 1)
    },
    "KMeans": {
        # DataGen
        "NUM_OF_POINTS": (2, 100000000),
        "NUM_OF_CLUSTERS": (3, 10),
        "DIMENSIONS": (4, 20),
        "SCALING": (5, 0.6),
        "NUM_OF_PARTITIONS": (6, 1000),
        # Run
        "MAX_ITERATION": (8, 1)
    },
    "DecisionTree": {
        "NUM_OF_PARTITIONS": (4, 1200),
        "NUM_OF_EXAMPLES": (2, 50000000),
        "NUM_OF_FEATURES": (3, 6),
        "NUM_OF_CLASS_C": (7, 10),
        "MAX_ITERATION": (21, 1)
    },
    "SVM": {
        "NUM_OF_PARTITIONS": (4, 1000),
        "NUM_OF_EXAMPLES": (2, 200000000),
        "NUM_OF_FEATURES": (3, 10),
        "MAX_ITERATION": (7, 1)
    }
}
"""Setting of the supported benchmark"""
if len(BENCHMARK_PERF) > 0:
    SCALE_FACTOR = BENCH_CONF[BENCHMARK_PERF[0]]["ScaleFactor"]
    INPUT_RECORD = 200 * 1000 * 1000 * SCALE_FACTOR
    NUM_TASK = SCALE_FACTOR
else:
    SCALE_FACTOR = BENCH_CONF[BENCHMARK_BENCH[0]]["NUM_OF_PARTITIONS"][1]
    NUM_TASK = SCALE_FACTOR
    try:
        INPUT_RECORD = BENCH_CONF[BENCHMARK_BENCH[0]]["NUM_OF_EXAMPLES"][1]
    except KeyError:
        try:
            INPUT_RECORD = BENCH_CONF[BENCHMARK_BENCH[0]]["NUM_OF_POINTS"][1]
        except KeyError:
            INPUT_RECORD = BENCH_CONF[BENCHMARK_BENCH[0]]["numV"][1]
BENCH_CONF[BENCHMARK_PERF[0] if len(BENCHMARK_PERF) > 0 else BENCHMARK_BENCH[0]][
    "NumTrials"] = BENCH_NUM_TRIALS

# Terminate istance after benchmark
TERMINATE = 0

# HDFS
HDFS = 1 if HDFS_MASTER == "" else 0  # TODO Fix this variable for plot
HADOOP_CONF = "/usr/local/lib/hadoop-2.7.2/etc/hadoop/"
DELETE_HDFS = 1 if SCALE_FACTOR != PREV_SCALE_FACTOR else 0

# CONFIG JSON
CONFIG_DICT = {
    "Benchmark": {
        "Name": BENCHMARK_PERF[0] if len(BENCHMARK_PERF) > 0 else BENCHMARK_BENCH[0],
        "Config": BENCH_CONF[BENCHMARK_PERF[0] if len(BENCHMARK_PERF) > 0 else BENCHMARK_BENCH[0]]
    },
    "Deadline": DEADLINE,
    "Control": {
        "Alpha": ALPHA,
        "OverScale": OVER_SCALE,
        "MaxExecutor": MAX_EXECUTOR,
        "CoreVM": CORE_VM,
        "K": K,
        "Ti": TI,
        "TSample": T_SAMPLE,
        "CoreQuantum": CORE_QUANTUM
    },
    "Aws": {
        "InstanceType": INSTANCE_TYPE,
        "HyperThreading": not DISABLE_HT,
        "Price": PRICE,
        "AMI": DATA_AMI[REGION]["ami"],
        "Region": REGION,
        "AZ": DATA_AMI[REGION]["az"],
        "SecurityGroup": SECURITY_GROUP,
        "KeyPair": DATA_AMI[REGION]["keypair"],
        "EbsOptimized": EBS_OPTIMIZED,
        "SnapshotId": DATA_AMI[REGION]["snapid"]
    },
    "Spark": {
        "ExecutorCore": CORE_VM,
        "ExecutorMemory": RAM_EXEC,
        "ExternalShuffle": ENABLE_EXTERNAL_SHUFFLE,
        "LocalityWait": LOCALITY_WAIT,
        "LocalityWaitProcess": LOCALITY_WAIT_PROCESS,
        "LocalityWaitNode": LOCALITY_WAIT_NODE,
        "LocalityWaitRack": LOCALITY_WAIT_RACK,
        "CPUTask": CPU_TASK,
        "SparkHome": SPARK_HOME
    },
    "HDFS": bool(HDFS)
}

# Line needed for enabling/disabling benchmark in spark-perf config.py
BENCH_LINES = {"scala-agg-by-key": ["226", "227"],
               "scala-agg-by-key-int": ["230", "231"],
               "scala-agg-by-key-naive": ["233", "234"],
               "scala-sort-by-key": ["237", "238"],
               "scala-sort-by-key-int": ["240", "241"],
               "scala-count": ["243", "244"],
               "scala-count-w-fltr": ["246", "247"]}
