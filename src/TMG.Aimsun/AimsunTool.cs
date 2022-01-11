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
    [ModuleInformation(Description = "The aimsun tool to run it takes an aimsun and a list of all the arguments you need to run it.")]
    public class AimSunTool : IAimsunTool
    {
        [RunParameter("Tool Arguments", "", "The arguments of the Aimsun tool you want to run")]
        public string ToolArguments;

        [RunParameter("Tool Name", "", "The namespace of the Aimsun tool you want to run")]
        public string ToolName;

        public string Name
        {
            get;
            set;
        }
        public float Progress
        {
            get;
            set;
        }
        public Tuple<byte, byte, byte> ProgressColour
        {
            get { return null; }
        }
        public bool Execute(ModellerController controller)
        {
            return controller.Run(this, ToolName, ToolArguments);
        }
        public bool RuntimeValidation(ref string error)
        {
            return true;
        }
    }
}
