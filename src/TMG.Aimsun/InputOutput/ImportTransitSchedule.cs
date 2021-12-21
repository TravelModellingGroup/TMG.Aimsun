using System;
using XTMF;
using TMG.Input;
using System.IO;

namespace TMG.Aimsun.InputOutput
{
    [ModuleInformation(Description = "Add a transit schedule to the network.")]
    public class ImportTransitSchedule : IAimsunTool
    {
        private const string ToolName = "InputOutput/importTransitSchedule.py";

        [SubModelInformation(Required = true, Description = "The network directory is located")]
        public FileLocation NetworkDirectory;

        [SubModelInformation(Required = true, Description = "The Aimsun toolbox directory is located")]
        public FileLocation ToolboxDirectory;

        [SubModelInformation(Required = true, Description = "The path of the csv file")]
        public FileLocation ServiceTableCSV;

        [SubModelInformation(Required = true, Description = "The path of the transit file")]
        public FileLocation TransitFile;

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
                    writer.WritePropertyName("ServiceTableCSV");
                    writer.WriteValue(ServiceTableCSV.GetFilePath());
                    writer.WritePropertyName("TransitFile");
                    writer.WriteValue(TransitFile.GetFilePath());
                }));
        }
    }
}
