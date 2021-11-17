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

using Microsoft.VisualStudio.TestTools.UnitTesting;
using Newtonsoft.Json;
using System.IO;

namespace TMG.Aimsun.Tests
{
    [TestClass]
    public class TestModuleImportTransitSchedule
    {
        [TestMethod]
        public void TestImportTransitSchedule()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\FrabitztownNetworkWithPedestrians.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);
            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "inputOutput\\importTransitSchedule.py");
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                OutputNetworkFile = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\output\\FrabitztownNetworkWithTransitSchedule.ang"),
                ModelDirectory = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\Frabitztown"),
                ToolboxInputOutputPath = Path.Combine(Helper.TestConfiguration.NetworkFolder, "src\\TMGToolbox\\inputOutput"),
                csvFile = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\frab_service_table.csv"),
                TransitFile = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\Frabitztown\\transit.221 ")
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
        }

        [TestMethod]
        public void TestSaveNetwork()
        {
            //change the network
            string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\FrabitztownNetworkWithPedestrians.ang");
            Helper.Modeller.SwitchModel(null, newNetwork);
            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "inputOutput\\importTransitSchedule.py");
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                OutputNetworkFile = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\output\\FrabitztownNetworkWithTransitSchedule.ang"),
                ModelDirectory = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\Frabitztown"),
                ToolboxInputOutputPath = Path.Combine(Helper.TestConfiguration.NetworkFolder, "src\\TMGToolbox\\inputOutput"),
                csvFile = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\frab_service_table.csv"),
                TransitFile = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\Frabitztown\\transit.221 ")
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
            //build an output file location of where to save the file
            string outputPath = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\test3\\FrabitztownNetworkWithTransitSchedule.ang");
            Helper.Modeller.SaveNetworkModel(null, outputPath);
        }
    }
}
