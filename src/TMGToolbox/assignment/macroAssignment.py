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

def create_schedule_demand_item(model, system):
    """
    Function which generates and creates the TrafficDemand Data
    """
    xtmf_parameters = {
        'matrix': 'testOD',
        # placeholder default values
        'start': 6.0 * 60.0,
        'duration': 3.0 * 60.0
    }
    # add info from the OD Matrix into a traffic demand item which is used in the model
    trafficDemand = GKSystem.getSystem().newObject("GKTrafficDemand", model)
    scheduleDemandItem = GKScheduleDemandItem()
    sectionType = model.getType("GKODMatrix")
    odMatrix = model.getCatalog().findObjectByExternalId(xtmf_parameters["matrix"], sectionType)
    # TODO make these parameters for the scenario length
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
    return trafficDemand

def create_PT_plan(model):
    """
    Create a PT plan
    """
    ptPlan = GKSystem.getSystem().newObject("GKPublicLinePlan", model)
    ptPlan.setName("Public Transit Plan")
    ptPlan.setExternalId("publicTransitPlan")
    timeTableType = model.getType("GKPublicLineTimeTable")
    timeTables = model.getCatalog().getObjectsByType(timeTableType)
    for timeTable in iter(timeTables.values()):
        ptPlan.addTimeTable(timeTable)

    return ptPlan

def create_scenario(model, trafficDemand, ptPlan):
    """
    Function to create the scenario
    """
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

    return (scenario, PathAssignment)

def create_experiment_for_scenario(model, scenario, PathAssignment):
    """
    Function to create the experiment
    """
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

    return experiment
    

def pt_scenario(model, system, experiment, trafficDemand, ptPlan):
    """
    Function to create a PT Scenario
    """
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
    return (ptScenario, cmd)

def experiment_pt_scenario(system, cmd):
    """
    Build experiment for pt scenario and run transit assignment
    """
    ptExperiment = cmd.createdObject()
    # Execute the scenarios
    print("Run transit assignment")
    system.executeAction( "execute", ptExperiment, [], "transit assignment")
    return ptExperiment

def get_pt_skim_matrices(model, ptExperiment):
    """
    Generate PT Skim Matrices
    """
    skimMatrices = ptExperiment.getOutputData().getSkimMatrices()
    contConfType = model.getType('GKPedestrianCentroidConfiguration')
    ptCentroidConf = model.getCatalog().findObjectByExternalId("ped_baseCentroidConfig", contConfType)
    return skimMatrices

def save_network(outputNetworkFile, console, model, skimMatrices, scenario, ptScenario, experiment, 
                 ptExperiment, trafficDemand, ptPlan):
    """
    Save to the network file
    """
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


def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    outputNetworkFile = parameters["OutputNetworkFile"]
    _execute(outputNetworkFile, model, console)

def _execute(outputNetworkFile, inputModel, console):
    """ 
    Main execute function to run the simulation 
    """
    model = inputModel
    system = GKSystem.getSystem()
    #extract the trafficDemand data
    trafficDemand = create_schedule_demand_item(model, system)
    #create a PT Plan
    ptPlan = create_PT_plan(model)
    # Create the scenario
    scenario, pathAssignment = create_scenario(model, trafficDemand, ptPlan)
    #generate the experiment 
    experiment = create_experiment_for_scenario(model, scenario, pathAssignment)
    # Execute the scenario for road assignment
    print("Run road assignment")
    system.executeAction( "execute", experiment, [], "static assignment")
    experiment.getStatsManager().createTrafficState()
    #create a PT scenario
    ptScenario, cmd = pt_scenario(model, system, experiment, trafficDemand, ptPlan)
    ptExperiment = experiment_pt_scenario(system, cmd)
    # Generate PT Skim Matrices
    skimMatrices = get_pt_skim_matrices(model, ptExperiment)
    # Save the Network
    save_network(outputNetworkFile, console, model, skimMatrices, scenario, ptScenario, experiment, 
                 ptExperiment, trafficDemand, ptPlan)

def runFromConsole(inputArgs):
    """
    This function takes commands from the terminal, creates a console and model to pass
    to the _execute function
    """
    #extract the data from the command line arguments
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
    #call the _execute() function
    _execute(outputNetworkFile, model, console)

if __name__ == "__main__":
    # function to parse the command line arguments and run network script
    runFromConsole(sys.argv)
