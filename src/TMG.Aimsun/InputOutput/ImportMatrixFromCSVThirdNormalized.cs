/*
    Copyright 2021 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of MGToolbox for Aimsun.

    MGToolbox for Aimsun is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    MGToolbox for Aimsun is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with MGToolbox for Aimsun.  If not, see <http://www.gnu.org/licenses/>.
*/

using System;
using XTMF;
using TMG.Input;
using System.IO;

namespace TMG.Aimsun.InputOutput
{
    [ModuleInformation(Description = "Import the OD matrixes into the network.")]
    public class ImportMatrixFromCSVThirdNormalized : IAimsunTool
    {
        private const string ToolName = "inputOutput/ImportMatrixFromCSVThirdNormalized.py";

        [SubModelInformation(Required = true, Description = "The file location of the OD CSV file")]
        public FileLocation ODCSV;

        [RunParameter("ThirdNormalized", true, "Boolean value to determine if the matrix is third normalized. Default value is true")]
        public bool ThirdNormalized;

        [RunParameter("IncludesHeader", true, "Boolean value whether to include a header. Default is true")]
        public bool IncludesHeader;

        [RunParameter("MatrixID", "testOD", "Matrix ID default is test OD")]
        public string MatrixID;

        [RunParameter("CentroidConfiguration", "baseCentroidConfig", "String value to write type of centroid configuration")]
        public string CentroidConfiguration;

        [RunParameter("VehicleType", "Car Class ", "String value to determine vehicle type. Default is Car Class")]
        public string VehicleType;

        [RunParameter("InitialTime", "06:00:00:000", "String value of the Initial time")]
        public string InitialTime;

        [RunParameter("DurationTime", "03:00:00:000", "String value of the Duration time")]
        public string DurationTime;
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
                    writer.WritePropertyName("ODCSV");
                    writer.WriteValue(ODCSV.GetFilePath());
                    writer.WritePropertyName("ThirdNormalized");
                    writer.WriteValue(ThirdNormalized);
                    writer.WritePropertyName("IncludesHeader");
                    writer.WriteValue(IncludesHeader);
                    writer.WritePropertyName("MatrixID");
                    writer.WriteValue(MatrixID.ToString());
                    writer.WritePropertyName("CentroidConfiguration");
                    writer.WriteValue(CentroidConfiguration.ToString());
                    writer.WritePropertyName("VehicleType");
                    writer.WriteValue(VehicleType.ToString());
                    writer.WritePropertyName("InitialTime");
                    writer.WriteValue(InitialTime.ToString());
                    writer.WritePropertyName("DurationTime");
                    writer.WriteValue(DurationTime.ToString());
                }));
        }
    }
}
