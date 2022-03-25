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
using TMG.Input;
using XTMF;

namespace TMG.Aimsun.InputOutput
{
    /// <summary>
    /// A tool to export a given matrix to a specified file path
    /// </summary>
    [ModuleInformation(Description = "A tool to export a given matrix to a specified file path")]
    public class ExportMatrix: IAimsunTool
    {
        public const string ToolName = "InputOutput/exportMatrix.py";

        [RunParameter("Scenario Type", ScenarioType.RoadAssignment, "The experiment scenario type where the matrix is for")]
        public ScenarioType ExperimentType;

        [SubModelInformation(Required = true, Description = "The filepath location where to save the csv")]
        public FileLocation FilePath;

        [RunParameter("Format", FileType.CSV, "The file format eg csv or txt you wish to save the file as")]
        public FileType Format;

        [RunParameter("Matrix Name", "", "The name of the matrix file user wishes to export")]
        public string MatrixName;

        public enum FileType
        {
            CSV,
            TXT
        }
        private string ReadFormatter() 
        {
            switch(Format)
            {
                case FileType.CSV:
                    return "csv";
                case FileType.TXT:
                    return "txt";
                default:
                    throw new XTMFRuntimeException(this, $"Unknown file type extension {Enum.GetName(typeof(FileType), Format)}");
            }
        }

        public enum ScenarioType
        {
            RoadAssignment,
            TransitAssignment,
        }
        
        /// <summary>
        /// Method to determine if the matrix to export is from a road assignment or a transit 
        /// assignment experiment
        /// </summary>
        /// <returns>A string of the experiment object type</returns>
        /// <exception cref="XTMFRuntimeException"></exception>
        private string ReturnExperimentType()
        {
            switch(ExperimentType)
            {
                case ScenarioType.RoadAssignment:
                    return "MacroExperiment";
                case ScenarioType.TransitAssignment:
                    return "MacroPTExperiment";
                default:
                    throw new XTMFRuntimeException(this, $"Unknown Experiment Type chosen {Enum.GetName(typeof(ScenarioType), Format)}");
            }
        }

        public string Name { get; set; }

        public float Progress => 0f;

        public Tuple<byte, byte, byte> ProgressColour => new Tuple<byte, byte, byte>(50, 150, 50);

        public bool Execute(ModellerController aimsunController)
        {
            if (aimsunController == null)
            {
                throw new XTMFRuntimeException(this, "AimsunController is not properly setup or initalized.");
            }
            return aimsunController.Run(this, ToolName,
                JsonParameterBuilder.BuildParameters(writer =>
                {
                    writer.WritePropertyName("ScenarioType");
                    writer.WriteValue(ReturnExperimentType());
                    writer.WritePropertyName("FilePath");
                    writer.WriteValue(FilePath);
                    writer.WritePropertyName("Format");
                    writer.WriteValue(ReadFormatter());
                    writer.WritePropertyName("MatrixName");
                    writer.WriteValue(MatrixName);
                }));
        }

        public bool RuntimeValidation(ref string error)
        {
            return true;
        }
    }
}
