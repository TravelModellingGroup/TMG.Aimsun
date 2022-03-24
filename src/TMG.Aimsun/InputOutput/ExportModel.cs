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
using System.IO;
using TMG.Input;
using XTMF;

namespace TMG.Aimsun.InputOutput
{
    /// <summary>
    /// A tool to export a given matrix to a specified file path
    /// </summary>
    public class ExportModel: IAimsunTool
    {
        public const string ToolName = "InputOutput/exportMatrix.py";

        [SubModelInformation(Required = true, Description = "The filepath location where to save the csv")]
        public FileLocation FilePath;

        [RunParameter("Extension Format", "csv", "The file format eg csv or mtx")]
        public string ExtensionFormat;

        [RunParameter("FileName", "", "The name of the file user wishes to export")]
        public string FileName;

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
                    writer.WritePropertyName("FilePath");
                    writer.WriteValue(FilePath);
                    writer.WritePropertyName("ExtensionFormat");
                    writer.WriteValue(ExtensionFormat);
                    writer.WritePropertyName("FileName");
                    writer.WriteValue(FileName);
                }));
        }

        public bool RuntimeValidation(ref string error)
        {
            return true;
        }
    }
}
