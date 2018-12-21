
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


def formatReverseStack():
    eType, eVal, eTb = _sys.exc_info()
    stackList = _tb.extract_tb(eTb)
    msg = "%s: %s\n\n\Stack trace below:" %(eVal.__class__.__name__, str(eVal))
    stackList.reverse()
    for file, line, func, text in stackList:
        msg += "\n  File '%s', line %s, in %s" %(file, line, func)
    return msg


def exportMatrixASCII( location, matrix ):
	with open(location, 'w') as file:
		centroids = matrix.getCentroidConfiguration().getCentroidsInOrder()
		file.write( '%u %s\n' % (matrix.getId(), matrix.getName())  )
		if matrix.getVehicle() != None:
			file.write( '%u %s\n' % (matrix.getVehicle().getId(), matrix.getVehicle().getName())  )
			print  '%u %s\n' % (matrix.getVehicle().getId(), matrix.getVehicle().getName())  
		else:
			file.write( '0 None\n' )
		file.write( '%s\n' % matrix.getFrom().toString( ) )
		file.write( '%s\n' % matrix.getDuration().toString() )
		for origin in centroids:
			for destination in centroids:
				if origin != destination:
					trips = matrix.getTrips( origin, destination )
					if trips > 0:
						file.write( '%u %u %f\n' % (origin.getId(), destination.getId(), trips)  )

def exportMatrixCSV(location, matrix):
	centroids = matrix.getCentroidConfiguration().getCentroidsInOrder()
	with open(location, 'wb') as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(['#',matrix.getId(),matrix.getName()])
		if matrix.getVehicle() != None:
			writer.writerow(['#', matrix.getVehicle().getId(), matrix.getVehicle().getName()])
		else:
			writer.writerow(['#',None,None])
		for origin in centroids:
			for destination in centroids:
				if origin != destination:
					trips = matrix.getTrips( origin, destination )
					if trips > 0:
						writer.writerow([origin.getId(), destination.getId(), trips])


# This script imports matrices from an ASCII file.
#
# This script imports all the matrices in a centroid configuration.
# The matrices must be saved in an ASCII file, one after another and separated
# by a blank line. The format for each matrix must be:
# AIMSUN_ID AIMSUN_NAME
# VEHICLE_ID VEHICLE_NAME
# Initial Time
# Duration
# For each O/D a line with:
# ORIGIN_CENTROID_ID DESTINATION_CENTROID_ID Trips
#
# If no vehicle has been assigned to a matrix the ID must be 0.
# Note that names for vehicles and matrices can contain the space character
def importMatrix( fileName, centroidConf ):
    state = 0
    matrix = None
    for line in open( fileName, "r" ).readlines():
        line = line.strip()
        if len( line ) == 0:
            state = 0
        else:
            if state == 0 :
                state = 1
                # read identifier and name
                matrixId = int( line[:line.index(' ')])
                matrixName = line[line.index(' ')+1:]
                matrix = centroidConf.getModel().getCatalog().find( matrixId )
                if matrix == None or matrix.isA( "GKODMatrix" ) == False:
                    matrix = GKSystem.getSystem().newObject( "GKODMatrix", model )
                    matrix.setName( matrixName )
                    centroidConf.addODMatrix( matrix )
                else:
                    print "New Matrix"
            elif state == 1:
                state = 2
                # read vehicle id and name
                vehId = int( line[:line.index(' ')] )
                vehName = line[line.index(' ')+1:]
                vehicle = centroidConf.getModel().getCatalog().find( vehId )
                if vehicle == None:
                        vehicle = centroidConf.getModel().getCatalog().findByName( vehName )
                if vehicle != None:
                        matrix.setVehicle( vehicle )
            elif state == 2:
                state = 3
                # From Time
                matrix.setFrom( QTime.fromString( line, Qt.ISODate ) )
            elif state == 3:
                state = 4
                # Duration
                matrix.setDuration( GKTimeDuration.fromString( line ) )
            elif state == 4:
                # Trips
                tokens = line.split( " " )
                if len( tokens ) == 3:
                    fromCentroid = centroidConf.getModel().getCatalog().find( int(tokens[0]) )
                    toCentroid = centroidConf.getModel().getCatalog().find( int(tokens[1]) )
                    trips = float(tokens[2])
                    # Set the value if the section is valid
                    if fromCentroid != None and toCentroid != None:
                        matrix.setTrips( fromCentroid, toCentroid, trips )
    matrix.setStatus( GKObject.eModified )
    model.getCommander().addCommand( None )

def deleteObject(object):
    cmd = object.getDelCmd()
    model.getCommander().addCommand( cmd )


