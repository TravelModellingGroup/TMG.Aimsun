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

def deleteAimsunObject(model, catalog, objectType, matrixId=''):
    """
    Method to delete the various aimsun objects
    duplicated from assignment/commonModule.py
    """
    sectionType = model.getType(objectType)
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            # delete the objects using the getDelCmd()
            if s is not None:
                # check if the name matches. Since it matches we then delete the object 
                if matrixId == s.getName():
                    cmd = s.getDelCmd()
                    model.getCommander().addCommand(cmd)


def extract_network_packagefile(network_package_file):
    """
    Function which takes a zipped file in this case the networkpackage file and
    returns a ZipFile object which can be further used 
    input: string path to zip file
    return: ZipFile object
    """
    zip_data_file = zipfile.ZipFile(network_package_file, 'r')
    return zip_data_file

def verify_file_exits(networkZipFileObject, filename):
    """
    Function which checks if the file exists in the nwp package file and returns
    the boolean value. True if the file exists otherwise False
    input: ZipFile object
    input2: string Filename
    ouptut: boolean of True if exists False otherwise
    """
    # check if file exists in the zip file
    return filename in networkZipFileObject.namelist()

def read_datafile(networkZipFileObject, filename):
    """
    Generator function takes ZipFileObject and filename to open the file and read the lines.
    Returns a list of the extract data for further processing.
    input: ZipFile object 
    input2: string filename
    return: a generator object 
    """
    #open the file 
    fileToOpen = networkZipFileObject.open(filename)
    for f in io.TextIOWrapper(fileToOpen, encoding="utf-8"):
        yield f

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

def getTransitNodesStopsAndLinesFromNWP(networkZipFileObject):
    """
    Function to read the transit.221 file and return the 
    relevant information for the import to Aimsun
    """
    nodes = []
    stops = []
    lines = []
    transitLines = []
    currentlyReadingLine = None
    lineInfo = None
    lineNodes = []
    lineStops = []

    lines = read_datafile(networkZipFileObject, "transit.221")
    next(lines)
    for line in lines:
        if line[0] == 'c' or line[0] == 't':
            if currentlyReadingLine != None:
                nodes.append(lineNodes)
                stops.append(lineStops)
                transitLines.append(lineInfo)
            # Clear all the currently reading item
            currentlyReadingLine = None
            lineInfo = None
            lineNodes = []
            lineStops = []
        elif line[0] == 'a':
            # if there is a line that was being read add it
            if currentlyReadingLine != None:
                nodes.append(lineNodes)
                stops.append(lineStops)
                transitLines.append(lineInfo)
            # set the new line details
            lineInfo = shlex.split(line[1:])
            currentlyReadingLine = lineInfo[0]
            lineNodes = []
            lineStops = []
        # if not comment or heading read into current transit line
        else:
            pathDetails = shlex.split(line)
            # TODO add error if path=yes
            if pathDetails[0] != 'path=no':
                lineNodes.append(pathDetails[0])
                dwt = float(pathDetails[1][5:])
                lineStops.append(dwt)
    # if get to the end of the file add the last line that was read
    if currentlyReadingLine != None:
        nodes.append(lineNodes)
        stops.append(lineStops)
        transitLines.append(lineInfo)
    return nodes, stops, transitLines
