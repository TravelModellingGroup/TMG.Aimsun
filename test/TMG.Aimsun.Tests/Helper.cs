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
using System.IO;
using Newtonsoft.Json;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using System.Diagnostics;
using XTMF;
using System.Collections.Generic;

namespace TMG.Aimsun.Tests
{
    /// <summary>
    /// Property class of all json parameters for traffic demand
    /// <param name="NameODMatrix">Name of OD matrix being used to create traffic demand</param>
    /// <param name="InitialTime">Initial time in minutes</param>
    /// <param name="Duration">Duration of demand in minutes</param>
    /// <param name="DemandName">The name of the Traffic Demand object</param>
    /// </summary>
    public class TrafficDemandClassParameters
    {
        public string NameODMatrix;
        public double InitialTime;
        public double Duration;
        public string DemandName;
    }

    /// <summary>
    /// Property class of all json parameters to change matrix names
    /// <param name="VehicleType">Type of vehicle</param>
    /// <param name="ACostName">Name of ACost Matrix</param>
    /// <param name="AIVTT">Name of AIVTT Matrix</param>
    /// </summary>
    public class MatrixName
    {
        public string VehicleType;
        public string ACostName;
        public string AIVTT;
        public string AToll;
    }

    /// <summary>
    /// Create a property class to rename matrices for transit assignment
    /// </summary>
    public class TransitAssignmentRenameMatrix
    {
        public string WalkTimes;
        public string AToll;
    }


    /// <summary>
    /// a property class of all the json configuration keys. 
    /// When we parse a json file we save the result to this class
    /// json object of files of interest.
    /// </summary>
    class TestConfiguration
    {
        ///<summary>
        ///The name of the parent network we wish to run.
        ///</summary>
        public string Network { get; set; }
        ///<summary>
        ///The parent folder where both the unzipped network and the aimsun files reside and are located.
        ///</summary>
        public string NetworkFolder { get; set; }
        ///<summary>
        ///Path to where Aimsun is installed and located.
        ///</summary>
        public string AimsunPath { get; set; }
        ///<summary>
        ///Base root folder to where aimsun python Aimsun modules are located.
        ///</summary>
        public string ModulePath { get; set; }
    }

    /// <summary>
    /// This class is a helper class that will help with generic functions
    /// First generic call is to open and read a task json which will house all the filepaths 
    /// and important information to run the bridge from Unittests 
    /// </summary>
    internal static class Helper
    {
        /// <summary>
        /// Initialized singleton Modeller Controller object.
        /// </summary>
        public static ModellerController Modeller { get; private set; }

        /// <summary>
        /// Singleton TestConfiguration object that stores the test configuration parameters.
        /// </summary>
        public static TestConfiguration TestConfiguration { get; set; }

        /// <summary>
        /// Method to build the path to the module
        /// </summary>
        /// <param name="userModulePath"> string of the name of the tool</param>
        /// <returns>string of the tool</returns>
        public static string BuildModulePath (string userModulePath)
        {
            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, userModulePath);
            return modulePath;
        }
        /// <summary>
        /// Method to build string path to the network package .nwp file
        /// </summary>
        /// <param name="userNetworkPath">string of the name of the network package</param>
        /// <returns>string of the path of networkpackage</returns>
        public static string BuildFilePath (string userNetworkPath)
        {
            string networkPath = Path.Combine(Helper.TestConfiguration.NetworkFolder, userNetworkPath);
            return networkPath;
        }

        /// <summary>
        /// Method to initalize the modeller and run the Aimsun controller
        /// </summary>
        internal static void InitializeAimsun()
        {
            //Method to read the configuration file, parse and extract the data and run the modeller
            if (Modeller == null)
            {
                //check if the file exists output an error if it doesn't exist for some reason
                var configFile = new FileInfo("TMG.Aimsun.Test.Configuration.json");
                if (!configFile.Exists)
                {
                    Assert.Fail("This file does not exist. Please create this file in your directory");
                }
                else
                {
                    var jsonData = File.ReadAllText(configFile.FullName);
                    TestConfiguration = JsonConvert.DeserializeObject<TestConfiguration>(jsonData);
                    //check if debugger is attached if it is used a random name otherwise use the default name DEBUGaimsum
                    bool debuggerAttached = Debugger.IsAttached;
                    string pipeName = debuggerAttached ? "DEBUGaimsun" : Guid.NewGuid().ToString();
                    string Network = Path.Combine(TestConfiguration.NetworkFolder, "aimsunFiles", TestConfiguration.Network);
                    Modeller = new ModellerController(null, Network, pipeName, TestConfiguration.AimsunPath);
                }
            }
        }
    }
}
