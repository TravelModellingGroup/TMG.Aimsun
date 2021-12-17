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
using System.IO;
using TMG.Input;
using XTMF;

namespace TMG.Aimsun
{
    /// <summary>
    /// Module to save the Aimsun Network.
    /// </summary>
    [ModuleInformation(Description = "Save the active Aimsun project to file")]
    public class SaveProject : IAimsunTool
    {
        public string Name { get; set; }

        public float Progress => 0f;

        public Tuple<byte, byte, byte> ProgressColour => new Tuple<byte, byte, byte>(50, 150, 50);

        public bool Execute(ModellerController aimsunController)
        {
            return aimsunController.SaveNetworkModel(this, Path.GetFullPath(SaveTo));
        }

        [SubModelInformation(Required = true, Description = "Where to save the network")]
        public FileLocation SaveTo;

        public bool RuntimeValidation(ref string error)
        {
            return true;
        }
    }
}
