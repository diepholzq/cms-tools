#!/usr/bin/env python3.8

from ROOT import *
from glob import glob
from sys import exit
import argparse
import sys
import numpy as np
import os
import cppyy
import itertools
from datetime import datetime

sys.path.append(os.path.expandvars("$CMSSW_BASE/src/cms-tools"))
sys.path.append(os.path.expandvars("$CMSSW_BASE/src/cms-tools/lib/classes"))
from lib import analysis_ntuples
from lib import analysis_tools
from lib import utils
from lib import analysis_observables

parser = argparse.ArgumentParser(description='Add observables to trees.')
parser.add_argument('-phase1', '--phase1', dest='phase1', help='Phase 1', action='store_true')
parser.add_argument('-phase1_2018', '--phase1_2018', dest='phase1_2018', help='Phase 1 2018', action='store_true')
args = parser.parse_args()

phase1 = args.phase1
phase1_2018 = args.phase1_2018



# 2016 version
WORK_DIR = "/afs/desy.de/user/n/nissanuv/nfs/x1x2x1/signal/skim"
WORK_DIR = "/nfs/dust/cms/user/beinsam/x1x2x1/signal/skim_sam/"

if phase1:
    WORK_DIR = "/nfs/dust/cms/user/beinsam/x1x2x1/signal/skim_phase1"
elif phase1_2018:
    WORK_DIR = "/nfs/dust/cms/user/diepholq/x1x2x1/signal/skim_pmssm/dataset_Autumn18Fast.PMSSM_set_2_LL_1"

SINGLE_OUTPUT = WORK_DIR + "/single"
OUTPUT_SUM = WORK_DIR + "/sum"

# 2016 version
##if not phase1 and not phase1_2018:#sam commented these out because the branches were being added to the single files
##    OUTPUT_SUM = SINGLE_OUTPUT


OUTPUT_SUM_OUTPUT = WORK_DIR + "/stdout"
OUTPUT_SUM_ERROR = WORK_DIR + "/stderr"


if not os.path.isdir(OUTPUT_SUM_OUTPUT):
    os.mkdir(OUTPUT_SUM_OUTPUT)

if not os.path.isdir(OUTPUT_SUM_ERROR):
    os.mkdir(OUTPUT_SUM_ERROR)

condor_wrapper = utils.TOOLS_BASE_PATH + "/analysis/scripts/condor_wrapper.sh"
add_observable_script = utils.TOOLS_BASE_PATH + "/analysis/scripts/add_dqa_observables_to_tree.py"


print(("Start: " + datetime.now().strftime('%d-%m-%Y %H:%M:%S')))

condor_file="/tmp/condor_submut." + datetime.now().strftime('%d-%m-%Y_%H:%M:%S')
print("condor submit file:", condor_file)

quotmark: str = str('"')
def main():
    condor_f = open(condor_file,'w')
    condor_f.write('''
universe = vanilla
should_transfer_files = IF_NEEDED
executable = /bin/bash
notification = Never
request_memory = 16 GB
''')
    files_per_job: int = 8
    files_per_job_counter: int = 1
    file_counter: int = 0
    print("Adding histograms.")
    #fileList = glob(WORK_DIR + "/*");
    fileList = glob(SINGLE_OUTPUT + "/*");
    for f in fileList:
        file_counter += 1
        filename = os.path.basename(f).split(".")[1] #pmssm

        command = add_observable_script + " -i " + f
        print("Performing:", command)
    
        #system(command)
        if files_per_job_counter == 1:
            condor_f.write("arguments = " + quotmark + condor_wrapper + " " + command)
        elif files_per_job_counter > 1 and files_per_job_counter < files_per_job:
            condor_f.write("," + f)
        else:
            condor_f.write("," + f + quotmark + "\n")
        # condor_f.write("arguments = " + quotmark + condor_wrapper + " " + command + quotmark + "\n")
        if files_per_job_counter == files_per_job:
            condor_f.write("error = " + OUTPUT_SUM_ERROR + "/" + filename + "_add_daq.err" + "\n")
            condor_f.write("output = " + OUTPUT_SUM_OUTPUT + "/" + filename + "_add_daq.out" + "\n")
            condor_f.write("Queue\n")
            files_per_job_counter = 0
        files_per_job_counter += 1
    condor_f.write(quotmark + "\nerror = " + OUTPUT_SUM_ERROR + "/" + filename + "_add_daq.err" + "\n")
    condor_f.write("output = " + OUTPUT_SUM_OUTPUT + "/" + filename + "_add_daq.out" + "\n")
    condor_f.write("Queue\n")

    condor_f.close()
    # system("condor_submit " + condor_file)
    print(condor_file)
    print(f"Number of files to be processed: {file_counter}")
main()

exit(0)
