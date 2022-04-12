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
using System.Collections.Generic;
using System.IO;

namespace TMG.Aimsun.Tests
{
    [TestClass]
    public class TestModuleMacroAssignment
    {
        [TestMethod]
        public void CreateTrafficDemand()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\roadTest1.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);
            List<TrafficDemandClassParameters> matrixParameters1 = new List<TrafficDemandClassParameters>()
            {
                new TrafficDemandClassParameters() {NameODMatrix="testOD", InitialTime=360.0, Duration=180.0},
                new TrafficDemandClassParameters() {NameODMatrix="transitOD", InitialTime=360.0, Duration=60.0}
            };
            Utility.RunTrafficDemand("DoubleTest1", matrixParameters1);
            List<TrafficDemandClassParameters> matrixParameters2 = new List<TrafficDemandClassParameters>()
            {
                new TrafficDemandClassParameters() {NameODMatrix="transitOD", InitialTime=360.0, Duration=180.0}
            };
            Utility.RunTrafficDemand("Transit Demand ", matrixParameters2);
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\TD1.ang"));
        }

        [TestMethod]
        public void CreatePublicTransitPlan()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\TD1.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);
            Utility.RunCreatePublicTransitPlan("TEST PUBLIC PLAN");
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\PT1.ang"));
        }

        [TestMethod]
        public void RunRoadAssignment()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\roadTest21.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);
            Utility.RunAssignmentTool("assignment\\roadAssignment.py", "DoubleTest1", "TEST IS  a pipeline test");
            Utility.RunAssignmentTool("assignment\\roadAssignment.py", "Transit Demand ", "TEST IS  a pipeline test");
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\TestRoadAssignment.ang"));
        }

        [TestMethod]
        public void RunTransitAssignment()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\roadAssignment.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\transitassignment4.ang"));
        }

        [TestMethod]
        public void TestToolPipeline()
        {
            string networkPath = Helper.BuildFilePath("inputFiles\\Frabitztown.nwp");
            Utility.RunImportNetworkTool(networkPath, Helper.BuildModulePath("inputOutput\\importNetwork.py"));
            Utility.RunImportNetworkTool(networkPath, Helper.BuildModulePath("inputOutput\\importTransitNetwork.py"));
            
            //run the remaining tools
            Utility.RunImportTransitScheduleTool(networkPath, Helper.BuildFilePath("inputFiles\\frab_service_table.csv"));
            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "testOD", "baseCentroidConfig",
                                                              "Car Class ", "06:00:00:000", "03:00:00:000");
            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "transitOD", "baseCentroidConfig",
                                                              "Transit Users", "06:00:00:000", "03:00:00:000");

            List<TrafficDemandClassParameters> matrixParameters1 = new List<TrafficDemandClassParameters>()
            {
                new TrafficDemandClassParameters() {NameODMatrix="testOD", InitialTime=360.0, Duration=180.0},
                new TrafficDemandClassParameters() {NameODMatrix="transitOD", InitialTime=360.0, Duration=60.0}
            };
            Utility.RunTrafficDemand("DoubleTest1", matrixParameters1);
            List<TrafficDemandClassParameters> matrixParameters2 = new List<TrafficDemandClassParameters>()
            {
                new TrafficDemandClassParameters() {NameODMatrix="transitOD", InitialTime=360.0, Duration=180.0}
            };
            Utility.RunTrafficDemand("Transit Demand", matrixParameters2);
            Utility.RunCreatePublicTransitPlan("PublicTransitTest1");
            Utility.RunAssignmentTool("assignment\\roadAssignment.py", "Transit Demand", "PublicTransitTest1");

            // if we don't do this here we won't get out transit matrices
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\roadTest21.ang"));
            //Helper.Modeller.SwitchModel(null, Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\road.ang"));
            //Utility.RunAssignmentTool("assignment\\transitAssignment.py", "testOD", 360.0, 180.0, "transitOD");
            //Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\transit.ang"));
            //Utility.RunExportTool(Helper.BuildFilePath("aimsunFiles\\results\\test1.csv"), "Skim - Cost: Car Class  ");
            //Utility.RunExportTool(Helper.BuildFilePath("aimsunFiles\\results\\test2.csv"), "Transit Skim - Initial Waiting Time: ");
        }

        [TestMethod]
        public void TestExtractTool()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\transit.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);
            Utility.RunExportTool(Helper.BuildFilePath("aimsunFiles\\results\\Acost.csv"), "ACost");
            Utility.RunExportTool(Helper.BuildFilePath("aimsunFiles\\results\\IVWT.csv"), "IVWT");
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\Road2.ang"));
        }
    }
}
