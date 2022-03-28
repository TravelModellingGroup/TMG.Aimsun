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
from PyMacroKernelPlugin import *
from PyMacroToolPlugin import *
from PyMacroAdjustmentPlugin import *
from PyMacroPTPlugin import *
from PyFrankWolfePlugin import *
import sys
import os


def create_schedule_demand_item(model, system, xtmf_parameters):
    """
    Function which generates and creates the TrafficDemand Data
    TODO need to rename odmatrix into a new variable to make this codebase cleaner
    """
    # add info from the OD Matrix into a traffic demand item which is used in the model
    trafficDemand = GKSystem.getSystem().newObject("GKTrafficDemand", model)
    scheduleDemandItem = GKScheduleDemandItem()
    sectionType = model.getType("GKODMatrix")
    odMatrix = model.getCatalog().findObjectByExternalId(
        xtmf_parameters["autoDemand"], sectionType
    )
    # TODO make these parameters for the scenario length
    scheduleDemandItem.setFrom(int(xtmf_parameters["start"] * 60.0))
    scheduleDemandItem.setDuration(int(xtmf_parameters["duration"] * 60.0))
    scheduleDemandItem.setTrafficDemandItem(odMatrix)
    trafficDemand.addToSchedule(scheduleDemandItem)
    # add in the transit demand
    transitscheduleDemandItem = GKScheduleDemandItem()
    sectionType = model.getType("GKODMatrix")
    transitODMatrix = model.getCatalog().findObjectByExternalId(
        xtmf_parameters["transitDemand"], sectionType
    )
    transitscheduleDemandItem.setFrom(int(xtmf_parameters["start"] * 60.0))
    transitscheduleDemandItem.setDuration(int(xtmf_parameters["duration"] * 60.0))
    transitscheduleDemandItem.setTrafficDemandItem(transitODMatrix)
    trafficDemand.addToSchedule(transitscheduleDemandItem)
    return trafficDemand

def create_PublicTransit_plan(model):
    """
    Create a public transit plan
    """
    ptPlan = GKSystem.getSystem().newObject("GKPublicLinePlan", model)
    ptPlan.setName("Public Transit Plan")
    ptPlan.setExternalId("publicTransitPlan")
    timeTableType = model.getType("GKPublicLineTimeTable")
    timeTables = model.getCatalog().getObjectsByType(timeTableType)
    for timeTable in iter(timeTables.values()):
        ptPlan.addTimeTable(timeTable)
    return ptPlan
