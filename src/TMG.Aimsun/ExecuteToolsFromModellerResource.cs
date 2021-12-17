using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using XTMF;

namespace TMG.Aimsun
{
    public class ExecuteToolsFromModellerResource: ISelfContainedModule
    {
        [SubModelInformation(Required = false, Description = "The tools to run in order.")]
        public IAimsunTool[] Tools;

        //use i datasource of aimsunmodeller here and this would call loadsimsuncontroller
        //little bit nastier this way not know the type and use this lookup 
        //dummy resource with aimsun controller getting a void pointer
        [SubModelInformation(Required = true, Description = "The name of the resource that has modeller.")]
        public IResource AimsunModeller;
        
        public void Start()
        {
            var modeller = AimsunModeller.AcquireResource<ModellerController>();
            var tools = Tools;
            int i = 0;
            // ReSharper disable AccessToModifiedClosure
            _Progress = () => (((float)i / tools.Length) + tools[i].Progress * (1.0f / tools.Length));
            Status = () => tools[i].ToString();
            for (; i < tools.Length; i++)
            {
                tools[i].Execute(modeller);
            }
            _Progress = () => 0f;
        }

        public string Name
        {
            get;
            set;
        }
        private Func<float> _Progress = () => 0f;
        public float Progress
        {
            get { return _Progress(); }
        }

        public Tuple<byte, byte, byte> ProgressColour
        {
            get { return new Tuple<byte, byte, byte>(50, 150, 50); }
        }

        public bool RuntimeValidation(ref string error)
        {
            if (!AimsunModeller.CheckResourceType<ModellerController>())
            {
                error = "In '" + Name + "' the resource 'EmmeModeller' did not contain an Emme ModellerController!";
                return false;
            }
            return true;
        }

        private Func<string> Status;

        public override string ToString()
        {
            if (Status == null)
            {
                return "Connecting to Aimsun";
            }
            return Status();
        }
    }
}
