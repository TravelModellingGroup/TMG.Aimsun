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
using TMG.Input;
using System.IO;

namespace TMG.Aimsun.InputOutput
{
    [ModuleInformation(Description = "Add a transit schedule to the network.")]
    public class ImportTransitSchedule : IAimsunTool
    {
        private const string ToolName = "InputOutput/importTransitSchedule.py";

        [SubModelInformation(Required = true, Description = "The path to where the network package file (.nwp) is located")]
        public FileLocation NetworkPackageFile;

        [SubModelInformation(Required = true, Description = "The path where the service table (.csv) file is located")]
        public FileLocation ServiceTableCSV;

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
            return aimsunController.Run(this, ToolName,
                JsonParameterBuilder.BuildParameters(writer =>
                {
                    writer.WritePropertyName("NetworkPackageFile");
                    writer.WriteValue(NetworkPackageFile.GetFilePath());
                    writer.WritePropertyName("ServiceTableCSV");
                    writer.WriteValue(ServiceTableCSV.GetFilePath());
                }));
        }
    }
}
