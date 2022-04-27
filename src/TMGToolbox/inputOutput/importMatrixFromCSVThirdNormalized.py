"""
    Copyright 2021 Travel Modelling Group, Department of Civil Engineering, University of Toronto

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

import sys
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
from datetime import time
from common.common import loadModel, deleteAimsunObject

def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    _execute(model, console, parameters)

def find_centroid_configuration(model, catalog, centroidConfigurationId, matrixId):
    """
    Function to find the centroid configuration
    """
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

    return centroidConfiguration

def build_matrix(model, catalog, vehicleEID, matrixId, centroidConfiguration, initialTime, durationTime):
    """
    function to build and create a new matrix
    """
    matrix = GKSystem.getSystem().newObject("GKODMatrix", model)
    matrix.setExternalId(matrixId)
    matrix.setName(matrixId)
    matrix.setStoreId( 2 ) # use external ID when storing
    matrix.setStoreType( 0 ) # store in the aimsun file
    matrix.setCentroidConfiguration(centroidConfiguration)
    matrix.setValueToAllCells(0.0)
    matrix.setEnableStore(True)
    
    sectionType = model.getType("GKVehicle")
    if catalog.findByName(vehicleEID, sectionType) is None:
        raise Exception(f"The specified vehicle type '{vehicleEID}' does not exist")
    else:
        vehicleType = catalog.findByName(vehicleEID, sectionType)
        matrix.setVehicle(vehicleType)

    initialTime = initialTime.split(":")
    startTime = time(int(initialTime[0]),int(initialTime[1]),int(initialTime[2]),int(initialTime[3]))
    matrix.setFrom(startTime)
    durationTime = durationTime.split(":")
    matrix.setDuration(GKTimeDuration(int(durationTime[0]), int(durationTime[1]), int(durationTime[2])))
    
    return matrix

def extract_OD_Data(fileLocation, model, catalog, header, thirdNormalized, vehicleEID, matrix):
    """
    Function to extract the data from the OD csv file 
    """
    #read file and import
    with open(fileLocation) as csvfile:
        reader = csv.reader(csvfile)
        sectionType = model.getType("GKCentroid")
        entranceCentroidType = model.getType("GKCenConnection")
        exitCentroidType = model.getType("GKCenConnection")

        if header is True:
            next(reader)
        for line in reader:
            if thirdNormalized is True:
                value = float(line[2])
                # Only create object if OD value is non zero
                if value != 0.0:
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

def _execute(model, console, parameters):
    """ 
    Main execute function to run the simulation.
    """
    catalog = model.getCatalog()
    #extract the json parameters
    fileLocation = str(parameters["ODCSV"])
    thirdNormalized = bool(parameters["ThirdNormalized"])
    header = bool(parameters["IncludesHeader"])
    matrixId = str(parameters["MatrixID"])
    centroidConfigurationId = str(parameters["CentroidConfiguration"])
    vehicleEID = str(parameters["VehicleType"])
    initialTime = str(parameters["InitialTime"])
    durationTime = str(parameters["DurationTime"])
    
    # check and delete all pre-existing Aimsun objects
    deleteAimsunObject(model, catalog, "GKODMatrix", matrixId)

    # find the centroid configuration
    centroidConfiguration = find_centroid_configuration(model, catalog, centroidConfigurationId, matrixId)

    # Create new matrix
    matrix = build_matrix(model, catalog, vehicleEID, matrixId, centroidConfiguration, initialTime, durationTime)

    # extract data from the OD Data csv file read file and import
    extract_OD_Data(fileLocation, model, catalog, header, thirdNormalized, vehicleEID, matrix)
    
    # Save add the matrix to the network file
    folderName = "GKCentroidConfiguration::matrices"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    folder.append(matrix)

    return console

def saveNetwork(console, model, outputNetworkFile):
    """
    Function to save the network runs from terminal and called only 
    inside runFromConsole
    """
    # Save the network to file
    print("Save network")
    console.save(outputNetworkFile)
    # Reset the Aimsun undo buffer
    model.getCommander().addCommand( None )
    print ("Network saved Successfully")
    
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
    # load a network
    model, catalog, geomodel = loadModel(Network, console)
    
    #call the _execute function with parameters
    _execute(model, console, xtmf_parameters)
    saveNetwork(console, model, outputNetworkFile)

if __name__ == "__main__":
    #function to parse the command line arguments and run network script
    runFromConsole(sys.argv)
