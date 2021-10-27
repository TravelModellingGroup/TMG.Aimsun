/*
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

        private string AddQuotes(string fileName)
        {
            return String.Concat("\"", fileName, "\"");
        }

        public ModellerController(IModule module, string projectFile, string pipeName, string aimsunPath, bool launchAimsun=true)
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
                                    toPrint = reader.ReadString();
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
        /// Throws an exception if the bridge has been disposed
        /// </summary>
        private void EnsureWriteAvailable(IModule caller)
        {
            if (_aimsunPipe == null)
            {
                throw new XTMFRuntimeException(caller, "Aimsun Bridge was invoked even though it has already been disposed.");
            }
        }

        /// <summary>
        /// Method outputting a bool that alllows us to pass in a NetworkPath to
        /// change the network we wish to analyze. Useful for running our unittests
        /// </summary>
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
