﻿/*
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
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\PipelineTest2.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);
            List<MatrixName> matrixParameters3 = new List<MatrixName>()
            {
                new MatrixName() { VehicleType="Car Class ", ACostName="Skim T1 - Car Class ACost", AIVTT="T1 - Car Class DIstance AIVTT", AToll="T1 Car Class Toll"},
                new MatrixName() { VehicleType="Transit Users", ACostName="T1 - Transit Users ACost", AIVTT="T1 - Transit Users DIstance AIVTT",  AToll="T1 Transit Users Toll"}
            };
            Utility.RunAssignmentTool("assignment\\roadAssignment.py", "CTRoadScenario", "CTExperiment", "CarAndTransitDemand", "PublicTransitTest1", matrixParameters3);
            List<MatrixName> matrixParameters4 = new List<MatrixName>()
            {
                new MatrixName() { VehicleType="Transit Users", ACostName="T2 - TUCOST", AIVTT="T2 - TUDIST", AToll="T2 - TUToll"}
            };
            Utility.RunAssignmentTool("assignment\\roadAssignment.py", "TRscenario", "TTExp", "Transit Demand", "PublicTransitTest1", matrixParameters4);
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\xxx.ang"));
        }

        [TestMethod]
        public void TestToolPipeline()
        {
            string networkPath = Helper.BuildFilePath("inputFiles\\Frabitztown.nwp");
            Utility.RunImportNetworkTool(networkPath, Helper.BuildModulePath("inputOutput\\importNetwork.py"));
            Utility.RunImportNetworkTool(networkPath, Helper.BuildModulePath("inputOutput\\importTransitNetwork.py"));
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
            Utility.RunTrafficDemand("CarAndTransitDemand", matrixParameters1);
            List<TrafficDemandClassParameters> matrixParameters2 = new List<TrafficDemandClassParameters>()
            {
                new TrafficDemandClassParameters() {NameODMatrix="transitOD", InitialTime=360.0, Duration=180.0}
            };
            Utility.RunTrafficDemand("Transit Demand", matrixParameters2);
            Utility.RunCreatePublicTransitPlan("PublicTransitTest1");

            List<MatrixName> matrixParameters3 = new List<MatrixName>()
            {
                new MatrixName() { VehicleType="Car Class ", ACostName="Skim T1 - Car Class ACost", AIVTT="Skim T1 - Car Class DIstance AIVTT", AToll="Skim T1 Car Class Toll"},
                new MatrixName() { VehicleType="Transit Users", ACostName="T1 - Transit Users ACost", AIVTT="T1 - Transit Users DIstance AIVTT",  AToll="T1 Transit Users Toll"}
            };
            Utility.RunAssignmentTool("assignment\\roadAssignment.py","CTScenario", "CTExp", "CarAndTransitDemand", "PublicTransitTest1", matrixParameters3);
            List<MatrixName> matrixParameters4 = new List<MatrixName>()
            {
                new MatrixName() { VehicleType="Transit Users", ACostName="T2 - TUCOST", AIVTT="T2 - TUDIST", AToll="T2 - TUToll"}
            };
            Utility.RunAssignmentTool("assignment\\roadAssignment.py", "TScenario", "TExp", "Transit Demand", "PublicTransitTest1", matrixParameters4);
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\PipelineTest3.ang"));
            Utility.RunExportTool(Helper.BuildFilePath("aimsunFiles\\results\\test1.csv"), "T2 - TUCOST");
            Utility.RunExportTool(Helper.BuildFilePath("aimsunFiles\\results\\test2.csv"), "T2 - TUDIST");
        }

        [TestMethod]
        public void TestExtractTool()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\TestRoadAssignmentxxx.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);
            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\1000.csv"),
                                                              true, true, "1000CarClass", "baseCentroidConfig",
                                                              "Car Class ", "06:00:00:000", "03:00:00:000");
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\Road-Ghost.ang"));
        }

        [TestMethod]
        public void DeleteAimsunObjects()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\PipelineTest1.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);
            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "transitOD", "baseCentroidConfig",
                                                              "Transit Users", "06:00:00:000", "03:00:00:000");
            List<TrafficDemandClassParameters> matrixParameters1 = new List<TrafficDemandClassParameters>()
            {
                new TrafficDemandClassParameters() {NameODMatrix="testOD", InitialTime=360.0, Duration=180.0},
                new TrafficDemandClassParameters() {NameODMatrix="transitOD", InitialTime=360.0, Duration=60.0}
            };
            Utility.RunTrafficDemand("CarAndTransitDemand", matrixParameters1);
            List<TrafficDemandClassParameters> matrixParameters2 = new List<TrafficDemandClassParameters>()
            {
                new TrafficDemandClassParameters() {NameODMatrix="transitOD", InitialTime=360.0, Duration=180.0}
            };
            Utility.RunTrafficDemand("Transit Demand", matrixParameters2);
            List<MatrixName> matrixParameters3 = new List<MatrixName>()
            {
                new MatrixName() { VehicleType="Car Class ", ACostName="Skim T1 - Car Class ACost", AIVTT="Skim T1 - Car Class DIstance AIVTT", AToll="Skim T1 Car Class Toll"},
                new MatrixName() { VehicleType="Transit Users", ACostName="T1 - Transit Users ACost", AIVTT="T1 - Transit Users DIstance AIVTT",  AToll="T1 Transit Users Toll"}
            };
            Utility.RunAssignmentTool("assignment\\roadAssignment.py", "DElCTRoadScenario", "DELCTExp", "CarAndTransitDemand", "PublicTransitTest1", matrixParameters3);

            List<MatrixName> matrixParameters4 = new List<MatrixName>()
            {
                new MatrixName() { VehicleType="Transit Users", ACostName="T2 - TUCOST", AIVTT="T2 - TUDIST", AToll="T2 - TUToll"}
            };
            Utility.RunAssignmentTool("assignment\\roadAssignment.py", "DelTcenario", "DELTExp", "Transit Demand", "PublicTransitTest1", matrixParameters4);
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\DeletedAimsunObjects.ang"));
        }
    }
}
