/*
    Copyright 2022 Travel Modelling Group, Department of Civil Engineering, University of Toronto

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

namespace TMG.Aimsun.assignment
{
    [ModuleInformation(Description="Add a transit to the system")]
    public class TransitAssignment : IAimsunTool
    {
        public const string ToolName = "assignment/transitAssignment.py";

        [SubModelInformation(Required = true, Description = "The directory of the network")]
        public FileLocation NetworkDirectory;

        [SubModelInformation(Required = true, Description = "The directory of the Aimsun toolbox")]
        public FileLocation ToolboxDirectory;

        [RunParameter("AutoDemand", "testOD", "The name of the autoDemand")]
        public string AutoDemand;

        [RunParameter("TransitDemand", "transitOD", "The name of the transit demand")]
        public string TransitDemand;

        [RunParameter("StartTime", 360.0, "The start time in minutes")]
        public float StartTime;

        [RunParameter("DurationTime", 180.0, "The duration of time in minutes")]
        public float DurationTime;

        public string Name { get; set; }

        public float Progress { get; set; }

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
                    writer.WritePropertyName("autoDemand");
                    writer.WriteValue(AutoDemand);
                    writer.WritePropertyName("transitDemand");
                    writer.WriteValue(TransitDemand);
                    writer.WritePropertyName("Start");
                    writer.WriteValue(StartTime);
                    writer.WritePropertyName("Duration");
                    writer.WriteValue(DurationTime);
                }));
        }

    }
}
