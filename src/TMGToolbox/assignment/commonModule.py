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

def save_network(outputNetworkFile, console, model,  trafficDemand, ptPlan, skimMatrices=None, 
                 scenario=None, ptScenario=None, experiment=None, ptExperiment=None):
    """
    Save to the network file
    """
    folderName = "GKCentroidConfiguration::matrices"
    folder = model.getCreateRootFolder().findFolder(folderName)
    if folder is None:
        folder = GKSystem.getSystem().createFolder(
            model.getCreateRootFolder(), folderName
        ) 
    #if skim matrices exists 
    if skimMatrices != None:
        for matrix in skimMatrices:
            m = model.getCatalog().find(matrix)
            print(m.getName())
            print(m.getTotalTrips())
            m.setExternalId(f"skimMatrix{matrix}")
            m.setStoreId(1)
            m.setStoreType(0)
            m.setCentroidConfiguration(ptCentroidConf)
            m.setEnableStore(True)
            folder.append(m)
            m.storeExternalMatrix()
    folderName = "GKModel::top::scenarios"
    folder = model.getCreateRootFolder().findFolder(folderName)
    if folder is None:
        folder = GKSystem.getSystem().createFolder(
            model.getCreateRootFolder(), folderName
        )
    folder.append(scenario)
    folder.append(ptScenario)
    folder.append(experiment)
    folder.append(ptExperiment)
    folderName = "GKModel::trafficDemand"
    folder = model.getCreateRootFolder().findFolder(folderName)
    if folder is None:
        folder = GKSystem.getSystem().createFolder(
            model.getCreateRootFolder(), folderName
        )
    folder.append(trafficDemand)
    folderName = "GKModel::publicPlans"
    folder = model.getCreateRootFolder().findFolder(folderName)
    if folder is None:
        folder = GKSystem.getSystem().createFolder(
            model.getCreateRootFolder(), folderName
        )
    folder.append(ptPlan)
    # Save the network file
    print("Save network")
    console.save(outputNetworkFile)
    print("Finish Save")
    model.getCommander().addCommand(None)
    print("Done")
