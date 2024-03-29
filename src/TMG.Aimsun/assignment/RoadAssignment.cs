﻿/*
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

namespace TMG.Aimsun.assignment
{
    [ModuleInformation(Description = "Generate a road assignment")]
    public class RoadAssignment : IAimsunTool
    {
        [ModuleInformation(Description ="SubModule to name the various types of Matrices")]
        public class TrafficClass: IModule
        {
            [RunParameter("Traffic Class Name", "", "Traffic Class Name")]
            public string VehicleType;

            [RunParameter("AIVTT Matrix Name ", "", "Name of the AIVTT Matrix Name")]
            public string AIVTT;

            [RunParameter("Cost Matrix", "", "Name of the Cost Matrix")]
            public string ACostName;

            [RunParameter("Toll Matrix", "", "Name of the Toll Matrix")]
            public string AToll;

            public string Name { get; set; }

            public float Progress => 0f;

            public Tuple<byte, byte, byte> ProgressColour => new Tuple<byte, byte, byte>(120, 25, 100);

            public bool RuntimeValidation(ref string error)
            {
                return true;
            }
        }

        public const string ToolName = "assignment/roadAssignment.py";

        [RunParameter("Name of Scenario", "", "The name of the road assignment scenario")]
        public string ScenarioName;

        [RunParameter("Name of Experiment", "", "The name of the road assignment experiment")]
        public string ExperimentName;

        [RunParameter("Name of Traffic Demand", "", "The name of the Traffic Demand you wish to use for the simulation")]
        public string NameOfTrafficDemand;

        [RunParameter("Name of Public Transit Plan", "", "The name of the public transit plan")]
        public string NameOfPublicTransitPlan;

        [SubModelInformation(Description = "traffic classes", Required = true)]
        public TrafficClass[] TrafficClasses;

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
                    writer.WritePropertyName("scenarioName");
                    writer.WriteValue(ScenarioName);
                    writer.WritePropertyName("experimentName");
                    writer.WriteValue(ExperimentName);
                    writer.WritePropertyName("nameOfTrafficDemand");
                    writer.WriteValue(NameOfTrafficDemand);
                    writer.WritePropertyName("nameOfPublicTransitPlan");
                    writer.WriteValue(NameOfPublicTransitPlan);
                    writer.WritePropertyName("matrixName");
                    writer.WriteStartArray();
                    for (int i = 0; i < TrafficClasses.Length; i++)
                    {
                        writer.WriteStartObject();
                        writer.WritePropertyName("ACostName");
                        writer.WriteValue(TrafficClasses[i].ACostName);
                        writer.WritePropertyName("AIVTT");
                        writer.WriteValue(TrafficClasses[i].AIVTT);
                        writer.WritePropertyName("AToll");
                        writer.WriteValue(TrafficClasses[i].AToll);
                        writer.WritePropertyName("VehicleType");
                        writer.WriteValue(TrafficClasses[i].VehicleType);
                        writer.WriteEndObject();
                    }
                    writer.WriteEndArray();
                }));
        }
    }
}
