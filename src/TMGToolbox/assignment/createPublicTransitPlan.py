"""
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
"""

from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
from PyANGDTA import *
import commonModule as CM

def create_PublicTransit_plan(model, system, xtmf_parameters):
    """
    Method to create a public transit plan used in the scenarios
    """
    ptPlan = system.newObject("GKPublicLinePlan", model)
    newNameOfPlan = xtmf_parameters["nameOfPlan"]
    # set the name of the public transit object
    ptPlan.setName(newNameOfPlan)
    # remove all whitespaces to create the external name
    externalIdPlan = newNameOfPlan.replace(" ", "")
    ptPlan.setExternalId(externalIdPlan)
    # add all the timetables to the plan
    timeTableType = model.getType("GKPublicLineTimeTable")
    timeTables = model.getCatalog().getObjectsByType(timeTableType)
    for timeTable in iter(timeTables.values()):
        ptPlan.addTimeTable(timeTable)

    # name of the public plans folder we need to create
    folderName = "GKModel::publicPlans"
    # add object to public transit folder
    CM.build_folder(model, ptPlan, folderName)
    
def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    # extract the parameters and save to dictionary
    xtmf_parameters = {
        "nameOfPlan": parameters["NameOfPlan"]
    }
    _execute(model, console, xtmf_parameters)
    
def _execute(inputModel, console, xtmf_parameters):
    """
    Main execute function to run the simulation
    """
    model = inputModel 
    system = GKSystem.getSystem()
    
    create_PublicTransit_plan(model, system, xtmf_parameters)
    