# Load in the required libraries
import sys
import time
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
import shlex
from importNetwork import loadModel, initializeNodeConnections

def parseArguments(argv):
    if len(argv) < 3:
        print("Incorrect Number of Arguments")
        print("Arguments: -script script.py blankAimsunProjectFile.ang networkDirectory outputNetworkFile.ang")
    inputModel = argv[1]
    networkDirectory = argv[2]
    outputNetworkFilename = argv[3]
    return inputModel, networkDirectory, outputNetworkFilename

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
        nodeConnections[fromNode].add(section)
        nodeConnections[toNode].add(section)
    return nodeConnections

def main(argv):
    console = ANGConsole()
    inputModel, networkDir, outputNetworkFilename = parseArguments(argv)
    global model
    model, catalog, geomodel = loadModel(inputModel, console)
    networkLayer = geomodel.findLayer("Network")
    nodes = cacheAllOfTypeByExternalId("GKNode", model, catalog)
    sections = cacheAllOfTypeByExternalId("GKSection", model, catalog)
    nodeConnections = cacheNodeConnections(nodes.values(), sections.values())
    

if __name__ == "__main__":
    main(sys.argv)