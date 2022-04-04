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
            string newNetwork = Helper.BuildFilePath("aimsunFiles\\transch.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "testOD", "baseCentroidConfig",
                                                              "Car Class ", "06:00:00:000", "03:00:00:000");
            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "transitOD", "baseCentroidConfig",
                                                              "Transit Users", "06:00:00:000", "03:00:00:000");
            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "RoadOD", "baseCentroidConfig",
                                                              "Car Class ", "06:00:00:000", "03:00:00:000");
            Helper.Modeller.SaveNetworkModel(null, Helper.BuildFilePath("aimsunFiles\\helloworld3.ang"));
        }

        [TestMethod]
        public void TestImportMatrixFromCSVThirdNormalizedTransitOD()
        {
            //change the network
            string newNetwork = Helper.BuildFilePath("aimsunFiles\\transch.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            Utility.RunImportMatrixFromCSVThirdNormalizedTool(Helper.BuildFilePath("inputFiles\\frabitztownOd.csv"),
                                                              true, true, "testOD", "baseCentroidConfig",
                                                              "Car Class ", "06:00:00:000", "03:00:00:000");
        }
    }
}
