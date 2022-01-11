/*
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
*/

using System;
using System.Text;
using System.Threading.Tasks;
using System.IO;
using System.IO.Pipes;
using XTMF;
using System.Reflection;
using System.Diagnostics;
using System.Runtime.InteropServices;
using TMG.Aimsun.InputOutput;

namespace TMG.Aimsun
{
    public sealed class ModellerController : IDisposable
    {
        private static object _loadLock = new object();
        private NamedPipeServerStream _aimsunPipe;

        /// <summary>
        /// We receive this error if the bridge can not get the parameters to match
        /// the selected tool
        /// </summary>
        private const int SignalParameterError = 4;

        /// <summary>
        /// Receive a signal that contains a progress report
        /// </summary>
        private const int SignalProgressReport = 7;

        /// <summary>
        /// We receive this when the Bridge has completed its module run
        /// </summary>
        private const int SignalRunComplete = 3;

        /// <summary>
        /// We receive this when the Bridge has completed its module run and that there is a return value as well
        /// </summary>
        private const int SignalRunCompleteWithParameter = 8;

        /// <summary>
        /// We revive this error if the tool that we tell the bridge to run throws a
        /// runtime exception that is not handled within the tool
        /// </summary>
        private const int SignalRuntimeError = 5;

        /// <summary>
        /// We will receive this from the ModellerBridge
        /// when it is ready to start processing
        /// </summary>
        private const int SignalStart = 0;

        /// <summary>
        /// We will send this signal when we want to start to run a new module with binary parameters
        /// </summary>
        private const int SignalStartModuleBinaryParameters = 14;

        /// <summary>
        /// This is the message that we will send when it is time to shutdown the bridge.
        /// If we receive it, then we know that the bridge is in a panic and has exited
        /// </summary>
        private const int SignalTermination = 1;

        /// <summary>
        /// Signal the bridge to check if a tool namespace exists
        /// </summary>
        private const int SignalCheckToolExists = 9;

        /// <summary>
        /// Signal from the bridge throwing an exception that the tool namespace could not be found
        /// </summary>
        private const int SignalToolDoesNotExistError = 10;

        /// <summary>
        /// Signal from the bridge that a print statement has been called, to write to the XTMF Console
        /// </summary>
        private const int SignalSentPrintMessage = 11;

        /// <summary>
        /// A signal from the modeller bridge saying that the tool that was requested to execute does not
        /// contain an entry point for a call from XTMF2.
        /// </summary>
        private const int SignalIncompatibleTool = 15;
        /// <summary>
        /// A signal from the modeller bridge saying to switch the network path for the console to open
        /// and not use the starting network
        /// </summary>
        private const int SignalSwitchNetworkPath = 16;
        /// <summary>
        /// A signal from the modeller bridge saying to save the network model now. 
        /// </summary>
        private const int SignalSaveNetwork = 17;
        private string AddQuotes(string fileName)
        {
            return String.Concat("\"", fileName, "\"");
        }

        /// <summary>
        /// Method which opens the pipe.
        /// </summary>
        /// <param name="module">The calling module. Used for reporting errors for XTMF.</param>
        /// <param name="projectFile">Path to directory folder where Aimsun folders are located.</param>
        /// <param name="pipeName">Name of pipe. If running in debug mode, pipe name is called DebugAimsun otherwise name is random number.</param>
        /// <param name="aimsunPath">Path to aconsole.exe</param>
        /// <exception cref="XTMFRuntimeException"></exception>
        public ModellerController(IModule module, string projectFile, string pipeName, string aimsunPath)
        {
            //check if file path or ang file exists
            if (!projectFile.EndsWith(".ang") | !File.Exists(projectFile))
            {
                throw new XTMFRuntimeException(module, $"The Aimsun ProjectFile doesn't exist at {projectFile}"); // + e.Message);
            }

            //create a named pipe as a server stream 
            _aimsunPipe = new NamedPipeServerStream(pipeName, PipeDirection.InOut, 1, PipeTransmissionMode.Byte, PipeOptions.Asynchronous);
            try
            {
                var codeBase = typeof(ModellerController).GetTypeInfo().Assembly.Location;
                string argumentString = "-script " + AddQuotes(Path.Combine(Path.GetDirectoryName(codeBase), "AimsunBridge.py"))
                                        + " " + AddQuotes(pipeName) + " " + AddQuotes(projectFile);
                var aimsun = new Process();
                var startInfo = new ProcessStartInfo(Path.Combine(aimsunPath, "aconsole.exe"), argumentString);
                startInfo.WorkingDirectory = aimsunPath;
                aimsun.StartInfo = startInfo;
                aimsun.Start();
                _aimsunPipe.WaitForConnection();
                var reader = new BinaryReader(_aimsunPipe, System.Text.Encoding.Unicode, true);
                reader.ReadInt32();
            }
            catch (AggregateException e)
            {
                throw e.InnerException;
            }
        }

