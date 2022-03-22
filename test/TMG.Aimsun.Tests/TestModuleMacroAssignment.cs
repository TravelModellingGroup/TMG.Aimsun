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
using System.IO;

namespace TMG.Aimsun.Tests
{
    [TestClass]
    public class TestModuleMacroAssignment
    {
        [TestMethod]
        public void RunRoadAssignment()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\FrabitztownNetworkWithOd2.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            Utility.RunAssignmentTool("assignment\\roadAssignment.py", "testOD", 360.0, 180.0, "transitOD");
        }

        [TestMethod]
        public void RunTransitAssignment()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\roadAssignment.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            Utility.RunAssignmentTool("assignment\\transitAssignment.py", "testOD", 360.0, 180.0, "transitOD");
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
        
            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownMatrixList.csv"),
                                                              Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "testOD", "baseCentroidConfig",
                                                              "Car Class ", "06:00:00:000", "03:00:00:000");
            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownMatrixList.csv"),
                                                              Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "transitOD", "baseCentroidConfig",
                                                              "Transit Users", "06:00:00:000", "03:00:00:000");
            Utility.RunAssignmentTool("assignment\\roadAssignment.py", "testOD", 360.0, 180.0, "transitOD");
            // if we don't do this here we won't get out transit matrices
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\road.ang"));
            Helper.Modeller.SwitchModel(null, Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\road.ang"));
            Utility.RunAssignmentTool("assignment\\transitAssignment.py", "testOD", 360.0, 180.0, "transitOD");
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\transit.ang"));
        }
    }
}
