using System;
using XTMF;
using TMG.Input;
using System.IO;

namespace TMG.Aimsun.InputOutput
{
    [ModuleInformation(Description = "Import the OD matrixes into the network.")]
    public class ImportMatrixFromCSVThirdNormalized : IAimsunTool
    {
        private const string ToolName = "InputOutput/ImportMatrixFromCSVThirdNormalized.py";

        [SubModelInformation(Required = true, Description = "The network directory is located")]
        public FileLocation NetworkDirectory;

        [SubModelInformation(Required = true, Description = "The Aimsun toolbox directory is located")]
        public FileLocation ToolboxDirectory;

        [SubModelInformation(Required = true, Description = "The location of the matrix CSV File")]
        public FileLocation MatrixCSV;

        [SubModelInformation(Required = true, Description = "The location of the OD CSV file")]
        public FileLocation ODCSV;

        [RunParameter("ThirdNormalized", true, "Is the Matrix third normalized default is true")]
        public bool ThirdNormalized;

        [RunParameter("IncludesHeader", true, "Is the header included default is true")]
        public bool IncludesHeader;

        [RunParameter("MatrixID", "testOD", "Matrix ID default is test OD")]
        public string MatrixID;

        [RunParameter("CentroidConfiguration", "baseCentroidConfig", "base centroid")]
        public string CentroidConfiguration;

        [RunParameter("VehicleType", "Car Class ", "vehcile type defualt is car")]
        public string VehicleType;

        [RunParameter("InitialTime", "06:00:00:000", "Initial time")]
        public string InitialTime;

        [RunParameter("DurationTime", "03:00:00:000", "Duration time")]
        public string DurationTime;
        public float Progress
        {
            get;
            set;
        }
        public string Name
        {
            get;
            set;
        }

        public Tuple<byte, byte, byte> ProgressColour => new Tuple<byte, byte, byte>(120, 25, 100);

        public bool RuntimeValidation(ref string error)
        {
            return true;
        }
        public bool Execute(ModellerController aimsunController)
        {
            if (aimsunController == null)
            {
                throw new XTMFRuntimeException(this, "AimsunController is not properly setup or initalized.");
            }
            return aimsunController.Run(this, Path.Combine(ToolboxDirectory, ToolName),
                JsonParameterBuilder.BuildParameters(writer =>
                {
                    writer.WritePropertyName("ModelDirectory");
                    writer.WriteValue(NetworkDirectory.GetFilePath());
                    writer.WritePropertyName("MatrixCSV");
                    writer.WriteValue(MatrixCSV.GetFilePath());
                    writer.WritePropertyName("ODCSV");
                    writer.WriteValue(ODCSV.GetFilePath());
                    writer.WritePropertyName("ThirdNormalized");
                    writer.WriteValue(ThirdNormalized);
                    writer.WritePropertyName("IncludesHeader");
                    writer.WriteValue(IncludesHeader);
                    writer.WritePropertyName("MatrixID");
                    writer.WriteValue(MatrixID.ToString());
                    writer.WritePropertyName("CentroidConfiguration");
                    writer.WriteValue(CentroidConfiguration.ToString());
                    writer.WritePropertyName("VehicleType");
                    writer.WriteValue(VehicleType.ToString());
                    writer.WritePropertyName("InitialTime");
                    writer.WriteValue(InitialTime.ToString());
                    writer.WritePropertyName("DurationTime");
                    writer.WriteValue(DurationTime.ToString());
                }));
        }
    }
}
