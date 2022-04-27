"""
    Copyright 2021 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of TMGToolbox for Aimsun.

    TMGToolbox for Aimsun is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    TMGToolbox for Aimsun is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with TMGToolbox for Aimsun.  If not, see <http://www.gnu.org/licenses/>.
"""

from io import StringIO
import sys
import os
import warnings as _warn
import traceback as _tb
import subprocess as _sp
import traceback
import shlex
import array
import threading
import json
import importlib
import importlib.util
import traceback
from PyANGApp import *
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
import time
import re

class AimSunBridge:
    """this class is the aimsun bridge we are building that is based off the Emme bridge"""

    def __init__(self):
        # Message numbers
        """Tell XTMF that we are ready to start accepting messages"""
        self.SignalStart = 0
        """Tell XTMF that we exited / XTMF is telling us to exit"""
        self.SignalTermination = 1
        # """XTMF is telling us to start up a tool <Depricated>"""
        # self.SignalStartModule = 2
        """Tell XTMF that we have successfully ran the requested tool"""
        self.SignalRunComplete = 3
        """Tell XTMF that we have had an error when creating the parameters"""
        self.SignalParameterError = 4
        """Tell XTMF that we have had an error while running the tool"""
        self.SignalRuntimeError = 5
        """XTMF says we need to clean out the modeller log book"""
        self.SignalCleanLogbook = 6
        """We say that we need to generate a progress report for XTMF"""
        self.SignalProgressReport = 7
        """Tell XTMF that we have successfully ran the requested tool"""
        self.SignalRunCompleteWithParameter = 8
        """XTMF is requesting a check if a Tool namespace exists"""
        self.SignalCheckToolExists = 9
        """Tell XTMF that we have had an error finding the requested tool"""
        self.SignalSendToolDoesNotExistsError = 10
        """Tell XTMF that a print statement has been encountered and to write to the Run Console"""
        self.SignalSendPrintMessage = 11
        """Signal from XTMF to disable writing to logbook"""
        self.SignalDisableLogbook = 12
        """Signal from XTMF to enable writing to logbook"""
        self.SignalEnableLogbook = 13
        """Signal from XTMF to start up a tool using binary parameters"""
        self.SignalStartModuleBinaryParameters = 14
        """Signal to XTMF saying that the current tool is not compatible with XTMF2"""
        self.SignalIncompatibleTool = 15
        """A signal to switch and open the console on a new path"""
        self.SignalSwitchNetworkPath = 16
        """A signal to save the network"""
        self.SignalSaveNetwork = 17

        # open the named pipe
        pipeName = sys.argv[1]
        self.aimsunPipe = open("\\\\.\\pipe\\" + pipeName, "w+b", 0)
        # extract path of network file
        self.NetworkPath = sys.argv[2]

        # Redirect sys.stdout
        sys.stdin.close()
        self.IOLock = threading.Lock()
        sys.stdin = None
        # TODO: Figure out what this function is and how to write it
        # sys.stdout = RedirectToXTMFConsole(self)

    def sendSignal(self, signal):
        """
        this function takes an integer aka the signal number as an input and passes it as
        a bit 32 signed integer
        """
        # as an array of type l to c#
        intArray = array.array("l")
        intArray.append(signal)
        intArray.tofile(self.aimsunPipe)
        # flush the pipe to clear the pipe not the array
        self.aimsunPipe.flush()
        return

    def sendString(self, stringToSend):
        """
        Send string  message to XTMF
        """
        msg = array.array("u", str(stringToSend))
        length = len(msg) * msg.itemsize
        self.sendSignal(length)
        msg.tofile(self.aimsunPipe)
        self.aimsunPipe.flush()
        return

    def readInt(self):
        """
        This function reads the input the c# side server gives us.
        note this function will give us a number a string and a json of parameters.
        """
        intArray = array.array("l")
        intArray.fromfile(self.aimsunPipe, 1)
        return intArray.pop()

    def readString(self):
        """
        Function to read the string coming from the C# pipeline
        """
        length = self.readInt()
        try:
            # create an unicode array
            stringArray = array.array("u")
            # read from the pipe up to the length of the message
            # multiplying by 2 since unicode is 16 bits
            stringArray.fromfile(self.aimsunPipe, length)
            return stringArray.tounicode()
        except Exception as e:
            # traceback outputs more information such as call output stack
            traceback.print_exc()
            return "error reading"

    def executeAimsunScript(self, moduleDict, console, model):
        """
        This function is responsible for calling the modules of interest. It passes
        in the console and model and uses the importlib library to import and run the module
        """
        try:
            #check if the tool exists in the path if it doesn't output an error
            if not os.path.exists(moduleDict["toolPath"]):
                raise Exception("Unable to find the tool '" + moduleDict["toolPath"] + "'.")
            # we need to append the Toolbox/InputPut folder path so all relative imports will work
            toolDirectory = os.path.dirname(moduleDict["toolPath"])
            sys.path.append(toolDirectory)
            # add the base TMG toolbox path to the sys paths so we can access the common module
            print (moduleDict["toolPath"])
            # check if the tool is from the inputOutput so we can parse the url
            if "inputOutput" in moduleDict["toolPath"]:
                # use re to parse the last elements of the string url so only the 
                # TMGToolbox part of the url is appended to the sys path
                folderPath = re.sub(r'inputOutput.*', "", moduleDict["toolPath"])
                print (folderPath)
                sys.path.append(folderPath)

            spec = importlib.util.spec_from_file_location(
                "tool", moduleDict["toolPath"]
            )
            moduleToRun = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(moduleToRun)
            # runAimsun is a function that all modules will have hence hard-coded here
            func = getattr(moduleToRun, "run_xtmf")
            # attaching module name of particular and running it with parameters
            func(moduleDict["parameters"], model, console)
        finally:
            # remove the Toolbox folder from the sys.path once the module is finished executing
            # remove the last element from the list
            sys.path.pop()

    def executeModule(self, console, model):
        """
        Function which executes the modules by extracting the tool and
        its json parameters
        """
        macroName = None
        parameterString = None
        # run the module here
        try:
            # extract the name of the tool along with the parameters and pass it to the function
            macroName = self.readString()
            parameterString = self.readString()
            nameSpace = {
                "toolPath": macroName,
                "parameters": json.loads(parameterString),
            }
            # run our script with passed in json
            self.executeAimsunScript(nameSpace, console, model)
            # send to the pipe that we ran the message successfully
            self.sendSuccess()
        except Exception as e:
            # output the call stack and pass to XTMF
            etype, evalue, etb = sys.exc_info()
            stackList = traceback.extract_tb(etb)
            msg = "%s: %s\n\nStack trace below:" % (evalue.__class__.__name__, str(evalue))
            stackList.reverse()
            for file, line, func, text in stackList:
                msg += "\n  File '%s', line %s, in %s" % (file, line, func)
            self.sendRuntimeError(msg)
        return

    def sendRuntimeError(self, problem):
        """
        Send runtime errors to XTMF.
        """
        self.IOLock.acquire()
        self.sendSignal(self.SignalRuntimeError)
        self.sendString(problem)
        self.IOLock.release()
        return

    def sendSuccess(self):
        """
        Send a successful run complete signal to XTMF
        """
        self.IOLock.acquire()
        intArray = array.array("l")
        intArray.append(self.SignalRunComplete)
        intArray.tofile(self.aimsunPipe)
        self.IOLock.release()
        return

    def checkToolExists(self):
        return True

    def loadModel(self, console):
        """
        Function to load the model
        open the console and create a model. This is passed around inside this script and also
        to external modules.
        """
        if console.open(self.NetworkPath):
            model = console.getModel()
            print("Network opened successfully")
        else:
            console.getLog().addError("Cannot load the network")
            print("Cannot load the network")
        return model

    def switchModel(self, console):
        """
        Function to open a new model based on a new network. The network filepath
        is passed from the bridge.
        """
        print("switching model")
        try:
            # extract the name of the tool along with the parameters and pass it to the function
            self.NetworkPath = self.readString()
            print("switched path files ", self.NetworkPath)

            model = self.loadModel(console)
            # send to the pipe that we ran the message successfully
            self.sendSuccess()
            return model
        except Exception as e:
            err = traceback.print_exc()
            self.sendRuntimeError(str(err))

    def saveModel(self, console, model):
        """
        Save the model to the provided outpath file if bridge passes
        savenetwork signal.
        """
        try:
            outputPath = self.readString()
            # save model to outputpath file location
            console.save(outputPath)
            # Reset the Aimsun undo buffer
            model.getCommander().addCommand(None)

            # check if file exists and was saved
            boolFileExists = os.path.isfile(outputPath)
            if boolFileExists == False:
                self.sendRuntimeError(
                    "This filepath doesn't exist please check the directory is correct."
                )
            else:
                # send successful run of command
                self.sendSuccess()
        except Exception as e:
            # traceback outputs more information such as call output stack
            err = traceback.print_exc()
            self.sendRuntimeError(str(err))

    def run(self):
        """
        Function to run the pipe
        """
        # use a local exit flag if the flag is set to true we will gracefully exist and
        # close the pipe otherwise we keep it running if exit=false the default setting
        exit = False

        # open the console and create a model. This is passed around inside this script and also
        # the modules of interest.
        console = ANGConsole([])
        model = self.loadModel(console)

        # send the start signal the first signal to C# server side
        self.sendSignal(self.SignalStart)
        try:
            while not exit:
                # try:
                input = self.readInt()
                if input == self.SignalTermination:
                    exit = True
                elif input == self.SignalStartModuleBinaryParameters:
                    self.executeModule(console, model)
                elif input == self.SignalCheckToolExists:
                    self.checkToolExists()
                elif input == self.SignalSwitchNetworkPath:
                    # we need to switch the network path and open console and get
                    # model to that network
                    model = self.switchModel(console)
                elif input == self.SignalSaveNetwork:
                    # we need to save the network
                    self.saveModel(console, model)
                else:
                    # If we do not understand what XTMF is saying quietly die
                    exit = True
                    self.sendSignal(self.SignalTermination)
        finally:
            # in the case of an error close is still called
            console.close()
        return

def main():
    """
    Initialize and run the class.
    """
    aimsunMain = AimSunBridge()
    aimsunMain.run()

if __name__ == "__main__":
    main()
