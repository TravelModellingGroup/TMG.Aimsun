
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
	with open(location, 'w') as csvfile:
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
		