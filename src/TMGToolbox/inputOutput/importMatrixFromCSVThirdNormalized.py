import csv
from ctypes import ArgumentError
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
from PyANGDTA import *
from PyMacroKernelPlugin import *
from PyMacroToolPlugin import *
from PyMacroAdjustmentPlugin import *
from PyMacroPTPlugin import *
import sys
import os
import warnings as _warn
import traceback as _tb
import subprocess as _sp
# sys.path.append( xtmf_parameters['toolboxPath'] )
from datetime import time


def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    outputNetworkFile = parameters["OutputNetworkFile"]
    _execute(outputNetworkFile, model, console, parameters)

def _execute(outputNetworkFile, inputModel, console, parameters):
    """ 
    Main execute function to run the simulation.
    """
    model = inputModel
    catalog = model.getCatalog()
    geomodel = model.getGeoModel()
    
    fileLocation = str(parameters["ODCSV"])
    thirdNormalized = bool(parameters["ThirdNormalized"])
    header = bool(parameters["IncludesHeader"])
    matrixId = str(parameters["MatrixID"])
    centroidConfigurationId = str(parameters["CentroidConfiguration"])
    vehicleEID = str(parameters["VehicleType"])
    initialTime = str(parameters["InitialTime"])
    durationTime = str(parameters["DurationTime"])

    #find the centroid configuration
    sectionType = model.getType("GKCentroidConfiguration")
    centroidConfiguration = catalog.findObjectByExternalId(centroidConfigurationId, sectionType)
    if centroidConfiguration is None:
        raise Exception(f"The specified centroid configuration '{centroidConfigurationId}' does not exist")
    #check if matrix with given id exists and delete it if it does
    if catalog.findObjectByExternalId(matrixId) != None:
        while catalog.findObjectByExternalId(matrixId) != None:
            obj = catalog.findObjectByExternalId(matrixId)
            cmd = obj.getDelCmd()
            model.getCommander().addCommand(cmd)
            model.getCommander().addCommand(None)

    # Create new matrix
    # set the type of OD matrix if is transit or no
    matrix = None
    if vehicleEID == 'transit':
        matrix = GKSystem.getSystem().newObject("GKPedestrianODMatrix", model)
        print("Adding transit OD matrix")
    else:
        matrix = GKSystem.getSystem().newObject("GKODMatrix", model)
    matrix.setExternalId(matrixId)
    matrix.setName(matrixId)
    matrix.setStoreId( 2 ) # use external ID when storing
    matrix.setStoreType( 0 ) # store in the aimsun file
    matrix.setCentroidConfiguration(centroidConfiguration)
    matrix.setValueToAllCells(0.0)
    matrix.setEnableStore(True)

    if vehicleEID != 'transit':
        sectionType = model.getType("GKVehicle")
        if catalog.findByName(vehicleEID, sectionType) is None:
            raise Exception(f"The specified vehicle type '{vehicleEID}' does not exist")
        else:
            vehicleType = catalog.findByName(vehicleEID, sectionType)
            matrix.setVehicle(vehicleType)
    elif vehicleEID == 'transit':
        sectionType = model.getType("GKPedestrianType")
        if catalog.findByName("Pedestrian", sectionType) is None:
            raise Exception(f"The specified vehicle type Pedestrian does not exist")
        else:
            vehicleType = catalog.findByName("Pedestrian", sectionType)
            matrix.setVehicle(vehicleType)

    initialTime = initialTime.split(":")
    startTime = time(int(initialTime[0]),int(initialTime[1]),int(initialTime[2]),int(initialTime[3]))
    matrix.setFrom(startTime)
    durationTime = durationTime.split(":")
    matrix.setDuration(GKTimeDuration(int(durationTime[0]), int(durationTime[1]), int(durationTime[2])))
    
    #read file and import
    with open(fileLocation) as csvfile:
        reader = csv.reader(csvfile)
        sectionType = model.getType("GKCentroid")
        entranceCentroidType = model.getType("GKPedestrianEntranceCentroid")
        exitCentroidType = model.getType("GKPedestrianExitCentroid")

        if header is True:
            next(reader)
        for line in reader:
            if thirdNormalized is True:
                value = float(line[2])
                # Only create object if OD value is non zero
                if value != 0.0:
                    if vehicleEID == 'transit':
                        originEID = f"ped_entrance_centroid_{line[0]}"
                        destinationEID = f"ped_exit_centroid_{line[1]}"
                        origin = catalog.findObjectByExternalId(originEID, entranceCentroidType)
                        destination = catalog.findObjectByExternalId(destinationEID, exitCentroidType)
                    else:
                        originEID = f"centroid_{line[0]}"
                        destinationEID = f"centroid_{line[1]}"
                        origin = catalog.findObjectByExternalId(originEID, sectionType)
                        destination = catalog.findObjectByExternalId(destinationEID, sectionType)
                    if origin is None:
                        raise Exception(f"The specified centroid '{originEID}' does not exist")
                    if destination is None:
                        raise Exception(f"The specified centroid '{destinationEID}' does not exist")
                    matrix.setTrips(origin, destination, value)
            else:
                raise Exception("Functionality has not been implemented yet")

    # Save add the matrix to the network file
    folderName = "GKCentroidConfiguration::matrices"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    folder.append(matrix)
    # Save the network file
    print("Save Network")
    console.save(outputNetworkFile)
    
def runFromConsole(argv):
    """
    this function is used to run the script from the terminal. Since it 
    needs a csv to pass in the parameters making it to run from _execute() 
    is too difficult and so we will leave this feature as is untouched.
    """
    # Temporary bridge to get inputs from CSV file instead of xtmf
    argv = sys.argv
    if len(argv) < 6:
        print("Incorrect Number of Arguments")
        print("Arguments: -script script.py aimsunNetowrk.ang odMatrix.csv matrixDetails.csv matrixID outputNetworkFile.ang")

    xtmf_parameters = {
        "ODCSV": argv[2],
        "ThirdNormalized": True,
        "IncludesHeader": True,
        "MatrixID": argv[4],
        "CentroidConfiguration": None,
        "VehicleType": None,
        "InitialTime": '08:00:00:000',
        "DurationTime": '01:00:00:000'
    }
    #get the output network file path and name
    outputNetworkFile = argv[5]

    # Use csv file for now for listing the commands
    with open(argv[3]) as csvfile:
        reader = csv.reader(csvfile)
        # skip the header line
        next(reader)
        for line in reader:
            if line[1] == argv[4] and len(line)>=6:
                xtmf_parameters["MatrixID"] = line[1]
                xtmf_parameters["CentroidConfiguration"] = line[2]
                xtmf_parameters["VehicleType"] = line[3]
                xtmf_parameters["InitialTime"] = line[4]
                xtmf_parameters["DurationTime"] = line[5]

    # Start a console
    console = ANGConsole()
    model = None
    # Load a network
    if console.open(argv[1]): 
        model = console.getModel()
        print("open network")
    else:
        console.getLog().addError("Cannot load the network")
        raise Exception("cannot load network")

    #call the _execute function with parameters
    _execute(outputNetworkFile, model, console, xtmf_parameters)

if __name__ == "__main__":
    #function to parse the command line arguments and run network script
    runFromConsole(sys.argv)
