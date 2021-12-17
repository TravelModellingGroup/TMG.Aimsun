using System;
using XTMF;
using TMG.Input;

namespace TMG.Aimsun.InputOutput
{
    [ModuleInformation(Description = "Add a pedestrian to the network")]
    public class ImportPedestrian: IAimsunTool, IDataSource<ModellerController>, IDisposable
    {
        [SubModelInformation(Required = true, Description = "The location of the aimsun project file.")]

        private ModellerController Data;
        public ModellerController GiveData() => Data;


        string pipeName = Guid.NewGuid().ToString();
        string aimsunPath = "C:\\Program Files\\Aimsun\\Aimsun Next 22";
        string projectFile = "C:\\Users\\sandhela\\source\\repos\\TravelModellingGroup\\TMG.Aimsun\\aimsunFiles\\blankNetworkWithVdfs.ang";

        public bool Loaded => Data != null;
        public void LoadData()
        {
            if (Data == null)
            {
                lock (this)
                {
                    if (Data == null)
                    {
                        GC.ReRegisterForFinalize(this);
                        Data = new ModellerController(this, projectFile, pipeName, aimsunPath);
                    }
                }
            }
        }
        public void UnloadData()
        {
            Dispose();
        }

        //~ModellerControllerDataSource()
        //{
        //    Dispose(true);
        //}

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool all)
        {
            Data?.Dispose();
            Data = null;
        }

        private const string ToolName = "Import Aimsun Network";

        [RunParameter("OutputNetworkFile", "", "The path with filename to save the network as an ang file")]
        public FileLocation OutputNetworkFile;

        [RunParameter("ModelDirectory", "", "The filepath where the network files exist")]
        public FileLocation ModelDirectory;

        [RunParameter("ToolboxInputOutputPath", "", "The filepath to where the Aimsun toolbox exists")]
        public FileLocation ToolboxInputOutputPath;

        [RunParameter("Result", "999", "Matrix")]
        public string Result;

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
                throw new XTMFRuntimeException(this, "this broke for osme reason ");
            }
            aimsunController.Run(this, ToolName, Result);

            return true;
        }
    }
}
