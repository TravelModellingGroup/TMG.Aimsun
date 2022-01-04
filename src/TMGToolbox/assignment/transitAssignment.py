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
import commonModule as CM

def pt_scenario(model, system, trafficDemand, ptPlan):
    """
    Function to create a PT Scenario
    """
    cmd = model.createNewCmd(model.getType("MacroPTScenario"))
    model.getCommander().addCommand(cmd)
    ptScenario = cmd.createdObject()
    ptScenario.setDemand(trafficDemand)
    ptScenario.setPublicLinePlan(ptPlan)
    ptOutputData = ptScenario.getOutputData()
    ptOutputData.setGenerateSkims(True)
    ptScenario.setOutputData(ptOutputData)
    print(f"Create transit scenario {ptScenario.getId()}")

    cmd = model.createNewCmd(model.getType("MacroPTExperiment"))
    cmd.setScenario(ptScenario)
    cmd.setEngine("PTFrequencyBased")
    cmd.setAlgorithm("AllOrNothing")
    model.getCommander().addCommand(cmd)
    return (ptScenario, cmd)

def experiment_pt_scenario(system, cmd):
    """
    Build experiment for pt scenario and run transit assignment
    """
    ptExperiment = cmd.createdObject()
    # Execute the scenarios
    print("Run transit assignment")
    system.executeAction("execute", ptExperiment, [], "transit assignment")
    return ptExperiment

def get_pt_skim_matrices(model, ptExperiment):
    """
    Generate PT Skim Matrices
    """
    skimMatrices = ptExperiment.getOutputData().getSkimMatrices()
    contConfType = model.getType("GKPedestrianCentroidConfiguration")
    ptCentroidConf = model.getCatalog().findObjectByExternalId(
        "ped_baseCentroidConfig", contConfType
    )
    return skimMatrices

def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    # extract the parameters and save to dictionary
    xtmf_parameters = {
        "autoDemand": parameters["autoDemand"],
        "start": parameters["Start"],
        "duration": parameters["Duration"],
        "transitDemand": parameters["transitDemand"],
    }
    _execute(model, console, xtmf_parameters)

def _execute(inputModel, console, xtmf_parameters):
    """
    Main execute function to run the simulation
    """
    model = inputModel
    system = GKSystem.getSystem()
    # extract the trafficDemand data
    trafficDemand = CM.create_schedule_demand_item(model, system, xtmf_parameters)
    # create a PT Plan
    ptPlan = CM.create_PublicTransit_plan(model)
    # create a PT scenario
    ptScenario, cmd = pt_scenario(model, system, trafficDemand, ptPlan)
    ptExperiment = experiment_pt_scenario(system, cmd)
    # Generate PT Skim Matrices
    skimMatrices = get_pt_skim_matrices(model, ptExperiment)
    
def runFromConsole(inputArgs):
    """
    This function takes commands from the terminal, creates a console and model to pass
    to the _execute function
    """
    # extract the data from the command line arguments
    inputNetwork = inputArgs[1]
    outputNetworkFile = inputArgs[2]
    # extract the parameters and save to dictionary
    xtmf_parameters = {
        "autoDemand": inputArgs[3],
        "start": float(inputArgs[4]),
        "duration": float(inputArgs[5]),
        "transitDemand": inputArgs[6],
    }
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
    # call the _execute() function
    _execute(model, console, xtmf_parameters)

if __name__ == "__main__":
    # function to parse the command line arguments and run network script
    runFromConsole(sys.argv)
