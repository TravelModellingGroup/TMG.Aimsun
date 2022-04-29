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

def create_traffic_demand(model, system, xtmf_parameters):
    """
    Function which generates and creates the TrafficDemand Data
    # to find a list of all folders qthelp://aimsun.com.aimsun.22.0/doc/UsersManual/ScriptExample1.
    """
    # the name of the folder object we will be creating
    folderName = "GKModel::trafficDemand"
    # add info from the OD Matrix into a traffic demand item which is used in the model
    trafficDemand = system.newObject("GKTrafficDemand", model)

    # build traffic demand folder is required
    CM.build_folder(model, trafficDemand, folderName)
    
    scheduleDemandItem = GKScheduleDemandItem()
    sectionType = model.getType("GKODMatrix") 
   
    for item in xtmf_parameters["demandParams"]:
        odMatrix = model.getCatalog().findObjectByExternalId(item["NameODMatrix"], sectionType)   
        # TODO make these parameters for the scenario length
        scheduleDemandItem.setFrom(int(item["InitialTime"] * 60.0))
        scheduleDemandItem.setDuration(int(item["Duration"] * 60.0))
        scheduleDemandItem.setTrafficDemandItem(odMatrix)
        trafficDemand.addToSchedule(scheduleDemandItem)
    
    trafficDemand.setName(xtmf_parameters["demandName"])
    
def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    # extract the parameters and save to dictionary
    xtmf_parameters = {
        "demandName": parameters["demandObjectName"],
        "demandParams": parameters["demandParams"],
    }
    _execute(model, console, xtmf_parameters)
    
def _execute(inputModel, console, xtmf_parameters):
    """
    Main execute function to run the simulation
    """
    model = inputModel
    system = GKSystem.getSystem()
    catalog = model.getCatalog()

    # delete the existing traffic demand objects
    CM.deleteAimsunObject(model, "GKTrafficDemand", xtmf_parameters["demandName"])

    # method to create the traffic demand object
    create_traffic_demand(model, system, xtmf_parameters)
