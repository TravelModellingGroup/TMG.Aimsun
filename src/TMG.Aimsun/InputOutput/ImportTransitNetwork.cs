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

using System;
using XTMF;
using TMG.Input;
using System.IO;

namespace TMG.Aimsun.InputOutput
{
    [ModuleInformation(Description = "Add a transit to the network")]
    public class ImportTransitNetwork: IAimsunTool
    {
        private const string ToolName = "inputOutput/importTransitNetwork.py";

        [SubModelInformation(Required = true, Description = "The network directory is located")]
        public FileLocation NetworkDirectory;

        [SubModelInformation(Required = true, Description = "The Aimsun toolbox directory is located ")]
        public FileLocation ToolboxDirectory;

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
                throw new XTMFRuntimeException(this, "this broke for some reason ");
            }
            return aimsunController.Run(this, Path.Combine(ToolboxDirectory, ToolName),
                JsonParameterBuilder.BuildParameters(writer =>
                {
                    writer.WritePropertyName("ModelDirectory")T
                    writer.WriteValue(NetworkDirectory.GetFilePath());
                }));
        }
    }
}
