"""
    Copyright 2022 Travel Modelling Group, Department of Civil Engineering, University of Toronto

    This file is part of XTMF.

    XTMF is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    XTMF is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with XTMF.  If not, see <http://www.gnu.org/licenses/>.
"""

# Load in the required libraries
import sys
import os
import time
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
import shlex
import zipfile
import io

def extract_network_packagefile(network_package_file):
    """
    Function which takes a zipped file in this case the networkpackage file and
    returns a ZipFile object which can be further used 
    input: string path to zip file
    return: ZipFile object
    """
    zip_data_file = zipfile.ZipFile(network_package_file, 'r')
    return zip_data_file

def read_datafile(networkZipFileObject, filename):
    """
    Function takes ZipFileObject and filename to open the file and read the lines.
    Returns a list of the extract data for further processing.
    input: ZipFile object 
    input2: string filename
    return: a List of the data in string format 
    """
    fileToOpen = networkZipFileObject.open(filename)
    with io.TextIOWrapper(fileToOpen, encoding="utf-8") as f:
        lines = f.readlines()
        return lines

def loadModel(filepath, console):
    """
    Method responsible to get the aimsun model() object and load the network.
    This method is only utilized and if a simulation is ran from the terminal
    """
    if console.open(filepath):
        model = console.getModel()
        print("Open network")
    else:
        console.getLog().addError("Cannot load the network")
        print("Cannot load the network")
        return -1
    catalog = model.getCatalog()
    geomodel = model.getGeoModel()
    return model, catalog, geomodel

def initializeNodeConnections(listOfNodes):
    nodeConnections = dict()
    for node in listOfNodes:
        nodeConnections[node] = set()
    return nodeConnections

def createTurn(node, fromLink, toLink, model):
    """
    Function to create a turn
    """
    cmd = model.createNewCmd(model.getType( "GKTurning" ))
    cmd.setTurning(fromLink, toLink)
    model.getCommander().addCommand( cmd )
    newTurn = cmd.createdObject()

    newTurn.setExternalId(f"turn_{fromLink.getExternalId()}_{toLink.getExternalId()}")
    newTurn.setNode(node)
    # True for curve turning, false for sorting the turnings
    node.addTurning(newTurn, True, False)

def cacheAllOfTypeByExternalId(typeString, model, catalog):
    cacheDict = dict()
    typeObject = model.getType(typeString)
    objects = catalog.getObjectsByType(typeObject)
    for o in iter(objects.values()):
        externalId = o.getExternalId()
        cacheDict[externalId] = o
    return cacheDict

def cacheNodeConnections(listOfNodes, listOfSections):
    nodeConnections = initializeNodeConnections(listOfNodes)
    for section in listOfSections:
        fromNode = section.getOrigin()
        toNode = section.getDestination()
        if fromNode is not None:
            nodeConnections[fromNode].add(section)
        if toNode is not None:
            nodeConnections[toNode].add(section)
    return nodeConnections

def parseArguments(argv):
    if len(argv) < 3:
        print("Incorrect Number of Arguments")
        print("Arguments: -script script.py blankAimsunProjectFile.ang networkDirectory outputNetworkFile.ang")
    inputModel = argv[1]
    networkDirectory = argv[2]
    outputNetworkFilename = argv[3]
    return inputModel, networkDirectory, outputNetworkFilename