        /// <summary>
        /// Method which analyzes the signal coming from the bridge to determine next steps.
        /// </summary>
        /// <param name="caller">The calling module. Used for reporting errors for XTMF.</param>
        /// <returns>Returns True or False. If True bridge stays open. </returns>
        /// <exception cref="XTMFRuntimeException"></exception>
        private bool WaitForAimsunResponse(IModule caller)
        {
            // now we need to wait
            try
            {
                string toPrint;
                while (true)
                {
                    using (var reader = new BinaryReader(_aimsunPipe, Encoding.Unicode, true))
                    {
                        int result = reader.ReadInt32();
                        switch (result)
                        {
                            case SignalRuntimeError:
                                {
                                    toPrint = ReadString(reader);
                                    throw new XTMFRuntimeException(caller, toPrint);
                                }
                            case SignalStart:
                                {
                                    continue;
                                }
                            case SignalRunComplete:
                                {
                                    return true;
                                }
                            case SignalRunCompleteWithParameter:
                                {
                                    return true;
                                }
                            case SignalTermination:
                                {
                                    throw new XTMFRuntimeException(caller, "The Aimsun ModellerBridge panicked and unexpectedly shutdown.");
                                }
                            case SignalCheckToolExists:
                                {
                                    return true;
                                }
                            case SignalSentPrintMessage:
                                {
                                    toPrint = ReadString(reader);
                                    Console.Write(toPrint);
                                    break;
                                }
                            default:
                                {
                                    throw new XTMFRuntimeException(caller, "Unknown message passed back from the Aimsun ModellerBridge.  Signal number " + result);
                                }
                        }
                    }
                }
            }
            catch (EndOfStreamException)
            {
                throw new XTMFRuntimeException(caller, "We were unable to communicate with Aimsun.  Please make sure you have an active Aimsun license.  If the problem persists, sometimes rebooting has helped fix this issue with Aimsun.");
            }
            catch (IOException e)
            {
                throw new XTMFRuntimeException(caller, "I/O Connection with Aimsun ended while waiting for data, with:\r\n" + e.Message);
            }
        }

        /// <summary>
        /// Read the Bytes the bridge passes back 
        /// </summary>
        /// <param name="input">The binaryReader object that is passed back from the bridge</param>
        /// <returns>A string of the command and data</returns>
        private static string ReadString(BinaryReader input)
        {
            int size = input.ReadInt32();
            byte[] output = input.ReadBytes(size);
            return System.Text.Encoding.Unicode.GetString(output);
        }

        /// <summary>
        /// Throws an exception if the bridge has been disposed
        /// </summary>
        /// <param name="caller">The calling module. Used for reporting errors for XTMF.</param>
        /// <exception cref="XTMFRuntimeException"></exception>
        private void EnsureWriteAvailable(IModule caller)
        {
            if (_aimsunPipe == null)
            {
                throw new XTMFRuntimeException(caller, "Aimsun Bridge was invoked even though it has already been disposed.");
            }
        }

