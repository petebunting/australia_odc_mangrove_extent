#! /usr/bin/env python

############################################################################
# Copyright (c) 2012 Pete Bunting, Aberystwyth University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#
# Purpose:  Submit jobs to pbs qsub.
# Author: Pete Bunting
# Email: petebunting@mac.com
# Date: 28/03/2017
# Version: 1.0
#
# History:
# Version 1.0 - Created.
#
#############################################################################


import os.path
import sys
from time import strftime
import argparse

def createOutputFiles(inputFile, outputFile, memory, timeStr, nCores, project):                
    outCmdsFile = open(outputFile, 'w')
    outCmdsFile.write("#!/bin/bash \n")
    outCmdsFile.write("#PBS -P " + project + str("\n"))
    outCmdsFile.write("#PBS -q normal\n")
    outCmdsFile.write("#PBS -l walltime="+timeStr+",mem="+memory+",ncpus="+str(nCores)+"\n")
    outCmdsFile.write("#PBS -l wd\n\n")
    
    outCmdsFile.write("module use /g/data/v10/public/modules/modulefiles\n")
    outCmdsFile.write("module load agdc-py3-prod\n\n")
    
    outCmdsFile.write("module load parallel\n\n")        

    outCmdsFile.write("parallel --delay .2 -j "+str(nCores)+" < " + inputFile + "\n\n")
    outCmdsFile.flush()
    outCmdsFile.close()            


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", dest="inputFile", type=str, required=True, help="Input list of commands (1 per line)")
    parser.add_argument("-o", "--output", dest="outputFile", type=str, required=True, help="Output file which is to be submitted to qsub")
    parser.add_argument("-m", "--memory", dest="memory", type=str, required=True, help="The amount of memory (e.g., 32Gb)")
    parser.add_argument("-t", "--time", dest="timeStr", type=str, required=True, help="The time limit for the jobs (HH:MM:SS).")
    parser.add_argument("-c", "--cores", dest="nCores", type=str, required=True, help="Number of cores to be used for the processing.")
    parser.add_argument("-p", "--project", dest="projectName", type=str, required=True, help="Name of the project the job is being submitted under.")

    args = parser.parse_args()
        
    createOutputFiles(args.inputFile, args.outputFile, args.memory, args.timeStr, args.nCores, args.projectName)



