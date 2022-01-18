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
    public class TestModuleImportMatrixFromCSVThirdNormalized
    {
        [TestMethod]
        public void TestImportMatrixFromCSVThirdNormalizedTestOD()
        {
            //change the network
            string newNetwork = Helper.BuildFilePath("aimsunFiles\\FrabitztownNetworkWithTransitSchedule.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownMatrixList.csv"),
                                                              Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "testOD", "baseCentroidConfig",
                                                              "Car Class ", "06:00:00:000", "03:00:00:000");
        }

        [TestMethod]
        public void TestImportMatrixFromCSVThirdNormalizedTransitOD()
        {
            // This unit test is used to test when transitOD is passed
            // change the network
            string newNetwork = Helper.BuildFilePath("aimsunFiles\\FrabitztownNetworkWithOd.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownMatrixList.csv"),
                                                              Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "transitOD", "ped_baseCentroidConfig",
                                                              "transit", "06:00:00:000", "03:00:00:000");
        }

        [TestMethod]
        public void TestSaveImportMatrixFromCSVThirdNormalizedTestOD()
        {
            //change the network
            string newNetwork = Helper.BuildFilePath("aimsunFiles\\FrabitztownNetworkWithTransitSchedule.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownMatrixList.csv"),
                                                              Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "testOD", "baseCentroidConfig",
                                                              "Car Class ", "06:00:00:000", "03:00:00:000");

            //build an output file location of where to save the file
            string outputPath = Helper.BuildFilePath("aimsunFiles\\test3\\FrabitztownNetworkWithOd.ang");
            Helper.Modeller.SaveNetworkModel(null, outputPath);
        }

        [TestMethod]
        public void TestSaveImportMatrixFromCSVThirdNormalizedTransitOD()
        {
            // This unit test is used to test when transitOD is passed
            // change the network
            string newNetwork = Helper.BuildFilePath("aimsunFiles\\FrabitztownNetworkWithOd.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownMatrixList.csv"),
                                                              Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "transitOD", "ped_baseCentroidConfig",
                                                              "transit", "06:00:00:000", "03:00:00:000");

            //build an output file location of where to save the file
            string outputPath = Helper.BuildFilePath("aimsunFiles\\test3\\FrabitztownNetworkWithOd2.ang");
            Helper.Modeller.SaveNetworkModel(null, outputPath);
        }
    }
}
