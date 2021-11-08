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
# sys.path.append( xtmf_parameters['toolboxPath'] )
# from common import utilities as _util

def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    outputNetworkFile = parameters["OutputNetworkFile"]
    networkDirectory = parameters["ModelDirectory"]
    _execute(networkDirectory, outputNetworkFile, model, console)

def _execute(networkDirectory, outputNetworkFile, inputModel, console):
    """ 
    Main execute function to run the simulation 
    """
    model = inputModel

    xtmf_parameters = {
        'matrix': 'testOD',
        # placeholder default values
        'start': 6.0 * 60.0,
        'duration': 3.0 * 60.0
    }

    catalog = model.getCatalog()
    system = GKSystem.getSystem()
    # add info from the OD Matrix into a traffic demand item which is used in the model
    trafficDemand = GKSystem.getSystem().newObject("GKTrafficDemand", model)
    scheduleDemandItem = GKScheduleDemandItem()
    sectionType = model.getType("GKODMatrix")
    odMatrix = model.getCatalog().findObjectByExternalId(xtmf_parameters["matrix"], sectionType)
    # TODO make these paramters for the scenario length
    scheduleDemandItem.setFrom(int(xtmf_parameters["start"]*60.0))
    scheduleDemandItem.setDuration(int(xtmf_parameters["duration"]*60.0))
    scheduleDemandItem.setTrafficDemandItem(odMatrix)
    trafficDemand.addToSchedule(scheduleDemandItem)
    # add in the transit demand
    scheduleDemandItem = GKScheduleDemandItem()
    sectionType = model.getType("GKODMatrix")
    odMatrix = model.getCatalog().findObjectByExternalId("transitOD", sectionType)
    # TODO make these paramters for the scenario length
    scheduleDemandItem.setFrom(int(xtmf_parameters["start"]*60.0))
    scheduleDemandItem.setDuration(int(xtmf_parameters["duration"]*60.0))
    scheduleDemandItem.setTrafficDemandItem(odMatrix)
    trafficDemand.addToSchedule(scheduleDemandItem)
    # create a PT plan
    ptPlan = GKSystem.getSystem().newObject("GKPublicLinePlan", model)
    ptPlan.setName("Public Transit Plan")
    ptPlan.setExternalId("publicTransitPlan")
    timeTableType = model.getType("GKPublicLineTimeTable")
    timeTables = model.getCatalog().getObjectsByType(timeTableType)
    for timeTable in iter(timeTables.values()):
        ptPlan.addTimeTable(timeTable)

    # Create the scenario
    cmd = model.createNewCmd( model.getType( "MacroScenario" ))
    model.getCommander().addCommand( cmd )
    scenario = cmd.createdObject()
    scenario.setDemand(trafficDemand)
    scenario.setPublicLinePlan(ptPlan)
    print(f"Create scenario {scenario.getId()}")

    cmd1 = model.createNewCmd( model.getType( "GKPathAssignment" ))
    model.getCommander().addCommand( cmd1 )
    PathAssignment = cmd1.createdObject()

    dataToOutput = scenario.getOutputData()
    dataToOutput.setGenerateSkims(1)

    scenario.setOutputData(dataToOutput)

    experiment = GKSystem.getSystem().newObject( "MacroExperiment", model )
    experiment.setEngine( "FrankWolfe" )
    params = experiment.createParameters()
    params.setMaxIterations ( 50 )
    params.setMaxRelativeGap ( 0.001 )
    params.setFrankWolfeMethod ( CFrankWolfeParams.eNormal )
    experiment.setParameters( params )

    model.getCatalog().add( experiment )
    experiment.setScenario( scenario )
    experiment.setOutputPathAssignment( PathAssignment )

    # Create the PT scenario
    cmd = model.createNewCmd( model.getType( "MacroPTScenario" ))
    model.getCommander().addCommand( cmd )
    ptScenario = cmd.createdObject()
    ptScenario.setDemand(trafficDemand)
    ptScenario.setPublicLinePlan(ptPlan)
    ptOutputData = ptScenario.getOutputData()
    ptOutputData.setGenerateSkims(True)
    ptScenario.setOutputData(ptOutputData)
    print(f"Create transit scenario {ptScenario.getId()}")

    cmd = model.createNewCmd( model.getType( "MacroPTExperiment" ))
    cmd.setScenario( ptScenario )
    cmd.setEngine( "PTFrequencyBased" )
    cmd.setAlgorithm( "AllOrNothing" )
    model.getCommander().addCommand( cmd )
    ptExperiment = cmd.createdObject()
    # # Execute the scenarios
    print("Run road assignment")
    system.executeAction( "execute", experiment, [], "static assignment")
    experiment.getStatsManager().createTrafficState()
    print("Run transit assignment")
    system.executeAction( "execute", ptExperiment, [], "transit assignment")

    # Generate PT Skim Matrices
    skimMatrices = ptExperiment.getOutputData().getSkimMatrices()
    contConfType = model.getType('GKPedestrianCentroidConfiguration')
    ptCentroidConf = model.getCatalog().findObjectByExternalId("ped_baseCentroidConfig", contConfType)
    # Save to the network file
    folderName = "GKCentroidConfiguration::matrices"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    for matrix in skimMatrices:
        m = model.getCatalog().find(matrix)
        # print(m.ensureMatrixData())
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
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    folder.append(scenario)
    folder.append(ptScenario)
    folder.append(experiment)
    folder.append(ptExperiment)
    folderName = "GKModel::trafficDemand"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    folder.append(trafficDemand)
    folderName = "GKModel::publicPlans"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    folder.append(ptPlan)
    # Save the network file
    print("Save network")
    console.save(outputNetworkFile)
    print("Finish Save")
    model.getCommander().addCommand( None )
    print("Done")

