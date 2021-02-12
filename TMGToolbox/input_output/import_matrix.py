import csv
from PyANGBasic import *
from PyANGKernel import *
from PyANGDTA import *
from PyMacroKernelPlugin import *
from PyMacroToolPlugin import *
from PyMacroAdjustmentPlugin import *
from PyMacroPTPlugin import *
import sys
import os
import warnings as _warn
import sys as _sys
import traceback as _tb
import subprocess as _sp
import sys
import os
sys.path.append( xtmf_parameters['toolboxPath'] )
from common import utilities as _util
import pandas
import PySide2.QtCore as qt

fileLocation = str(xtmf_parameters['matrix_location'])
thirdNormalized = bool(xtmf_parameters['third_normalized'])
header = bool(xtmf_parameters['includes_header'])
matrixId = str(xtmf_parameters['matrix_id'])
centroidConfigurationId = str(xtmf_parameters['centroid_configuration'])
vehicleEID = str(xtmf_parameters['vehicle_type'])
initialTime = str(xtmf_parameters['intial_time'])
durationTime = str(xtmf_parameters['duration_time'])

system = GKSystem.getSystem()
model = system.getActiveModel()
catalog = model.getCatalog()
#find the centroid configuration
if catalog.findObjectByExternalId(centroidConfigurationId) is None:
    raise Exception("The specified centroid configuration '%s' does not exist") %(centroidConfigurationId)
else:
    centroidConfiguration = catalog.findObjectByExternalId(centroidConfigurationId)

#check if matrix with given id exists and delete it if it does
if catalog.findObjectByExternalId(matrixId) is not None:
    while catalog.findObjectByExternalId(matrixId) is not None:
        obj = catalog.findObjectByExternalId(matrixId)
        _util.deleteObject(obj)


# Create new matrix
cmd = model.createNewCmd( model.getType( "GKODMatrix" ))
model.getCommander().addCommand( cmd )
matrix = cmd.createdObject()
matrix.setExternalId(matrixId)
matrix.setStoreId( 2 )
matrix.setStoreType( 0 )
matrix.setCentroidConfiguration(centroidConfiguration)
matrix.setValueToAllCells(0.0)

if catalog.findObjectByExternalId(vehicleEID) is None:
    raise Exception("The specified vehicle type '%s' does not exist") %(vehicleEID)
else:
    vehicleType = catalog.findObjectByExternalId(vehicleEID)
    matrix.setVehicle(vehicleType)

initialTime = initialTime.split(":")
startTime = qt.Qtime(int(initialTime[0]),int(initialTime[1]))
matrix.setFrom(startTime)
durationTime = durationTime.split(":")
matrix.setDuration(GKTimeDuration(int(durationTime[0]), int(durationTime[1])))

##trying to find the "contents" variable. need to figure out whether people will specify demand vehicle, start time, duration. 

#read file and import

with open(filelocation) as csvfile:
    reader = csv.reader(csvfile)
    if header == True:
        reader.next()
    for line in reader:
        if thirdNormalized == True:
            originEID = line[0]
            destinationEID = line[1]
            value = float(line[2])
            if catalog.findObjectByExternalId(originEID) is None:
                raise Exception("The specified centroid '%s' does not exist") %(originEID)
            else:
                origin = catalog.findObjectByExternalId(originEID)
            if catalog.findObjectByExternalId(destinationEID) is None:
                raise Exception("The specified centroid '%s' does not exist") %(destinationEID)
            else:
                destination = catalog.findObjectByExternalId(destinationEID)
            matrix.setTrips(origin, destination, value)
        else:
            raise Exception("Functionality has not been implemented yet")

        