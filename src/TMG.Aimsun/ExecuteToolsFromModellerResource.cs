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

using System;
using XTMF;

namespace TMG.Aimsun
{
    [ModuleInformation(Description = "Module that runs the Aimsun Tools to run in order")]
    public class ExecuteToolsFromModellerResource: ISelfContainedModule
    {
        [SubModelInformation(Required = false, Description = "The tools to run in order.")]
        public IAimsunTool[] Tools;

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
