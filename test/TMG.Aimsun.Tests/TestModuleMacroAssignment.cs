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
        public void TestEntireSystem()
        {
            //UnitTest to test the entire system and run a pipeline of all the tools starting with a blank

            //the json parameters to pass to all the tools 
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                NetworkPackageFile = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\Frabitztown.nwp"),
                ServiceTableCSV = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\frab_service_table.csv"),
                MatrixCSV = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\frabitztownMatrixList.csv"),
                ODCSV = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\frabitztownOd.csv"),
                ThirdNormalized = true,
                IncludesHeader = true,
                MatrixID = "testOD",
                CentroidConfiguration = "baseCentroidConfig",
                VehicleType = "Car Class ",
                InitialTime = "06:00:00:000",
                DurationTime = "03:00:00:000",
                autoDemand = "testOD",
                Start = 360.0,
                Duration = 180.0,
                transitDemand = "transitOD"

            });
            //the json parameter to pass specificlly to the second instance of importmatrix when it builds the 
            //transit section
            string jsonParameters2 = JsonConvert.SerializeObject(new 
            {
                ODCSV = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\frabitztownOd2.csv"),
                ThirdNormalized = true,
                IncludesHeader = true,
                MatrixID = "transitOD",
                CentroidConfiguration = "ped_baseCentroidConfig",
                VehicleType = "transit",
                InitialTime = "06:00:00:000",
                DurationTime = "03:00:00:000"
            });

            //List of all the tools in the sequential order in which we wish to run them.
            List<string> TitleArray = new List<string>{ "inputOutput\\importNetwork.py", "inputOutput\\importPedestrians.py", 
                                                        "inputOutput\\importTransitNetwork.py", "inputOutput\\importTransitSchedule.py",
                                                        "inputOutput\\importMatrixFromCSVThirdNormalized.py", 
                                                        "inputOutput\\importMatrixFromCSVThirdNormalized.py",
                                                        "assignment\\roadAssignment.py", "assignment\\transitAssignment.py"};
            
            //counter to keep track in case specific json paramters need to be passed 
            int counter = 0;
            //iterate over each string in the titlearray generate a modulepath and run the tool with the 
            //json parameters of interest and incrase counter
            foreach (string title in TitleArray)
            {
                counter+=1;
                string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, title);
                if (counter == 6)
                {
                    Helper.Modeller.Run(null, modulePath, jsonParameters2);
                }
                else
                {
                    Helper.Modeller.Run(null, modulePath, jsonParameters);
                }
            }
        }
    }
}
