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
import commonModule as CM

def create_scenario(model, trafficDemand, ptPlan):
    """
    Function to create the static road assignmment scenario
    """
    cmd = model.createNewCmd(model.getType("MacroScenario"))
    model.getCommander().addCommand(cmd)
    scenario = cmd.createdObject()
    scenario.setDemand(trafficDemand)
    scenario.setPublicLinePlan(ptPlan)
    print(f"Create scenario {scenario.getId()}")

    cmd1 = model.createNewCmd(model.getType("GKPathAssignment"))
    model.getCommander().addCommand(cmd1)
    PathAssignment = cmd1.createdObject()

    dataToOutput = scenario.getOutputData()
    dataToOutput.setGenerateSkims(1)

    scenario.setOutputData(dataToOutput)

    return (scenario, PathAssignment)

def create_experiment_for_scenario(model, scenario, PathAssignment):
    """
    Function to create the experiment
    """
    #create a new experiment
    macroExperimentCmd = model.createNewCmd(model.getType("MacroExperiment"))
    macroExperimentCmd.setScenario(scenario)
    macroExperimentCmd.setEngine("FrankWolfe")
    model.getCommander().addCommand(macroExperimentCmd)
    experiment = macroExperimentCmd.createdObject()
    params = experiment.getParameters()
    params.setMaxIterations(50)
    params.setMaxRelativeGap(0.001)
    params.setFrankWolfeMethod(CFrankWolfeParams.eNormal)
    #attach the experiment to the scenario
    experiment.setParameters(params)
    model.getCatalog().add(experiment)
    experiment.setScenario(scenario)
    experiment.setOutputPathAssignment(PathAssignment)
    
    return experiment

def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    # extract the parameters and save to dictionary
    xtmf_parameters = {
        "trafficDemandName": parameters["nameOfTrafficDemand"],
        "PublicTransitPlanName": parameters["nameOfPublicTransitPlan"],
        "MatrixNames": parameters["matrixName"]
    }
    _execute(model, console, xtmf_parameters)

def buildOriginalAimsunMatrixName(model, experiment_id, parameters):
    """
    Function to create the original aimsun matrix names which will then be renamed 
    in the renameMatrix() function
    """
    # matrix prefix for road assignment it is Skim
    matrix_name_prefix = "Skim - "
    # iterate over the matrix list and create the aimsun names
    for item in parameters:
        # create the names
        ACostName = matrix_name_prefix + "Cost: " + item["VehicleType"] + " " + str(experiment_id)
        AIVTTName = matrix_name_prefix + "Distance: " + item["VehicleType"] + " " + str(experiment_id)
        # rename the matrices
        CM.renameMatrix(model, AcostName, userName)
        CM.renameMatrix(model, AIVTTNAME, userName)

def _execute(inputModel, console, xtmf_parameters):
    """
    Main execute function to run the simulation
    """
    model = inputModel
    system = GKSystem.getSystem()
    catalog = model.getCatalog()
    # extract the traffic demand object
    trafficDemandObject = catalog.findByName(xtmf_parameters["trafficDemandName"])
    # extract the public transit object
    publicTransitObject = catalog.findByName(xtmf_parameters["PublicTransitPlanName"])
    # Create the scenario
    scenario, pathAssignment = create_scenario(model, trafficDemandObject, publicTransitObject)
    # generate the experiment
    experiment = create_experiment_for_scenario(model, scenario, pathAssignment)
    # Execute the experiment for road assignment
    print("Run road assignment experiment")
    system.executeAction("execute", experiment, [], "static assignment")
    experiment.getStatsManager().createTrafficState()
    # extract the skim matrices 
    skim_matrix_list = experiment.getOutputData().getSkimMatrices()
    # get id of experiment
    experiment_id = experiment.getId()
    # build the original aimsun matrix 
    buildOriginalAimsunMatrixName(model, experiment_id, xtmf_parameters["MatrixNames"])
    print ('experiment ran successfully')
    
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
        # placeholder default values
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
