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

namespace TMG.Aimsun.Tests
{
    [TestClass]
    public class TestModuleImportTransitNetwork
    {
        [TestMethod]
        public void TestImportTransitNetwork()
        {
            //change the network
            string newNetwork = Helper.BuildFilePath("aimsunFiles\\FrabitztownNetwork.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            string networkPath = Helper.BuildFilePath("inputFiles\\Frabitztown.nwp");
            string modulePath = Helper.BuildModulePath("inputOutput\\importTransitNetwork.py");
            Utility.RunImportNetworkTool(networkPath, modulePath);
        }

        [TestMethod]
        public void TestSaveImportTransitNetwork()
        {
            //change the network
            string newNetwork = Helper.BuildFilePath("aimsunFiles\\FrabitztownNetwork.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);

            string networkPath = Helper.BuildFilePath("inputFiles\\Frabitztown.nwp");
            string modulePath = Helper.BuildModulePath("inputOutput\\importTransitNetwork.py");
            Utility.RunImportNetworkTool(networkPath, modulePath);

            //build an output file location of where to save the file
            string outputPath = Helper.BuildFilePath("aimsunFiles\\test3\\FrabitztownNetworkWithTransit.ang");
            Helper.Modeller.SaveNetworkModel(null, outputPath);
        }
    }
}
