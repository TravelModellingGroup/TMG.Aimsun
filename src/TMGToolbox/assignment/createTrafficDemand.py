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

from ast import Param
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
from PyANGDTA import *
from PyMacroKernelPlugin import *
from PyMacroToolPlugin import *
from PyMacroAdjustmentPlugin import *
from PyMacroPTPlugin import *
from PyFrankWolfePlugin import *
import sys
import os

def build_TrafficDemand_Folder(model, trafficDemand):
    folderName = "GKModel::trafficDemand"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder == None:
        folder = GKSystem.getSystem().createFolder(model.getCreateRootFolder(), folderName) 
    folder.append(trafficDemand)

    return folder

def create_traffic_demand(model, system, xtmf_parameters):
    """
    Function which generates and creates the TrafficDemand Data
    # to find a list of all folders qthelp://aimsun.com.aimsun.22.0/doc/UsersManual/ScriptExample1.
    """
    # add info from the OD Matrix into a traffic demand item which is used in the model
    trafficDemand = GKSystem.getSystem().newObject("GKTrafficDemand", model)

    # build or check if the traffic demand folder is available
    build_TrafficDemand_Folder(model, trafficDemand)
    
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
    return trafficDemand
    
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
    
    trafd = create_traffic_demand(model, system, xtmf_parameters)
