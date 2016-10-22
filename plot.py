import glob
from datetime import datetime as dt
from datetime import timedelta

import matplotlib.dates as mpdate
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import random
import time
import math

from config import *

STRPTIME_FORMAT = '%H:%M:%S'
SECONDLOCATOR = 10
TITLE = True


def timing(f):
    def wrap(*args):
        tstart = time.time()
        ret = f(*args)
        tend = time.time()
        print('\n%s function took %0.3f ms' % (f.__name__, (tend - tstart) * 1000.0))
        return ret

    return wrap


@timing
def plot(folder):
    # COREVM = 12
    # COREHTVM = 12
    # DEADLINE = 82800
    # SCALE_FACTOR = 0.1
    # K = 50
    # TSAMPLE = 500
    # STRPTIME_FORMAT = '%H:%M:%S,%f'
    benchLog = glob.glob(folder + "*.err") + glob.glob(folder + "*.dat")
    plotDICT = {}
    appIDinfo = {}
    for bench in sorted(benchLog):
        # 16/08/30 21:45:51 INFO ControllerJob: SEND INIT TO EXECUTOR CONTROLLER EID 0, SID 2, TASK 150, DL 81322, C 12
        # 16/08/30 21:46:13 INFO DAGScheduler: ResultStage 2 (count at KVDataTest.scala:151) finished in 22.195 s
        # 16/08/31 14:30:28 INFO ControllerJob: SEND NEEDED CORE TO MASTER spark://ec2-52-42-181-165.us-west-2.compute.amazonaws.com:7077, 0, Vector(4, 4, 4, 4), app-20160831142852-0000
        # 16/09/11 12:39:19,930 INFO DAGScheduler: Submitting 60 missing tasks from ResultStage 0 (GraphLoader.edgeListFile - edges (hdfs://10.8.0.1:9000/SparkBench/PageRank/Input) MapPartitionsRDD[3] at mapPartitionsWithIndex at GraphLoader.scala:75)
        # 16/09/11 12:41:13,537 INFO TaskSetManager: Finished task 10.0 in stage 1.0 (TID 78) in 1604 ms on 131.175.135.183 (1/60)
        appID = ""
        with open(bench) as applog:
            SID = -1 if HDFS else 0
            for line in applog:
                l = line.split(" ")
                # 16/09/11 12:39:18,070 INFO StandaloneSchedulerBackend: Connected to Spark cluster with app ID app-20160911123918-0002
                if len(l) > 3 and l[3] == "TaskSetManager:" and l[4] == "Finished":
                    try:
                        appIDinfo[appID][int(float(l[9]))]["tasktimestamps"].append(
                            dt.strptime(l[1], STRPTIME_FORMAT).replace(year=2016))
                    except KeyError:
                        appIDinfo[appID][int(float(l[9]))]["tasktimestamps"] = []
                        appIDinfo[appID][int(float(l[9]))]["tasktimestamps"].append(
                            dt.strptime(l[1], STRPTIME_FORMAT).replace(year=2016))
                if len(l) > 3 and l[3] == "StandaloneSchedulerBackend:" and l[4] == "Connected":
                    appIDinfo[l[-1].rstrip()] = {}
                    appID = l[-1].rstrip()
                    plotDICT[appID] = {}
                    plotDICT[appID]["dealineTimeStages"] = []
                    plotDICT[appID]["startTimeStages"] = []
                    plotDICT[appID]["finishTimeStages"] = []
                elif len(l) > 12 and l[3] == "ControllerJob:":
                    if l[5] == "INIT":
                        if SID != int(l[12].replace(",", "")) or int(l[12].replace(",", "")) == 0:
                            SID = int(l[12].replace(",", ""))
                            appIDinfo[appID][SID]["start"] = dt.strptime(l[1], STRPTIME_FORMAT).replace(year=2016)
                            plotDICT[appID]["startTimeStages"].append(appIDinfo[appID][SID]["start"])
                            print("START: " + str(dt.strptime(l[1], STRPTIME_FORMAT).replace(year=2016)))
                            print(l[16].replace(",", ""))
                            appIDinfo[appID][SID]["deadline"] = plotDICT[appID]["startTimeStages"][-1] + timedelta(
                            milliseconds=float(l[16].replace(",", "")))
                            plotDICT[appID]["dealineTimeStages"].append(appIDinfo[appID][SID]["deadline"])
                    if l[5] == "NEEDED" and l[4] == "SEND":
                        nextAppID = l[-1].replace("\n", "")
                        if appID != nextAppID:
                            appID = nextAppID
                            plotDICT[appID] = {}
                            plotDICT[appID]["dealineTimeStages"] = []
                            plotDICT[appID]["startTimeStages"] = []
                            plotDICT[appID]["finishTimeStages"] = []
                elif len(l) > 3 and l[3] == "DAGScheduler:":
                    if l[4] == "Submitting" and l[6] == "missing":
                        appIDinfo[appID][int(l[10])] = {}
                        appIDinfo[appID][int(l[10])]["tasks"] = int(l[5])
                        appIDinfo[appID][int(l[10])]["start"] = dt.strptime(l[1], STRPTIME_FORMAT).replace(
                            year=2016)
                    elif l[-4] == "finished":
                        if appID != "":
                            SID = int(l[5])
                            appIDinfo[appID][SID]["end"] = dt.strptime(l[1], STRPTIME_FORMAT).replace(
                                year=2016)
                            if len(plotDICT[appID]["startTimeStages"]) > len(plotDICT[appID]["finishTimeStages"]):
                                plotDICT[appID]["finishTimeStages"].append(appIDinfo[appID][SID]["end"])
                                print("END: " + str(appIDinfo[appID][SID]["end"]))

                elif len(l) > 10 and l[5] == "added:" and l[4] == "Executor":
                    None
                    # 16/08/31 14:28:52 INFO StandaloneAppClient$ClientEndpoint: Executor added: app-20160831142852-0000/0 on worker-20160831142832-ec2-52-43-162-151.us-west-2.compute.amazonaws.com-9999 (ec2-52-43-162-151.us-west-2.compute.amazonaws.com:9999) with 8 cores
                    # COREHTVM = int(l[-2])

                    # print(plotDICT.keys())
    # print(appIDinfo)
    for app in appIDinfo.keys():
        if len(appIDinfo[app]) > 0:
            x = []
            y = []
            colors_stage = colors.cnames
            deadlineapp = 0
            for sid in sorted(appIDinfo[app].keys()):
                try:
                    deadlineapp = appIDinfo[app][DELETE_HDFS]["start"] + timedelta(milliseconds=DEADLINE)
                    for timestamp in appIDinfo[app][sid]["tasktimestamps"]:
                        x.append(timestamp)
                        if len(y) == 0:
                            y.append(1)
                        else:
                            y.append(y[-1] + 1)
                except KeyError:
                    None

            fig, ax1 = plt.subplots(figsize=(16, 9), dpi=300)
            normalized = [(z - min(y)) / (max(y) - min(y)) for z in y]
            taskprogress, = ax1.plot(x, normalized, ".k-")
            ymin, ymax = ax1.get_ylim()
            ax1.axvline(deadlineapp)
            ax1.text(deadlineapp, ymax, 'DEADLINE APP', rotation=90)
            deadlineAlphaApp = deadlineapp - timedelta(milliseconds=((1 - ALPHA) * DEADLINE))
            ax1.axvline(deadlineAlphaApp)
            ax1.text(deadlineAlphaApp, ymax, 'ALPHA DEADLINE', rotation=90)
            ax1.set_xlabel('time')
            ax1.set_ylabel('app progress')
            errors = []
            for sid in sorted(appIDinfo[app].keys()):
                # color = colors_stage.popitem()[1]
                int_dead = 0
                try:
                    ax1.axvline(appIDinfo[app][sid]["deadline"], color="r", linestyle='--')
                    ax1.text(appIDinfo[app][sid]["deadline"], ymin + 0.15 * ymax, 'DEAD SID ' + str(sid), rotation=90)
                    int_dead = appIDinfo[app][sid]["deadline"].timestamp()
                    # if sid != 0:
                    ax1.axvline(appIDinfo[app][sid]["start"], color="b")
                    ax1.text(appIDinfo[app][sid]["start"], ymax - 0.02 * ymax, 'START SID ' + str(sid), rotation=90, )
                    ax1.axvline(appIDinfo[app][sid]["end"], color="r")
                    ax1.text(appIDinfo[app][sid]["end"], ymax - 0.25 * ymax, 'END SID ' + str(sid), rotation=90)
                    #if int_dead != 0 and sid != DELETE_HDFS:
                    end = appIDinfo[app][sid]["end"].timestamp()
                    duration = deadlineAlphaApp.timestamp() - appIDinfo[app][DELETE_HDFS]["start"].timestamp()
                    error = round(round(((abs(int_dead - end)) / duration), 3) * 100, 3)
                    errors.append(error)
                    ax1.text(appIDinfo[app][sid]["end"], ymax - random.uniform(0.4, 0.5) * ymax,
                             "E " + str(error) + "%", rotation=90)
                except KeyError:
                    None

            try:
                end = appIDinfo[app][sorted(appIDinfo[app].keys())[-1]]["end"].timestamp()
            except KeyError:
                None
            int_dead = deadlineAlphaApp.timestamp()
            duration = int_dead - appIDinfo[app][DELETE_HDFS]["start"].timestamp()
            error = round(round(((int_dead - end) / duration), 3) * 100, 3)
            ax1.text(deadlineAlphaApp, ymax - 0.5 * ymax, "ERROR = " + str(error) + "%")

            np_errors = np.array(errors)
            print("DEADLINE_ERROR " + str(abs(error)))
            if len(np_errors) > 0:
                print("MEAN ERROR: " + str(np.mean(np_errors)))
                print("DEVSTD ERROR: " + str(np.std(np_errors)))
                print("MEDIAN ERROR: " + str(np.median(np_errors)))
                print("MAX ERROR: " + str(max(np_errors)))
                print("MIN ERROR: " + str(min(np_errors)))

            with open(folder + "ERROR.txt", "w") as error_f:
                error_f.write("DEADLINE_ERROR " + str(abs(error)) + "\n")
                if len(np_errors) > 0:
                    error_f.write("MEAN_ERROR " + str(np.mean(np_errors)) + "\n")
                    error_f.write("DEVSTD_ERROR: " + str(np.std(np_errors)) + "\n")
                    error_f.write("MEDIAN_ERROR: " + str(np.median(np_errors)) + "\n")
                    error_f.write("MAX_ERROR: " + str(max(np_errors)) + "\n")
                    error_f.write("MIN_ERROR: " + str(min(np_errors)) + "\n")

            labels = ax1.get_xticklabels()
            plt.setp(labels, rotation=90)
            locator = mpdate.SecondLocator(interval=SECONDLOCATOR)
            plt.gca().xaxis.set_major_locator(locator)
            plt.gca().xaxis.set_major_formatter(mpdate.DateFormatter(STRPTIME_FORMAT))
            plt.gcf().autofmt_xdate()
            if TITLE:
                plt.title(app + " " + str(SCALE_FACTOR) + " " + str(DEADLINE) + " " + str(TSAMPLE) + " " + str(   ALPHA) + " " + str(K))
            plt.savefig(folder + app + ".png", bbox_inches='tight', dpi=300)
            plt.close()

    workerLog = glob.glob(folder + "*worker*.out")
    sarLog = glob.glob(folder + "sar*.log")

    # Check len log
    print(len(workerLog), len(sarLog))

    if len(workerLog) == len(sarLog):
        for w, s in zip(sorted(workerLog), sorted(sarLog)):
            print(w)
            print(s)
            # 16/08/31 14:29:43 INFO Worker: Scaled executorId 2  of appId app-20160831142852-0000 to  8 Core
            # 16/09/11 17:37:18,062 INFO Worker: Created ControllerExecutor: 0 , 1 , 16000 , 30 , 6
            with open(w) as wlog:
                appID = ""
                plotDICT[w] = {}
                plotDICT[w]["cpu_real"] = []
                plotDICT[w]["time_cpu"] = []
                for line in wlog:
                    l = line.split(" ")
                    if len(l) > 3:
                        if l[4] == "Created" and appID != "":
                            plotDICT[appID][w]["cpu"].append(float(l[-1].replace("\n", "")))
                            plotDICT[appID][w]["sp_real"].append(0.0)
                            plotDICT[appID][w]["time"].append(
                                dt.strptime(l[1], STRPTIME_FORMAT).replace(year=2016))
                            plotDICT[appID][w]["sp"].append(0.0)
                        if l[4] == "Scaled":
                            # print(l)
                            if appID == "" or appID != l[10]:
                                nextAppID = l[10]
                                try:
                                    plotDICT[nextAppID][w] = {}
                                    plotDICT[nextAppID][w]["cpu"] = []
                                    plotDICT[nextAppID][w]["time"] = []
                                    plotDICT[nextAppID][w]["sp_real"] = []
                                    plotDICT[nextAppID][w]["sp"] = []
                                    appID = nextAppID
                                except KeyError:
                                    None
                                    # print(nextAppID + " NOT FOUND BEFORE IN BENCHMARK LOGS")
                        if appID != "":
                            if l[4] == "CoreToAllocate:":
                                # print(l)
                                plotDICT[appID][w]["cpu"].append(float(l[-1].replace("\n", "")))
                            if l[4] == "Real:":
                                plotDICT[appID][w]["sp_real"].append(float(l[-1].replace("\n", "")))
                            if l[4] == "SP":
                                plotDICT[appID][w]["time"].append(
                                    dt.strptime(l[1], STRPTIME_FORMAT).replace(year=2016))
                                # print(l[-1].replace("\n", ""))
                                sp = float(l[-1].replace("\n", ""))
                                # print(sp)
                                if sp < 0.0:
                                    plotDICT[appID][w]["sp"].append(abs(sp) / 100)
                                else:
                                    plotDICT[appID][w]["sp"].append(sp)

            with open(s) as cpulog:
                for line in cpulog:
                    l = line.split("    ")
                    if not ("Linux" in l[0].split(" ") or "\n" in l[0].split(" ")) and l[1] != " CPU" and l[
                        0] != "Average:":
                        plotDICT[w]["time_cpu"].append(
                            dt.strptime(l[0], '%I:%M:%S %p').replace(year=2016))
                        cpuint = float('{0:.2f}'.format((float(l[2]) * COREHTVM) / 100))
                        plotDICT[w]["cpu_real"].append(cpuint)
    else:
        print("ERROR: SAR != WORKER LOGS")

    for appID in sorted(plotDICT.keys()):
        if len(appID) <= len("app-20160831142852-0000"):
            cpu_time = 0
            cpu_time_max = 0
            for worker in plotDICT[appID].keys():
                if worker not in ["startTimeStages", "dealineTimeStages", "finishTimeStages"]:
                    cpu_time += (TSAMPLE / 1000) * sum(plotDICT[appID][worker]["cpu"])
                    for c, t in zip(plotDICT[appID][worker]["cpu"], plotDICT[appID][worker]["time"]):
                        try:
                            index = plotDICT[worker]["time_cpu"].index(t)
                        except ValueError:
                            def func(x):
                                delta = x - t if x > t else timedelta.max
                                return delta

                            index = plotDICT[worker]["time_cpu"].index(min(plotDICT[worker]["time_cpu"], key=func))
                        cpu_time_max += (TSAMPLE / 1000) * max(c, plotDICT[worker]["cpu_real"][index + int(TSAMPLE / 1000)])

            if cpu_time == 0:
                cpu_time = ((appIDinfo[appID][max(list(appIDinfo[appID].keys()))]["end"].timestamp() - appIDinfo[appID][0]["start"].timestamp())) * MAXEXECUTOR * COREVM
                cpu_time_max = cpu_time
            cpu_time_max = math.floor(cpu_time_max)
            print("CPU_TIME: " + str(cpu_time))
            print("CPU TIME MAX: " + str(cpu_time_max))
            print("SID " + str(appIDinfo[appID].keys()))
            print("CHECK NON CONTROLLED STAGE FOR CPU_TIME")

    with open(folder + "CPU_TIME.txt", "w") as cpu_time_f:
        if plotDICT:
            cpu_time_f.write("CPU_TIME " + str(cpu_time) + "\n")
            cpu_time_f.write("CPU_TIME_MAX " + str(cpu_time_max) + "\n")

    # print(plotDICT)
    for appID in sorted(plotDICT.keys()):
        if len(appID) <= len("app-20160831142852-0000"):
            for worker in plotDICT[appID].keys():
                colors_stage = {'m', 'y', 'k', 'c', 'g'}
                colors2_stage = colors_stage.copy()
                if worker not in ["startTimeStages", "dealineTimeStages", "finishTimeStages"] and len(
                        plotDICT[appID][worker]["sp"]) > 0:
                    # print(appID, worker)
                    fig, ax1 = plt.subplots(figsize=(16, 9), dpi=300)
                    # pos = np.where(np.abs(np.diff(plotDICT[appID][worker]["time"])) >= timedelta(
                    #         milliseconds=TSAMPLE*2))[0] + 1
                    # print(pos)
                    # if pos != []:
                    #     for p in pos:
                    #         plotDICT[appID][worker]["time"] = np.insert(plotDICT[appID][worker]["time"], p, plotDICT[appID][worker]["time"][p-1])
                    #         plotDICT[appID][worker]["sp"] = np.insert(plotDICT[appID][worker]["sp"], p, 0)
                    #         plotDICT[appID][worker]["sp_real"] = np.insert(plotDICT[appID][worker]["sp_real"], p, 0)
                    #         plotDICT[appID][worker]["cpu"] = np.insert(plotDICT[appID][worker]["cpu"], p, 0)
                    if len(plotDICT[appID][worker]["sp"]) > 0:
                        sp_plt, = ax1.plot(plotDICT[appID][worker]["time"], plotDICT[appID][worker]["sp"], ".r-",
                                           label='PROGRESS')
                    if len(plotDICT[appID][worker]["sp_real"]) > 0:
                        sp_real_plt, = ax1.plot(plotDICT[appID][worker]["time"], plotDICT[appID][worker]["sp_real"],
                                                ".k-",
                                                label='PROGRESS REAL')
                    ax1.set_xlabel('time')
                    ax1.set_ylabel('stage progress')

                    for starttime, finishtime in zip(plotDICT[appID]["startTimeStages"],
                                                     plotDICT[appID]["finishTimeStages"]):
                        try:
                            c = colors_stage.pop()
                        except KeyError:
                            colors_stage = {'m', 'y', 'k', 'c', 'g'}
                            try:
                                c = colors2_stage.pop()
                            except KeyError:
                                colors2_stage = {'m', 'y', 'k', 'c', 'g'}
                                c = colors_stage.pop()

                        ax1.axvline(starttime, color=c, linestyle='--')
                        ax1.axvline(finishtime, color=c)
                    for deadline in plotDICT[appID]["dealineTimeStages"]:
                        ax1.axvline(deadline, color="red", linestyle='--')

                    ax1.spines["top"].set_visible(False)
                    ax1.spines["right"].set_visible(False)

                    ax1.get_xaxis().tick_bottom()
                    ax1.get_yaxis().tick_left()

                    xlim = ax1.get_xlim()
                    factor = 0.1
                    new_xlim = (xlim[0] + xlim[1]) / 2 + np.array((-0.5, 0.5)) * (xlim[1] - xlim[0]) * (1 + factor)
                    ax1.set_xlim(new_xlim)

                    ylim = ax1.get_ylim()
                    factor = 0.1
                    new_ylim = (ylim[0] + ylim[1]) / 2 + np.array((-0.5, 0.5)) * (ylim[1] - ylim[0]) * (1 + factor)
                    ax1.set_ylim(new_ylim)

                    ax2 = ax1.twinx()
                    cpu_plt, = ax2.plot(plotDICT[appID][worker]["time"], plotDICT[appID][worker]["cpu"], ".b-",
                                        label='CPU')
                    if len(plotDICT[worker]["cpu_real"]) > 0:
                        b_d = plotDICT[appID][worker]["time"][0]

                        def func(x):
                            delta = x - b_d if x > b_d else timedelta.max
                            return delta

                        indexInit = plotDICT[worker]["time_cpu"].index(min(plotDICT[worker]["time_cpu"], key=func))
                        b_d = plotDICT[appID][worker]["time"][-1]
                        indexEnd = plotDICT[worker]["time_cpu"].index(min(plotDICT[worker]["time_cpu"], key=func))
                        print(indexInit, indexEnd)
                        cpu_real, = ax2.plot(plotDICT[worker]["time_cpu"][indexInit:indexEnd + 1],
                                             plotDICT[worker]["cpu_real"][indexInit:indexEnd + 1], ".g-",
                                             label='CPU REAL')
                        #plt.legend(handles=[sp_plt, sp_real_plt, cpu_plt, cpu_real], bbox_to_anchor=(1, 0.2), prop={'size': 12})
                        plt.legend(handles=[sp_plt, sp_real_plt, cpu_plt, cpu_real], loc='best', prop={'size': 12})
                    else:
                        plt.legend(handles=[sp_plt, sp_real_plt, cpu_plt], bbox_to_anchor=(1, 0.15), prop={'size': 12})

                    ax2.set_ylabel('cpu')
                    ax2.set_ylim(0, COREVM)
                    labels = ax1.get_xticklabels()
                    plt.setp(labels, rotation=90, fontsize=10)
                    xlim = ax2.get_xlim()
                    # example of how to zoomout by a factor of 0.1
                    factor = 0.1
                    new_xlim = (xlim[0] + xlim[1]) / 2 + np.array((-0.5, 0.5)) * (xlim[1] - xlim[0]) * (1 + factor)
                    ax2.set_xlim(new_xlim)
                    ylim = ax2.get_ylim()
                    factor = 0.1
                    new_ylim = (ylim[0] + ylim[1]) / 2 + np.array((-0.5, 0.5)) * (ylim[1] - ylim[0]) * (1 + factor)
                    ax2.set_ylim(new_ylim)
                    locator = mpdate.SecondLocator(interval=SECONDLOCATOR)
                    plt.gca().xaxis.set_major_locator(locator)
                    plt.gca().xaxis.set_major_formatter(mpdate.DateFormatter(STRPTIME_FORMAT))
                    plt.gcf().autofmt_xdate()
                    # print(worker)
                    # for starttime, finishtime in zip(plotDICT[appID]["startTimeStages"],
                    #                                  plotDICT[appID]["finishTimeStages"]):
                    #
                    #     b_d = starttime
                    #
                    #     def func(x):
                    #         delta = x - b_d if x > b_d else timedelta.max
                    #         return delta
                    #
                    #     indexStart = plotDICT[appID][worker]["time"].index(
                    #         min(plotDICT[appID][worker]["time"], key=func))
                    #
                    #     if starttime < plotDICT[appID][worker]["time"][indexStart] and plotDICT[appID][worker]["time"][indexStart] - starttime <= timedelta(seconds=10):
                    #         print("START", starttime, plotDICT[appID][worker]["time"][indexStart])
                    #         b_d = finishtime
                    #         indexFinish = plotDICT[appID][worker]["time"].index(
                    #             min(plotDICT[appID][worker]["time"], key=func))
                    #         print("END", finishtime, plotDICT[appID][worker]["time"][indexFinish -1])
                    #         if plotDICT[appID][worker]["time"][indexFinish - 1] - finishtime <= timedelta(seconds=10):
                    #             print("END OK", finishtime, plotDICT[appID][worker]["time"][indexFinish -1])
                    #             b_d = starttime
                    #             indexInit = plotDICT[worker]["time_cpu"].index(min(plotDICT[worker]["time_cpu"], key=func))
                    #             b_d = finishtime
                    #             indexEnd = plotDICT[worker]["time_cpu"].index(min(plotDICT[worker]["time_cpu"], key=func))
                    #             if indexFinish == 0:
                    #                 indexFinish = len(plotDICT[appID][worker]["cpu"])
                    #             mean_cpu = np.mean(plotDICT[appID][worker]["cpu"][indexStart:indexFinish -1])
                    #             mean_cpu_real = np.mean(plotDICT[worker]["cpu_real"][indexInit:indexEnd])
                    #
                    #             xmin = float(indexStart) / len(plotDICT[appID][worker]["time"])
                    #             xmax = float(indexFinish - 1) / len(plotDICT[appID][worker]["time"])
                    #             xmin = xmin + 0.1
                    #             xmax = xmax + 0.1
                    #             if xmax == 0.0 or xmax >= 0.9:
                    #                 xmax = 0.9
                    #             print(mean_cpu, mean_cpu_real, xmin, xmax)
                    #             ax2.axhline(y=mean_cpu, xmin=xmin, xmax=xmax, c="blue", linewidth=2)
                    #             ax2.axhline(y=mean_cpu_real, xmin=xmin, xmax=xmax, c="green", linewidth=2)
                    if TITLE:
                        plt.title(appID + " " + str(SCALE_FACTOR) + " " + str(DEADLINE) + " " + str(TSAMPLE) + " " + str(ALPHA) + " " + str(K))
                    plt.savefig(worker + "." + appID + '.png', bbox_inches='tight', dpi=300)
                    plt.close()
        else:
            worker = appID
            colors_stage = {'m', 'y', 'k', 'c', 'g'}
            colors2_stage = colors_stage.copy()

            fig, ax1 = plt.subplots(figsize=(16, 9), dpi=300)

            ax1.set_xlabel('time')
            ax1.set_ylabel('cpu')

            ax1.spines["top"].set_visible(False)
            ax1.spines["right"].set_visible(False)

            ax1.get_xaxis().tick_bottom()
            ax1.get_yaxis().tick_left()

            ax2 = ax1.twinx()

            if len(plotDICT[worker]["cpu_real"]) > 0:
                cpu_real, = ax2.plot(plotDICT[worker]["time_cpu"],
                                     plotDICT[worker]["cpu_real"], ".g-",
                                     label='CPU REAL')
                plt.legend(handles=[cpu_real], bbox_to_anchor=(1.1, -0.025))

            ax2.set_ylabel('cpu')
            ax2.set_ylim(0, COREVM)
            labels = ax1.get_xticklabels()
            plt.setp(labels, rotation=90, fontsize=10)
            xlim = ax2.get_xlim()
            # example of how to zoomout by a factor of 0.1
            factor = 0.1
            new_xlim = (xlim[0] + xlim[1]) / 2 + np.array((-0.5, 0.5)) * (xlim[1] - xlim[0]) * (1 + factor)
            ax2.set_xlim(new_xlim)
            ylim = ax2.get_ylim()
            factor = 0.1
            new_ylim = (ylim[0] + ylim[1]) / 2 + np.array((-0.5, 0.5)) * (ylim[1] - ylim[0]) * (1 + factor)
            ax2.set_ylim(new_ylim)
            # plt.title(appID + " " + str(SCALE_FACTOR) + " " + str(DEADLINE) + " " + str(TSAMPLE) + " " + str(
            #   ALPHA) + " " + str(K))
            import matplotlib.dates as mdate
            locator = mdate.SecondLocator(interval=SECONDLOCATOR)
            plt.gca().xaxis.set_major_locator(locator)

            plt.gcf().autofmt_xdate()
            # plt.savefig(worker + '.png', bbox_inches='tight', dpi=300)
            plt.close()