        /// <summary>
        /// Method that allows us to change the network by specifying a pre-defined network file.
        /// Used for running unit tests.
        /// </summary>
        /// <param name="caller">The calling module. Used for reporting errors for XTMF.</param>
        /// <param name="networkPath">the path to where the .ang network file is located.</param>
        /// <returns>Returns true if the script executed successfully, false otherwise.</returns>
        /// <exception cref="XTMFRuntimeException"></exception>
        public bool SwitchModel(IModule caller, string networkPath)
        {
            lock (this)
            {
                try
                {
                    EnsureWriteAvailable(caller);
                    // clear out all of the old input before starting
                    var writer = new BinaryWriter(_aimsunPipe, Encoding.Unicode, true);
                    {
                        writer.Write(SignalSwitchNetworkPath);
                        writer.Write(networkPath.Length);
                        writer.Write(networkPath.ToCharArray());
                        writer.Flush();
                    }
                }
                catch (IOException e)
                {
                    throw new XTMFRuntimeException(caller, "I/O Connection with Aimsun while sending data, with:\r\n" + e.Message);
                }
                return WaitForAimsunResponse(caller);
            }
        }

        /// <summary>
        /// Method to save the network model based on the file path provided.
        /// </summary>
        /// <param name="caller">The calling module. Used for reporting errors for XTMF.</param>
        /// <param name="networkPath">The path to where the saved .ang network file is stored.</param>
        /// <returns>Returns true if the script executed successfully, false otherwise.</returns>
        /// <exception cref="XTMFRuntimeException"></exception>
        public bool SaveNetworkModel(IModule caller, string networkPath)
        {
            lock (this)
            {
                try
                {
                    EnsureWriteAvailable(caller);
                    // clear out all of the old input before starting
                    var writer = new BinaryWriter(_aimsunPipe, Encoding.Unicode, true);
                    {
                        writer.Write(SignalSaveNetwork);
                        writer.Write(networkPath.Length);
                        writer.Write(networkPath.ToCharArray());
                        writer.Flush();
                    }
                }
                catch (IOException e)
                {
                    throw new XTMFRuntimeException(caller, "I/O Connection with Aimsun while sending data, with:\r\n" + e.Message);
                }
                return WaitForAimsunResponse(caller);
            }
        }

        /// <summary>
        /// Method to run Aimsun modules.
        /// </summary>
        /// <param name="caller">The calling module. Used for reporting errors for XTMF.</param>
        /// <param name="macroName">Name of Aimsun module to run.</param>
        /// <param name="jsonParameters">Input parameters to pass into the Aimsun module passed as json.</param>
        /// <returns>Returns true if the script executed successfully, false otherwise.</returns>
        /// <exception cref="XTMFRuntimeException"></exception>
        public bool Run(IModule caller, string macroName, string jsonParameters)
        {
            lock (this)
            {
                try
                {
                    EnsureWriteAvailable(caller);
                    // clear out all of the old input before starting
                    var writer = new BinaryWriter(_aimsunPipe, Encoding.Unicode, true);
                    {
                        writer.Write(SignalStartModuleBinaryParameters);
                        writer.Write(macroName.Length);
                        writer.Write(macroName.ToCharArray());
                        if (jsonParameters == null)
                        {
                            writer.Write((int)0);
                        }
                        else
                        {
                            writer.Write(jsonParameters.Length);
                            writer.Write(jsonParameters.ToCharArray());
                        }
                        writer.Flush();
                    }
                }
                catch (IOException e)
                {
                    throw new XTMFRuntimeException(caller, "I/O Connection with Aimsun while sending data, with:\r\n" + e.Message);
                }
                return WaitForAimsunResponse(caller);
            }
        }

        /// <summary>
        /// Method to gracefully close the bridge once all work is finished.
        /// </summary>
        /// <param name="managed">Incoming bool value. If True the bridge is closed otherwise keep bridge open.</param>
        private void Dispose(bool managed)
        {
            if (managed)
            {
                //calls garbage collector not to call deconstructor
                GC.SuppressFinalize(this);
            }
            if (_aimsunPipe != null && _aimsunPipe.IsConnected)
            {
                //collection to displose of the pipe this is garbage collection
                BinaryWriter writer = new BinaryWriter(_aimsunPipe, Encoding.Unicode, true);
                writer.Write(SignalTermination);
                writer.Flush();
                ((IDisposable)_aimsunPipe).Dispose();
                _aimsunPipe = null;
            }
        }
        public void Dispose()
        {
            Dispose(true);
        }
        ~ModellerController()
        {
            Dispose(false);
        }
    }
}
