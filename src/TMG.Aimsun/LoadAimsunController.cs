using System;
using TMG.Input;
using XTMF;

namespace TMG.Aimsun
{
    public class LoadAimsunController : IDataSource<ModellerController>, IDisposable
    {
        [SubModelInformation(Required = true, Description = "The location of the aimsun project file.")]

        private ModellerController Data;
        public ModellerController GiveData() => Data;

        [SubModelInformation(Required = true, Description = "The path where aimsun aconsole.exe is located")]
        public FileLocation AimsunPath;

        [SubModelInformation(Required = true, Description = "The path where the starting ang file is located")]
        public FileLocation ProjectFile;

        //dont need this
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
                        string pipeName = Guid.NewGuid().ToString();
                        Data = new ModellerController(this, ProjectFile, pipeName, AimsunPath);
                    }
                }
            }
        }
        public void UnloadData()
        {
            Dispose();
        }

        ~LoadAimsunController()
        {
            Dispose(true);
        }

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
    }
}
