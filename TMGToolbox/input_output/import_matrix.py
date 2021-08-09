import csv
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

# Temporary bridge to get inputs from CSV file instead of xtmf
argv = sys.argv
if len(argv) < 4:
    print("Incorrect Number of Arguments")
    print("Arguments: -script script.py aimsunNetowrk.ang odMatrix.csv outputNetworkFile.ang")
xtmf_parameters = {
    'matrix_location': argv[2],
    'third_normalized': True,
    'includes_header': True,
    'matrix_id': 'TestOD',
    'centroid_configuration': 'baseCentroidConfig',
    'vehicle_type': 'Car',
    'initial_time': '08:00:00:000',
    'duration_time': '01:00:00:000'
}

fileLocation = str(xtmf_parameters['matrix_location'])
thirdNormalized = bool(xtmf_parameters['third_normalized'])
header = bool(xtmf_parameters['includes_header'])
matrixId = str(xtmf_parameters['matrix_id'])
centroidConfigurationId = str(xtmf_parameters['centroid_configuration'])
vehicleEID = str(xtmf_parameters['vehicle_type'])
initialTime = str(xtmf_parameters['initial_time'])
durationTime = str(xtmf_parameters['duration_time'])

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

catalog = model.getCatalog()
#find the centroid configuration
sectionType = model.getType("GKCentroidConfiguration")
centroidConfiguration = catalog.findObjectByExternalId(centroidConfigurationId, sectionType)
if centroidConfiguration is None:
    raise Exception(f"The specified centroid configuration '{centroidConfigurationId}' does not exist")

#check if matrix with given id exists and delete it if it does
if catalog.findObjectByExternalId(matrixId) is not None:
    while catalog.findObjectByExternalId(matrixId) is not None:
        obj = catalog.findObjectByExternalId(matrixId)
        cmd = obj.getDelCmd()
        model.getCommander().addCommand(cmd)
        model.getCommander().addCommand(None)


# Create new matrix
matrix = GKSystem.getSystem().newObject("GKODMatrix", model)
matrix.setExternalId(matrixId)
matrix.setStoreId( 2 )
matrix.setStoreType( 0 )
matrix.setCentroidConfiguration(centroidConfiguration)
matrix.setValueToAllCells(0.0)

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

#read file and import

with open(fileLocation) as csvfile:
    reader = csv.reader(csvfile)
    sectionType = model.getType("GKCentroid")
    if header is True:
        next(reader)
    for line in reader:
        if thirdNormalized is True:
            originEID = f"centroid_{line[0]}"
            destinationEID = f"centroid_{line[1]}"
            value = float(line[2])
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
console.save(argv[3])

