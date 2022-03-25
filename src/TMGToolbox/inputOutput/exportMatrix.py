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
    Function to export a matrix to a csv or mtx file
    """
    # Full path to the file in where matrices will be written
    matrixFilePath = filePath
    file = open(matrixFilePath, 'w')
    centroids = matrix.getCentroidConfiguration().getCentroidsInOrder()
    print (centroids)
    file.write( '%u %s\n' % (matrix.getId(), matrix.getName())  )
    if matrix.getVehicle() is not None:
        file.write( '%u %s\n' % (matrix.getVehicle().getId(), matrix.getVehicle().getName())  )
    else:
        file.write( '0 None\n' )
    #file.write( '%s\n' % matrix.getFrom().toString() )
    #file.write( '%s\n' % matrix.getDuration().toString() )
    for origin in centroids:
        for destination in centroids:
            trips = matrix.getTrips(origin, destination)
            if trips > 0:
                file.write('%u %u %f\n' % (origin.getId(), destination.getId(), trips))

def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    # extract the parameters and save to dictionary
    xtmf_parameters = {
        "scenarioType": parameters["ScenarioType"],
         "filePath": parameters["FilePath"],
         "format": parameters["Format"],
         "matrixName": parameters["MatrixName"]
    }
    print (parameters)
    _execute(model, console, xtmf_parameters)
    
def _execute(inputModel, console, xtmf_parameters):
    """
    Main execute function to run the simulation
    """
    model = inputModel
    system = GKSystem.getSystem()
    matrix_name = xtmf_parameters["matrixName"]
    
    # get the macro static experiment object. This is the pymacrokernelplugin
    macro_exp_object = model.getType( xtmf_parameters["scenarioType"] ) #"MacroExperiment")
    # returns back a dictionary of {id: pymacrokernel} object
    macro_exp_dict = model.getCatalog().getObjectsByType(macro_exp_object)
    # iterate over the dictionary keys and extract the experiment object
    for exp_id in macro_exp_dict:
        experiment = model.getCatalog().find(exp_id)
        # get the skim matrices of the experiment as a list
        skim_matrix_list = experiment.getOutputData().getSkimMatrices()
        # iterate over the skim matrix list and check if the name is equal to the input filter name
        for item in skim_matrix_list:
            print (item.getId(), item.getName())
            if matrix_name in item.getName():
                # run the export matrix function to export the matrix to the desired path and format
                print ('exporting file')
                name = str(item.getName()).strip().replace(":", "")
                file_path = xtmf_parameters["filePath"] + name + "." + xtmf_parameters["format"]
                exportMatrix(model, console, file_path, item)
    print ('export was successful')