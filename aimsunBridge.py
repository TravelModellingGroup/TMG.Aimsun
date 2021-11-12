"""
    Copyright 2021 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of XTMF.

    XTMF is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    XTMF is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with XTMF.  If not, see <http://www.gnu.org/licenses/>.
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

class AimSunBridge:
    """this class is the aimsun bridge we are building that is based off the emme bridge """
    def __init__(self):
        # Message numbers
        """Tell XTMF that we are ready to start accepting messages"""
        self.SignalStart = 0
        """Tell XTMF that we exited / XTMF is telling us to exit"""
        self.SignalTermination = 1
        #"""XTMF is telling us to start up a tool <Depricated>"""
        #self.SignalStartModule = 2
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
        self.aimsunPipe = open('\\\\.\\pipe\\' + pipeName, 'w+b',0)
        # extract path of network file
        self.NetworkPath = sys.argv[2]

        # Redirect sys.stdout
        sys.stdin.close()
        self.IOLock = threading.Lock()
        sys.stdin = None
        # TODO: Figure out what this function is and how to write it 
        # sys.stdout = RedirectToXTMFConsole(self)

    def sendSignal(self, signal):
        # this function takes an integer aka the signal number as an input and passes it as a bit 32 signed integer
        # as an array of type l to c# 
        intArray = array.array('l')
        intArray.append(signal)
        intArray.tofile(self.aimsunPipe)
        # flush the pipe to clear the pipe not the array
        self.aimsunPipe.flush()
        return
    
    def sendString(self, stringToSend):
        msg = array.array('u', str(stringToSend))
        length = len(msg) * msg.itemsize
        tempLength = length
        bytes = 0
        # figure out how many bytes we are going to need to store the length
        while tempLength > 0:
            tempLength = tempLength >> 7
            bytes += 1
        lengthArray = array.array('B')
        if length <= 0:
            lengthArray.append(0)
        else:
            tempLength = length
            for i in range(bytes):
                current = int(tempLength >> 7)
                current = int(current << 7)
                diff = tempLength - current
                if tempLength < 128:
                    lengthArray.append(diff)
                else:
                    lengthArray.append(diff + 128)
                tempLength = tempLength >> 7
        lengthArray.tofile(self.aimsunPipe)
        msg.tofile(self.aimsunPipe)
        self.aimsunPipe.flush()
        return

    def readInt(self):
        # this function reads the input the c# side server gives us. 
        # note this function will give us a number a string and a json of parameters
        intArray = array.array('l')
        intArray.fromfile(self.aimsunPipe, 1)
        return intArray.pop()

    def readString(self):
        # function to read the string coming from the C# pipeline
        length = self.readInt()
        try:
            # create an unicode array
            stringArray = array.array('u')
            # read from the pipe up to the length of the message
            # multiplying by 2 since unicode is 16 bits
            stringArray.fromfile(self.aimsunPipe, length)
            return stringArray.tounicode()
        except Exception as e:
            #traceback outputs more information such as call output stack
            traceback.print_exc()
            return "error reading"
        
    def executeAimsunScript(self, moduleDict, console, model):
        """This function is responsible for calling the modules of interest. It passes 
        in the console and model and uses the importlib library to import and run the module
        """
        try:
            #we need to append the Toolbox/InputPut folder path so all relative imports will work
            sys.path.append(moduleDict['parameters']['ToolboxInputOutputPath'])
            spec = importlib.util.spec_from_file_location('tool', moduleDict['toolPath'])
            moduleToRun = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(moduleToRun)
            #runAimsun is a function that all modules will have hence hard-coded here
            func = getattr(moduleToRun, "run_xtmf")
            # attaching module name of particular and running it with parameters
            func(moduleDict['parameters'], model, console)
        finally:
            #remove the Toolbox folder from the sys.path once the module is finished executing
            #remove the last element from the list
            sys.path.pop()

    def executeModule(self, console, model):
        """Function which executes the modules by extracting the tool and 
        its json parameters
        """
        macroName = None
        parameterString = None
        # run the module here
        try:
            # extract the name of the tool along with the parameters and pass it to the function
            macroName = self.readString()
            parameterString = self.readString()
            nameSpace = {'toolPath':macroName, 'parameters':json.loads(parameterString)}
            # run our script with passed in json
            self.executeAimsunScript(nameSpace, console, model)
            # send to the pipe that we ran the message successfully
            self.sendSuccess()
        except Exception as e:
            #traceback outputs more information such as call output stack
            err = traceback.print_exc()
            self.sendRuntimeError(repr(err))
        return

    def sendRuntimeError(self, problem):
        self.IOLock.acquire()
        self.sendSignal(self.SignalRuntimeError)
        self.sendString(problem)
        self.IOLock.release()
        return
    
    def sendSuccess(self):
        self.IOLock.acquire()
        intArray = array.array('l')
        intArray.append(self.SignalRunComplete)
        intArray.tofile(self.aimsunPipe)
        self.IOLock.release()
        return
    
    def checkToolExists(self):
        return True

    def loadModel(self, console):
        """Function to load the model
        open the console and create a model. This is passed around inside this script and also
        to external modules
        """
        if console.open(self.NetworkPath):
            model = console.getModel()
            print("Network opened successfully")
        else:
            console.getLog().addError("Cannot load the network")
            print("Cannot load the network")
        return model


    def switchModel(self, console):
        """function to open a new model based on a new network. The network filepath
        is passed from the bridge
        """
        print ("switching model")
        try:
            # extract the name of the tool along with the parameters and pass it to the function
            self.NetworkPath = self.readString()
            print ('switched path files ', self.NetworkPath)

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
        savenetwork signal
        """
        try:
            outputPath = self.readString()
            print ('saving file to: ', outputPath)
            #save model to outputpath file location
            console.save(outputPath)
            # Reset the Aimsun undo buffer
            model.getCommander().addCommand(None)

            #check if file exists and was saved
            boolFileExists = os.path.isfile( outputPath)
            if boolFileExists == False:
                self.sendRuntimeError(str("This filepath doesn't exist please check the directory is correct"))
            else:
                #send successful run of command
                self.sendSuccess()
            
            #send successful run of command
            #self.sendSuccess()
        except Exception as e:
            #traceback outputs more information such as call output stack
            err = traceback.print_exc()
            self.sendRuntimeError(str(err))

    def run(self):
        # Function to run the pipe
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
            while (not exit):
                # try:
                input = self.readInt()
                if input == self.SignalTermination:
                    exit = True
                elif input == self.SignalStartModuleBinaryParameters:
                    self.executeModule(console, model)
                elif input == self.SignalCheckToolExists:
                    self.checkToolExists()
                elif input == self.SignalSwitchNetworkPath:
                    #we need to switch the network path and open console and get
                    #model to that network
                    model = self.switchModel(console)
                elif input == self.SignalSaveNetwork:
                    #we need to save the network
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
    # initialize and run the class
    aimsunMain = AimSunBridge()
    aimsunMain.run()
    
if __name__ == "__main__":
    main()
