# Load in the required libraries
import sys
import time
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
import shlex

def parseArguments(argv):
    if len(argv) < 3:
        print("Incorrect Number of Arguments")
        print("Arguments: -script script.py blankAimsunProjectFile.ang networkDirectory outputNetworkFile.ang")
    inputModel = argv[1]
    networkDirectory = argv[2]
    outputNetworkFilename = argv[3]
    return inputModel, networkDirectory, outputNetworkFilename

def main(argv):
    console = ANGConsole()
    inputModel, networkDir, outputNetworkFilename = parseArguments(argv)


if __name__ == "__main__":
    main(sys.argv)