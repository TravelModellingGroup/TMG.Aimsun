/*
    Copyright 2022 Travel Modelling Group, Department of Civil Engineering, University of Toronto

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

namespace TMG.Aimsun.assignment
{
    [ModuleInformation(Description = "Module to generate and build the Aimsun Traffic Demand object")]
    public class CreateTrafficDemand : IAimsunTool
    {
        public const string ToolName = "assignment/createTrafficDemand.py";

        [RunParameter("TrafficDemandName", "", "The new name of the traffic demand object created.")]
        public string demandName;

        [ModuleInformation(Description = "Module to Add the inputs for actually creating multiple traffic demand objects")]
        public class DemandParameters : IModule
        {
            [RunParameter("NameODMatrix", "", "Name of OD Matrix used to create the demand matrix from", Index = 0)]
            public string NameODMatrix;
            [RunParameter("InitialTime", 0.0, "Initial Starting Time in minutes", Index = 1)]
            public double InitialTime;
            [RunParameter("Duration", 0.0, "Duration of demand in minutes", Index = 2)]
            public double Duration;

            public string Name { get; set; }
            public float Progress => 0f;
            public Tuple<byte, byte, byte> ProgressColour => new Tuple<byte, byte, byte>(120, 25, 100);
            public bool RuntimeValidation(ref string error)
            {
                return true;
            }
        };

        [SubModelInformation(Description = "Traffic Demand Matrix Parameters", Required = true)]
        public DemandParameters[] DemandParams;

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
            return aimsunController.Run(this, ToolName,
                JsonParameterBuilder.BuildParameters(writer =>
                {
                    writer.WritePropertyName("demandObjectName");
                    writer.WriteValue(demandName);
                    writer.WritePropertyName("demandParams");
                    writer.WriteStartArray();
                    for (int i = 0; i < DemandParams.Length; i++)
                    {
                        writer.WriteStartObject();
                        writer.WritePropertyName("NameODMatrix");
                        writer.WriteValue(DemandParams[i].NameODMatrix);
                        writer.WritePropertyName("InitialTime");
                        writer.WriteValue(DemandParams[i].InitialTime);
                        writer.WritePropertyName("Duration");
                        writer.WriteValue(DemandParams[i].Duration);
                        writer.WriteEndObject();
                    }
                    writer.WriteEndArray();
                }));
        }
    }
}
