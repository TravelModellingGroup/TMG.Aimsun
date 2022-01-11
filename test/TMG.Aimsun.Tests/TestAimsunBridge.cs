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

using Microsoft.VisualStudio.TestTools.UnitTesting;
using Newtonsoft.Json;
using System.IO;

namespace TMG.Aimsun.Tests
{
    [TestClass]
    public class TestAimsunBridge
    {
        [Microsoft.VisualStudio.TestTools.UnitTesting.AssemblyCleanup]
        public static void TestCleanUp()
        {
            //get modeller if modeller is not null dispose
            Helper.Modeller?.Dispose();
        }

        [Microsoft.VisualStudio.TestTools.UnitTesting.AssemblyInitialize]
        public static void InitTest(TestContext _)
        {
            //initialize the Aimsun module
            Helper.InitializeAimsun();
        }

        [TestMethod]
        public void ConstructAimsunBridge()
        {
            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "inputOutput\\importNetwork.py");
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                OutputNetworkFile = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\output\\FrabitztownNetwork.ang"),
                ModelDirectory = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\Frabitztown"),
                ToolboxInputOutputPath = Path.Combine(Helper.TestConfiguration.NetworkFolder, "src\\TMGToolbox\\inputOutput")
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
        }

        [TestMethod]
        public void TestSaveNetwork()
        {
            //testing that we will save the network only if the save signal is sent
            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "inputOutput\\importNetwork.py");
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                OutputNetworkFile = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\output\\FrabitztownNetwork.ang"),
                ModelDirectory = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\Frabitztown"),
                ToolboxInputOutputPath = Path.Combine(Helper.TestConfiguration.NetworkFolder, "src\\TMGToolbox\\inputOutput")
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
            //build an output file location of where to save the file
            string outputPath = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\test2\\FrabitztownNetwork.ang");
            Helper.Modeller.SaveNetworkModel(null, outputPath);
        }

        [TestMethod]
        public void TestSaveNetworkWithInvalidPath()
        {
            //testing that we will save the network only if the save signal is sent
            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "inputOutput\\importNetwork.py");
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                OutputNetworkFile = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\output\\FrabitztownNetwork.ang"),
                ModelDirectory = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\Frabitztown"),
                ToolboxInputOutputPath = Path.Combine(Helper.TestConfiguration.NetworkFolder, "src\\TMGToolbox\\inputOutput")
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
            //build an output file location of where to save the file
            string outputPath = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\test3\\BadPath.ang");
            Helper.Modeller.SaveNetworkModel(null, outputPath);
        }
    }
}
