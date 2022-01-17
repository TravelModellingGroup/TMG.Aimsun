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
using System.Collections.Generic;
using System.IO;

namespace TMG.Aimsun.Tests
{
    [TestClass]
    public class TestModuleMacroAssignment
    {

        [TestMethod]
        public void RunMacroAssignment()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\FrabitztownNetworkWithOd2.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "assignment\\macroAssignment.py");
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                OutputNetworkFile = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\output\\FrabitztownNetworkWithAssign.ang"),
                ModelDirectory = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\Frabitztown"),
                ToolboxInputOutputPath = Path.Combine(Helper.TestConfiguration.NetworkFolder, "src\\TMGToolbox\\assignment"),
                autoDemand = "testOD",
                Start = 6.0 * 60.0,
                Duration = 3.0 * 60.0,
                transitDemand = "transitOD"
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
        }

        [TestMethod]
        public void RunRoadAssignment()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\FrabitztownNetworkWithOd2.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "assignment\\roadAssignment.py");
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                autoDemand = "testOD",
                Start = 360.0,
                Duration = 180.0,
                transitDemand = "transitOD"
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
        }

        [TestMethod]
        public void RunTransitAssignment()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\FrabitztownNetworkWithOd2.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "assignment\\transitAssignment.py");
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                autoDemand = "testOD",
                Start = 6.0 * 60.0,
                Duration = 3.0 * 60.0,
                transitDemand = "transitOD"
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
        }

        [TestMethod]
        public void TestToolPipeline()
        {
            string networkPath = Helper.BuildFilePath("inputFiles\\Frabitztown.nwp");
            Utility.RunImportNetworkTool(networkPath, Helper.BuildModulePath("inputOutput\\importNetwork.py"));
            Utility.RunImportPedestriansTool();
            Utility.RunImportNetworkTool(networkPath, Helper.BuildModulePath("inputOutput\\importTransitNetwork.py"));
            Utility.RunImportTransitScheduleTool(networkPath, Helper.BuildFilePath("inputFiles\\frab_service_table.csv"));
            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownMatrixList.csv"), 
                                                              Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "testOD", "baseCentroidConfig", 
                                                              "Car Class ", "06:00:00:000", "03:00:00:000");
            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownMatrixList.csv"),
                                                              Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "transitOD", "ped_baseCentroidConfig",
                                                              "transit", "06:00:00:000", "03:00:00:000");
            Utility.RunRoadAssignmentTool("testOD", 360.0, 180.0, "transitOD");



        }

        [TestMethod]
        public void checkandswitchnetwor()
        {

            //change the network
            //string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\FrabitztownNetworkWithTransit.ang");
            //Helper.Modeller.SwitchModel(null, newNetwork);
        }
    }
}
