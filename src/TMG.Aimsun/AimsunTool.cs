using System;
using XTMF;

namespace TMG.Aimsun
{
    [ModuleInformation(Description = @"The aimsun tool to run it takes an aimsun and a list of all the arguments you 
    need to run it ")]
    public class AimSunTool : IAimsunTool
    {
        [RunParameter("Tool Arguments", "", "The arguments of the Aimsun tool you want to run")]
        public string ToolArguments;

        [RunParameter("Tool Name", "", "The namespace of the Emme tool you want to run")]
        public string ToolName;
        public string Name
        {
            get;
            set;
        }
        public float Progress
        {
            get;
            set;
        }
        public Tuple<byte, byte, byte> ProgressColour
        {
            get { return null; }
        }
        public bool Execute(ModellerController controller)
        {
            return controller.Run(this, ToolName, ToolArguments);
        }
        public bool RuntimeValidation(ref string error)
        {
            return true;
        }
    }
}
