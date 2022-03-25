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
import os

def exportMatrix(model, console, filePath, matrix):
    """
    Function to export a matrix to a csv or txt file
    """
    # Full path to the file in where matrices will be written
    matrixFilePath = filePath
    #open the file 
    with open(matrixFilePath, 'w') as matfile:
        centroids = matrix.getCentroidConfiguration().getCentroidsInOrder()
        print (centroids)
        matfile.write('%s,%s,%s\n' %("origin", "destination", "value"))
        for origin in centroids:
            for destination in centroids:
                trips = matrix.getTrips(origin, destination)
                if trips > 0:
                    matfile.write('%u,%u,%f\n' %(origin.getId(), destination.getId(), trips))
        matfile.close()

def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    # extract the parameters and save to dictionary
    xtmf_parameters = {
         "filePath": parameters["FilePath"],
         "matrixName": parameters["MatrixName"]
    }
    print (parameters)
    _execute(model, console, xtmf_parameters)
    
def _execute(inputModel, console, xtmf_parameters):
    """
    Main execute function to run the simulation
    """
    model = inputModel
    matrix_name = xtmf_parameters["matrixName"]
    file_path = xtmf_parameters["filePath"]
    # find the matrix object based by string name
    experiment_matrix = model.getCatalog().findByName(matrix_name)
    # run the export matrix function to save the file
    exportMatrix(model, console, file_path, experiment_matrix)

    print ('export of matrix was successful')
