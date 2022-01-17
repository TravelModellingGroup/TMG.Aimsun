using Newtonsoft.Json;
using System.IO;

namespace TMG.Aimsun.Tests
{
    public static class Utility
    {
        public static void ImportNetwork(string nwpFile, string toolPath)
        {
            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, toolPath);
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                NetworkPackageFile = nwpFile
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
        }

        public static void TestImportPedestrians()
        {
            //change the network
            //string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\FrabitztownNetworkWithTransit.ang");
            //Helper.Modeller.SwitchModel(null, newNetwork);
            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "inputOutput\\importPedestrians.py");
            string jsonParameters = JsonConvert.SerializeObject(new
            {
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
        }

        public static void TestImportTransitSchedule(string nwpFile, string serviceTablePath)
        {
            //change the network
            //string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\FrabitztownNetworkWithPedestrians.ang");
            //Helper.Modeller.SwitchModel(null, newNetwork);
            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "inputOutput\\importTransitSchedule.py");
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                NetworkPackageFile = nwpFile,
                ServiceTableCSV = serviceTablePath
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
        }

        public static void TestImportMatrixFromCSVThirdNormalizedTestOD(string matrixID, string transitType)
        {
            //change the network
            //string newNetwork = Path.Combine(Helper.TestConfiguration.NetworkFolder, "aimsunFiles\\FrabitztownNetworkWithTransitSchedule.ang");
            //Helper.Modeller.SwitchModel(null, newNetwork);
            string modulePath = Path.Combine(Helper.TestConfiguration.ModulePath, "inputOutput\\importMatrixFromCSVThirdNormalized.py");
            string jsonParameters = JsonConvert.SerializeObject(new
            {
                MatrixCSV = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\frabitztownMatrixList.csv"),
                ODCSV = Path.Combine(Helper.TestConfiguration.NetworkFolder, "inputFiles\\frabitztownOd.csv"),
                ThirdNormalized = true,
                IncludesHeader = true,
                MatrixID = matrixID,
                CentroidConfiguration = "baseCentroidConfig",
                VehicleType = transitType,
                InitialTime = "06:00:00:000",
                DurationTime = "03:00:00:000"
            });
            Helper.Modeller.Run(null, modulePath, jsonParameters);
        }


    }
}
