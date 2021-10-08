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
        
        #open the named pipe 
        #TODO THIS HAS TO BE DYNAMIC AS IT COULD BE DEBUG OR NUMBERED PIPE
        pipeName = sys.argv[1] 
        self.aimsunPipe = open('\\\\.\\pipe\\' + pipeName, 'w+b',0)

        # Redirect sys.stdout
        sys.stdin.close()
        self.IOLock = threading.Lock()
        sys.stdin = None
        #TODO: Figure out what this function is and how to write it 
        #sys.stdout = RedirectToXTMFConsole(self)

    def sendSignal(self, signal):
        #this function takes an integer aka the signal number as an input and passes it as a bit 32 signed integer
        # as an array of type l to c# 
        intArray = array.array('l')
        intArray.append(signal)
        intArray.tofile(self.aimsunPipe)
        #flush the pipe to clear the pipe not the array
        self.aimsunPipe.flush()
        return
    
    def sendString(self, stringToSend):
        msg = array.array('u', str(stringToSend))
        length = len(msg) * msg.itemsize
        tempLength = length
        bytes = 0
        #figure out how many bytes we are going to need to store the length
        #string
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
        #this function reads the input the c# side server gives us. 
        #note this function will give us a number a string and a json of parameters
        intArray = array.array('l')
        intArray.fromfile(self.aimsunPipe, 1)
        return intArray.pop()

    def readString(self):
        #function to read the string coming from the C# pipeline
        length = self.readInt()
        try:
            #create an unicode array
            stringArray = array.array('u')
            #read from the pipe up to the length of the message
            #multiplying by 2 since unicode is 16 bits
            stringArray.fromfile(self.aimsunPipe, length)
            return stringArray.tounicode()
        except Exception as e:
            print (e)
            return "error reading"

    def executeModule(self):
        macroName = None
        parameterString = None
        # run the module here
        try:
            #figure out how long the macro's name is
            macroName = self.readString()
            parameterString = self.readString()
            #send to the pipe that we ran the message successfully
            self.sendSuccess()
        except Exception as e:
            self.sendRuntimeError(str(e))
        return

    def sendRuntimeError(self, problem):
        self.IOLock.acquire()
        self.SendSignal(self.SignalRuntimeError)
        self.SendString(problem)
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

    def run(self):
        #function to run the pipe
        #use a local exit flag if the flag is set to true we will gracefully exist and
        #close the pipe otherwise we keep it running if exit=false the default setting 
        exit = False

        #send the start signal the first signal to C#
        self.sendSignal(self.SignalStart)
    
        while (not exit):
            #try:
            input = self.readInt()
            if input == self.SignalTermination:
                #_m.logbook_write("Exiting on termination signal from XTMF")
                exit = True
            elif input == self.SignalStartModuleBinaryParameters:
                self.executeModule()
            elif input == self.SignalCheckToolExists:
                self.checkToolExists()
            else:
                #If we do not understand what XTMF is saying quietly die
                exit = True
                self.sendSignal(self.SignalTermination)
        return

def main():
    #initalize and run the class
    aimsunMain = AimSunBridge()
    aimsunMain.run()
    
if __name__ == "__main__":
    main()
