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
            //initalize the Aimsun module
            Helper.InitializeAimsun();
        }

        [TestMethod]
        public void ConstructAimsunBridge()
        {
            //JsonParameterBuilder.
            string json = JsonConvert.SerializeObject(Helper.TestConfiguration);
            //function that can take string or whatever and generate json and combine two json together
            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "inputOutput\\importNetwork.py");
            Helper.Modeller.Run(null, modulePath, json);
        }

        [TestMethod]
        public void TestJSON()
        {
            string modulePath = "C:\\Users\\sandhela\\source\\repos\\TravelModellingGroup\\TMG.Aimsun\\src\\TMGToolbox\\inputOutput\\importNetwork.py";
            var myData2 = new
            {
                BlankNetwork = "C:\\Users\\sandhela\\source\\repos\\TravelModellingGroup\\TMG.Aimsun\\aimsunFiles\\blankNetwork.ang",
                OutputNetworkFile = "C:\\Users\\sandhela\\source\\repos\\TravelModellingGroup\\TMG.Aimsun\\aimsunFiles\\FrabitztownNetwork.ang",
                NetworkDirectory = "C:\\Users\\sandhela\\source\\repos\\TravelModellingGroup\\TMG.Aimsun\\inputFiles\\Frabitztown",
                AimsunPath = "C:\\Program Files\\Aimsun\\Aimsun Next 20",
                ModulePath = "C:\\Users\\sandhela\\source\\repos\\TravelModellingGroup\\TMG.Aimsun\\src\\TMGToolbox\\inputOutput\\importNetwork.py",
            };
            string jsonData = JsonConvert.SerializeObject(myData2);
            Helper.Modeller.Run(null, modulePath, jsonData);
        }
    }
}
