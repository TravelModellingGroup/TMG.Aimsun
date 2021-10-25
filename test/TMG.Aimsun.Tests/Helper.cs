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
    /// a property class of all the json keys. 
    /// When we parse a json file we save the result to this class
    /// json object of files of interest
    /// </summary>
    class TestConfiguration
    {
        public string BlankNetwork { get; set; }
        public string OutputNetworkFile { get; set; }
        public string NetworkDirectory { get; set; }
        public string AimsunPath { get; set; }
        public string ModulePath { get; set; }     
    }

    /// <summary>
    /// This class is a helper class that will help with generic functions
    /// First generic call is to open and read a task json which will house all the filepaths 
    /// and important information to run the bridge from Unittests 
    /// </summary>
    internal static class Helper
    {
        //initialize the modeller controller
        public static ModellerController Modeller { get; private set; }
        public static TestConfiguration TestConfiguration { get; set; }

        internal static string buildJSONParameters(string value)
        {
            //a function to convert a string into a json serialized object
            string json = JsonConvert.SerializeObject(value);
            return json;
        }
        internal static void InitializeAimsun()
        {
            //method to read the configuration file, parse and extract the data and run the modeller
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

                    Modeller = new ModellerController(null, TestConfiguration.BlankNetwork, pipeName, TestConfiguration.AimsunPath, !debuggerAttached);
                }
            }
        }
    }
}
