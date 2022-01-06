﻿/*
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
    public class TestModuleImportNetwork
    {
        [TestMethod]
        public void ImportNetwork()
        {
            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "inputOutput\\importNetwork.py");
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                //note modeldirectory is going to be renamed and passing in zip file in next PR
                ModelDirectory = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\Frabitztown"),
                NetworkPackageFile = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\Frabitztown.zip")
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
                ModelDirectory = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\Frabitztown")
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
            //build an output file location of where to save the file
            string outputPath = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\test3\\FrabitztownNetwork.ang");
            Helper.Modeller.SaveNetworkModel(null, outputPath);
        }
    }
}