def runFromConsole(inputArgs):
    """
    This function takes commands from the terminal, creates a console and model to pass
    to the _execute function
    """
    xtmf_parameters = {
        'matrix': 'testOD',
        # placeholder default values
        'start': 6.0 * 60.0,
        'duration': 3.0 * 60.0
    }
    #extract the data from the args
    inputNetwork = inputArgs[1]
    outputNetworkFile = inputArgs[2]
    
    # Start a console
    console = ANGConsole()

    # generate a model of the input network
    model = None
    # Load a network
    if console.open(inputNetwork): 
        model = console.getModel()
        print("Open network")
    else:
        console.getLog().addError("Cannot load the network")
        raise Exception("Cannot load network")
    catalog = model.getCatalog()
    system = GKSystem.getSystem()
    # add info from the OD Matrix into a traffic demand item which is used in the model
    trafficDemand = GKSystem.getSystem().newObject("GKTrafficDemand", model)
    scheduleDemandItem = GKScheduleDemandItem()
    sectionType = model.getType("GKODMatrix")
    odMatrix = model.getCatalog().findObjectByExternalId(xtmf_parameters["matrix"], sectionType)
    # TODO make these paramters for the scenario length
    scheduleDemandItem.setFrom(int(xtmf_parameters["start"]*60.0))
    scheduleDemandItem.setDuration(int(xtmf_parameters["duration"]*60.0))
    scheduleDemandItem.setTrafficDemandItem(odMatrix)
    trafficDemand.addToSchedule(scheduleDemandItem)
    # add in the transit demand
    scheduleDemandItem = GKScheduleDemandItem()
    sectionType = model.getType("GKODMatrix")
    odMatrix = model.getCatalog().findObjectByExternalId("transitOD", sectionType)
    # TODO make these paramters for the scenario length
    scheduleDemandItem.setFrom(int(xtmf_parameters["start"]*60.0))
    scheduleDemandItem.setDuration(int(xtmf_parameters["duration"]*60.0))
    scheduleDemandItem.setTrafficDemandItem(odMatrix)
    trafficDemand.addToSchedule(scheduleDemandItem)
    # create a PT plan
    ptPlan = GKSystem.getSystem().newObject("GKPublicLinePlan", model)
    ptPlan.setName("Public Transit Plan")
    ptPlan.setExternalId("publicTransitPlan")
    timeTableType = model.getType("GKPublicLineTimeTable")
    timeTables = model.getCatalog().getObjectsByType(timeTableType)
    for timeTable in iter(timeTables.values()):
        ptPlan.addTimeTable(timeTable)

    # Create the scenario
    cmd = model.createNewCmd( model.getType( "MacroScenario" ))
    model.getCommander().addCommand( cmd )
    scenario = cmd.createdObject()
    scenario.setDemand(trafficDemand)
    scenario.setPublicLinePlan(ptPlan)
    print(f"Create scenario {scenario.getId()}")

    cmd1 = model.createNewCmd( model.getType( "GKPathAssignment" ))
    model.getCommander().addCommand( cmd1 )
    PathAssignment = cmd1.createdObject()

    dataToOutput = scenario.getOutputData()
    dataToOutput.setGenerateSkims(1)

    scenario.setOutputData(dataToOutput)

    experiment = GKSystem.getSystem().newObject( "MacroExperiment", model )
    experiment.setEngine( "FrankWolfe" )
    params = experiment.createParameters()
    params.setMaxIterations ( 50 )
    params.setMaxRelativeGap ( 0.001 )
    params.setFrankWolfeMethod ( CFrankWolfeParams.eNormal )
    experiment.setParameters( params )

    model.getCatalog().add( experiment )
    experiment.setScenario( scenario )
    experiment.setOutputPathAssignment( PathAssignment )

    # Create the PT scenario
    cmd = model.createNewCmd( model.getType( "MacroPTScenario" ))
    model.getCommander().addCommand( cmd )
    ptScenario = cmd.createdObject()
    ptScenario.setDemand(trafficDemand)
    ptScenario.setPublicLinePlan(ptPlan)
    ptOutputData = ptScenario.getOutputData()
    ptOutputData.setGenerateSkims(True)
    ptScenario.setOutputData(ptOutputData)
    print(f"Create transit scenario {ptScenario.getId()}")

    cmd = model.createNewCmd( model.getType( "MacroPTExperiment" ))
    cmd.setScenario( ptScenario )
    cmd.setEngine( "PTFrequencyBased" )
    cmd.setAlgorithm( "AllOrNothing" )
    model.getCommander().addCommand( cmd )
    ptExperiment = cmd.createdObject()
    # # Execute the scenarios
    print("Run road assignment")
    system.executeAction( "execute", experiment, [], "static assignment")
    experiment.getStatsManager().createTrafficState()
    print("Run transit assignment")
    system.executeAction( "execute", ptExperiment, [], "transit assignment")

    # Generate PT Skim Matrices
    skimMatrices = ptExperiment.getOutputData().getSkimMatrices()
    contConfType = model.getType('GKPedestrianCentroidConfiguration')
    ptCentroidConf = model.getCatalog().findObjectByExternalId("ped_baseCentroidConfig", contConfType)
    # Save to the network file
    folderName = "GKCentroidConfiguration::matrices"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    for matrix in skimMatrices:
        m = model.getCatalog().find(matrix)
        # print(m.ensureMatrixData())
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
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    folder.append(scenario)
    folder.append(ptScenario)
    folder.append(experiment)
    folder.append(ptExperiment)
    folderName = "GKModel::trafficDemand"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    folder.append(trafficDemand)
    folderName = "GKModel::publicPlans"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    folder.append(ptPlan)
    # Save the network file
    print("Save network")
    console.save(outputNetworkFile)
    print("Finish Save")
    model.getCommander().addCommand( None )
    print("Done")

if __name__ == "__main__":
    # function to parse the command line arguments and run network script
    runFromConsole(sys.argv)
