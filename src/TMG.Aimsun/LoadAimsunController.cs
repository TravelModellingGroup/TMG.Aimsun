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
using TMG.Input;
using XTMF;

namespace TMG.Aimsun
{
    [ModuleInformation(Description = "Load the Aimsun Controller")]
    public class LoadAimsunController : IDataSource<ModellerController>, IDisposable
    {
        private ModellerController Data;
        public ModellerController GiveData() => Data;

        [SubModelInformation(Required = true, Description = "The path where aimsun aconsole.exe is located")]
        public FileLocation AimsunPath;

        [SubModelInformation(Required = true, Description = "The path where the starting ang file is located")]
        public FileLocation ProjectFile;

        //dont need this
        public bool Loaded => Data != null;
        public void LoadData()
        {
            if (Data == null)
            {
                lock (this)
                {
                    if (Data == null)
                    {
                        GC.ReRegisterForFinalize(this);
                        string pipeName = Guid.NewGuid().ToString();
                        Data = new ModellerController(this, ProjectFile, pipeName, AimsunPath);
                    }
                }
            }
        }
        public void UnloadData()
        {
            Dispose();
        }

        ~LoadAimsunController()
        {
            Dispose(true);
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool all)
        {
            Data?.Dispose();
            Data = null;
        }

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
    }
}
