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

fileLocation = str(xtmf_parameters['matrix_location'])
thirdNormalized = bool(xtmf_parameters['third_normalized'])
header = bool(xtmf_parameters['includes_header'])
matrixId = str(xtmf_parameters['matrix_id'])
centroidConfigurationId = str(xtmf_parameters['centroid_configuration'])

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

#read file and import

with open(filelocation) as csvfile:
    reader = csv.reader(csvfile)
    for line in reader:

        