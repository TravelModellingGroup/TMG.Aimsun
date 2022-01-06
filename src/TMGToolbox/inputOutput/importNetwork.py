"""
    Copyright 2021 Travel Modelling Group, Department of Civil Engineering, University of Toronto

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
from common import common

# Function to read the base network file
def readFile(networkZipFileObject, filename):
    lines = []
    nodes = []
    links = []
    centroids = []
    centroidSet = set()
    currentlyReading = 'nodes'
    lines = common.read_datafile(networkZipFileObject, filename)
    for line in lines:
        # Check if the line isn't blank
        if len(line)!=0:
            if line[0] == 't':
                currentlyReading = line.split()[1]
            if line[0] == 'a':
                if currentlyReading == 'nodes':
                    if line[1] != "*":
                        nodes.append(line.split())
                    # a* indicates that the node is a centroid
                    if line[1] == "*":
                        splitLine = line.split()
                        centroids.append(splitLine)
                        centroidSet.add(splitLine[1])
                elif currentlyReading == 'links':
                    splitLine = line.split()
                    links.append(splitLine)
    return links, nodes, centroids, centroidSet

# Function to create a node object in Aimsun
def addNode(model, node):
    # Create new node
    cmd = model.createNewCmd(model.getType("GKNode"))
    # Set the position of the node in space
    cmd.setPosition(GKPoint(float(node[2]), float(node[3])))
    model.getCommander().addCommand(cmd)
    newNode = cmd.createdObject()
    # Set the name to the node number
    newNode.setName(f"node{node[1]}")
    newNode.setExternalId(node[1])
    # For performance catalog by external id for searching
    model.getCatalog().catalogObjectExternalId(newNode)
    # For now ignoring the Data1, Data 2, Data 3, and Label columns
    return newNode

def initializeNodeConnections(listOfNodes):
    nodeConnections = dict()
    for node in listOfNodes:
        nodeConnections[node] = set()
    return nodeConnections

def getPointsFromNodes(fromNode, toNode):
    points = GKPoints()
    points.append(fromNode.getPosition())
    points.append(toNode.getPosition())
    return points

# Function to create a link (section) object in Aimsun
def addLink(model, link, allVehicles, roadTypes, layer, nodeConnections):
    # Create the link
    numberOfLanes = max(int(float(link[6])),1)
    # Set the road type
    roadTypeName = f"fd{link[7]}"
    roadType = roadTypes[roadTypeName]
    # newLink.setRoadType(roadType, True)
    # get the points
    nodeType = model.getType("GKNode")
    fromNode = model.getCatalog().findObjectByExternalId(link[1], nodeType)
    toNode = model.getCatalog().findObjectByExternalId(link[2], nodeType)
    points = getPointsFromNodes(fromNode, toNode)
    # lane width
    laneWidth = 2.0
    cmd = model.createNewCmd( model.getType( "GKSection" ))
    cmd.setPoints(numberOfLanes, laneWidth, points, layer)
    cmd.setRoadType(roadType)
    model.getCommander().addCommand( cmd )
    newLink = cmd.createdObject()
    # Set the name to reflect start and end nodes
    name = f"link{link[1]}_{link[2]}"
    newLink.setName(name)
    newLink.setExternalId(name)
    # Set the start and end nodes for the link
    newLink.setOrigin(fromNode)
    newLink.setDestination(toNode)
    # Connect the origin and destination nodes to the link
    nodeConnections[fromNode].add(newLink)
    nodeConnections[toNode].add(newLink)
    # set the allowed mode by link not road type
    newLink.setUseRoadTypeNonAllowedVehicles(False)
    # create list of banned vehicles
    bannedVehicles = []
    allowedModes = link[4]
    for vehicle in allVehicles:
        mode = vehicle.getTransportationMode().getExternalId()
        if mode not in allowedModes:
            bannedVehicles.append(vehicle)
    # set the banned vehicles on the section
    if len(bannedVehicles)>0:
        newLink.setNonAllowedVehicles(bannedVehicles)

    # Add Data 1 which is the user defined cost for use in certain VDFs
    ul1 = float(link[8])
    newLink.setUserDefinedCost(ul1)
    # Add Data 2 which is free flow speed
    freeFlowSpeed = float(link[9])
    newLink.setSpeed(freeFlowSpeed)
    # Add Data 3 which is capacity per lane per hour
    capacityPerLane = float(link[10])
    newLink.setCapacity(float(numberOfLanes) * capacityPerLane)

# Function to add curvature to a link
def addLinkCurvature(link, pointsToAdd):
    # insert points after the origin
    position = 1
    for point in pointsToAdd:
        link.addPointAt(position,point)
        position = position + 1
    # Have aimsun recalculate the geometry with the new points
    # 0 is for straight line segments
    link.setFromPoints(link.getPoints(), 0)
    return link

# Function to read the shapes.251 file and return the applicable links and curvature information
def readShapesFile(model, networkZipFileObject, filename, catalog):
    curves = []
    lines = []
    link = None
    curvaturePoints = []
    sectionType = model.getType("GKSection")
    lines = common.read_datafile(networkZipFileObject, filename)
    for line in lines:
        if len(line)!=0:
            if line[0] == 'r':
                if link is not None and curvaturePoints != []:
                    curves.append((link, curvaturePoints))
                splitLine = line.split()
                fromNode = splitLine[1]
                toNode = splitLine[2]
                link = catalog.findObjectByExternalId(f"link{fromNode}_{toNode}")
                curvaturePoints = []
            if line[0] == "a":
                splitLine = line.split()
                curvaturePoints.append(GKPoint(float(splitLine[4]),float(splitLine[5])))
    return curves

# Function to add the curvature to all applicable links in the network
def addLinkCurvatures(model, networkZipFileObject, filename, catalog):
    curves = readShapesFile(model, networkZipFileObject, filename, catalog)
    for curve in curves:
        addLinkCurvature(curve[0], curve[1])

# Function to read the turns.231
def readTurnsFile(networkZipFileObject, filename):
    turns = []
    lines = common.read_datafile(networkZipFileObject, filename)
    for line in lines:
        if len(line)!=0:
            if line[0] == "a":
                splitLine = line.split()
                turns.append(splitLine)
    return turns

# Function to create a turn
def createTurn(node, fromLink, toLink, model):
    cmd = model.createNewCmd(model.getType( "GKTurning" ))
    cmd.setTurning(fromLink, toLink)
    model.getCommander().addCommand( cmd )
    newTurn = cmd.createdObject()

    newTurn.setExternalId(f"turn_{fromLink.getExternalId()}_{toLink.getExternalId()}")
    newTurn.setNode(node)
    # True for curve turning, false for sorting the turnings
    node.addTurning(newTurn, True, False)

# Function to create the turns from file
def createTurnsFromFile(model, networkZipFileObject, filename, listOfAllNodes, nodeConnections):
    print("Build turns")
    # Copy the list of nodes
    nodes = listOfAllNodes.copy()
    # Make a set for tracking nodes with defined turns
    nodesWithDefinedTurns = set()
    # Try reading the turns from file
    try:
        turns = readTurnsFile(networkZipFileObject, filename)
        nodeType = model.getType("GKNode")
        linkType = model.getType("GKSection")
        catalog = model.getCatalog()
        # cache a node for faster speed if multiple turns at same node
        node = None
        cachedNode = catalog.findObjectByExternalId(turns[0][1], nodeType)
        if cachedNode is not None:
            cachedNodeId = cachedNode.getExternalId()
        for turn in turns:
            if len(turn) >= 5 and turn[4] == "-1":
                # check if the node is the cached node
                nodeId = turn[1]
                if cachedNodeId == nodeId:
                    node = cachedNode
                # If the node is not the cached node, search the catalog
                # Update the cached node to be the new node
                else:
                    # when the node changes sort the turnings in the previously cached node
                    cachedNode.orderTurningsById()
                    node = catalog.findObjectByExternalId(nodeId, nodeType)
                    cachedNode = node
                    cachedNodeId = nodeId
                # Find the links represented by the turn
                # Check that the "at" node was found
                if node is not None:
                    fromLink = None
                    toLink = None
                    fromLinkId = f"link{turn[2]}_{turn[1]}"
                    toLinkId = f"link{turn[1]}_{turn[3]}"
                    connectedLinks = nodeConnections[node]
                    for link in connectedLinks:
                        if link is not None and link.getType() == linkType:
                            testLinkId = link.getExternalId()
                            if testLinkId == fromLinkId:
                                fromLink = link
                            if testLinkId == toLinkId:
                                toLink = link
                    if fromLink is not None and toLink is not None:
                        createTurn(node, fromLink, toLink, model)
                        # Add node to the list of nodes with defined turns
                        nodesWithDefinedTurns.add(node)
                    else:
                        print(f"Could not create turn {turn[1]} {turn[2]} {turn[3]}")
        # sort the turnings by Id for the last node from the loop
        # other nodes run this operation when the cached node changes
        node.orderTurningsById()
        # Remove nodes with defined turns from the full list
        # build turnings for the remaining nodes assuming all allowed
        for node in nodesWithDefinedTurns:
            nodes.remove(node)
        buildTurnings(model, nodes, nodeConnections)
    except FileNotFoundError:
        # If the turns.231 file is not found build in all possible turns
        print("Turns file not found. Build all possible turns")
        buildTurnings(model, nodes, nodeConnections)

# Function to connect links (sections) in Aimsun
def buildTurnings(model, listOfNodes, nodeConnections):
    # Get all of the links and nodes
    # Assume that all links that are connected by nodes have all lanes 
    # turning to each other
    for node in listOfNodes:
        linksIn = []
        linksOut = []
        linkType = model.getType("GKSection")
        connectedLinks = nodeConnections[node]
        for link in connectedLinks:
            origin = link.getOrigin()
            destination = link.getDestination()
            if origin is node:
                linksOut.append(link)
            if destination is node:
                linksIn.append(link)
        for entering in linksIn:
            for exiting in linksOut:
                createTurn(node, entering, exiting, model)

# Function to add all visual objects to the gui network layer
def drawLinksAndNodes(model, layer):
    print("Draw objects to the Geo Model")
    modelToAddTo = model.getGeoModel()
    sectionType = model.getType("GKNode")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            modelToAddTo.add(layer, s)
    sectionType = model.getType("GKSection")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            modelToAddTo.add(layer, s)
    sectionType = model.getType("GKTurning")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            modelToAddTo.add(layer, s)
    sectionType = model.getType("GKBusStop")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            modelToAddTo.add(layer, s)
    sectionType = model.getType("GKCentroid")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            modelToAddTo.add(layer, s)

def createCentroid(model, centroidInfo, centroidConfiguration):
    nodeId = centroidInfo[1]
    xCoord = float(centroidInfo[2])
    yCoord = float(centroidInfo[3])
    # First check if the centroid already exists
    # If yes return centroid
    # If no create new centroid
    sectionType = model.getType("GKCentroid")
    existingCentroid = model.getCatalog().findObjectByExternalId(f"centroid_{nodeId}", sectionType)
    if existingCentroid != None:
        return existingCentroid
    # Create the centroid
    cmd = model.createNewCmd( model.getType( "GKCentroid" ))
    cmd.setData(GKPoint(xCoord, yCoord), centroidConfiguration)
    model.getCommander().addCommand( cmd )
    centroid = cmd.createdObject()
    centroid.setExternalId(f"centroid_{nodeId}")
    centroid.setName(f"centroid_{nodeId}")
    return centroid

# Create centroid configuration
def createCentroidConfiguration(model, name, listOfCentroidInfo):
    print("Create centroid config object")
    cmd = model.createNewCmd(model.getType("GKCentroidConfiguration"))
    model.getCommander().addCommand( cmd )
    centroidConfig = cmd.createdObject()
    centroidConfig.setName(name)
    centroidConfig.setExternalId(name)
    print("Create and add the centroids")
    for centroidInfo in listOfCentroidInfo:
        centroid = createCentroid(model, centroidInfo, centroidConfig)
        # Add the centroid to the centroid configuration if not already included
        if centroidConfig.contains(centroid) is False:
            centroidConfig.addCentroid(centroid)
    # save the centroid configuration
    folderName = "GKModel::centroidsConf"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    folder.append(centroidConfig)
    return centroidConfig

def newCentroidConnection(model, fromNode, toNode, nodeType, centroidType, catalog):
    # First check assuming from node to centroid
    nodeToCentroid = True
    node = catalog.findObjectByExternalId(fromNode, nodeType)
    centroid = catalog.findObjectByExternalId(f"centroid_{toNode}", centroidType)
    # if the node was not found the connection is centroid to node
    if node is None:
        nodeToCentroid = False
        node = catalog.findObjectByExternalId(toNode, nodeType)
        centroid = catalog.findObjectByExternalId(f"centroid_{fromNode}", centroidType)
    cmd = model.createNewCmd(model.getType("GKCenConnection"))
    if nodeToCentroid is True:
        cmd.setData(node, centroid)
    else:
        cmd.setData(centroid, node)
    model.getCommander().addCommand(cmd)
    centroidConnection = cmd.createdObject()
    return centroidConnection

# Method to create the centroid connections
def buildCentroidConnections(model, listOfCentroidConnections):
    nodeType = model.getType("GKNode")
    centroidType = model.getType("GKCentroid")
    catalog = model.getCatalog()
    for connectInfo in listOfCentroidConnections:
        fromNode = connectInfo[1]
        toNode = connectInfo[2]
        newCentroidConnection(model, fromNode, toNode, nodeType, centroidType, catalog)

# Reads the modes file and defines all possible modes on the network
def defineModes(networkZipFileObject, filename, model):
    # Delete the default modes
    sectionType = model.getType("GKVehicle")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            if s != None:
                cmd = s.getDelCmd()
                model.getCommander().addCommand(cmd)
    model.getCommander().addCommand(None)
    # make list of nodes and vehicles created
    modes = []
    vehicleTypes = []

    # read the file and return a list of lines
    lines = common.read_datafile(networkZipFileObject, filename)
    #further processing of data
    for line in lines:
        lineItems = shlex.split(line)
        if len(line)>0 and len(lineItems) >= 3 and line[0] == 'a':
            # Create a mode object
            newMode = GKSystem.getSystem().newObject("GKTransportationMode", model)
            newMode.setName(lineItems[2])
            newMode.setExternalId(lineItems[1])
            modes.append(newMode)
            # Create a vehicle type
            newVeh = GKSystem.getSystem().newObject("GKVehicle", model)
            newVeh.setName(lineItems[2])
            newVeh.setTransportationMode(newMode)
            vehicleTypes.append(newVeh)
    # save vehicle in network file
    folderName = "GKModel::vehicles"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    for veh in vehicleTypes:
        folder.append(veh)
    return modes, vehicleTypes

# Method to read the functions.411 file
def readFunctionsFile(networkZipFileObject, filename):
    vdfNames = []
    lines = common.read_datafile(networkZipFileObject, filename)
    for line in lines:
        if len(line)!=0:
            if line[0] == "a":
                splitLine = line.split()
                vdfNames.append(splitLine[1])
    return vdfNames

def addRoadTypes(model, listOfNames):
    roadTypes = dict()
    # Add a type for dummy links
    # Check if the type already exists
    roadTypeType = model.getType("GKRoadType")
    catalog = model.getCatalog()
    newRoadType = catalog.findObjectByExternalId("dummyLinkRoadType", roadTypeType)
    if newRoadType is None:
        cmd = model.createNewCmd( model.getType( "GKRoadType" ))
        model.getCommander().addCommand( cmd )
        newRoadType = cmd.createdObject()
        newRoadType.setName("dummyLinkRoadType")
        newRoadType.setExternalId("dummyLinkRoadType")
    newRoadType.setDrawMode(3) # hide the dummy links
    # add the road type to the dict
    roadTypes["dummyLinkRoadType"] = newRoadType
    # Add a type for when VDF is 0 links
    # TODO make permanent behaviour for fd0 links
    newRoadType = catalog.findObjectByExternalId("fd0", roadTypeType)
    if newRoadType is None:
        cmd = model.createNewCmd( model.getType( "GKRoadType" ))
        model.getCommander().addCommand( cmd )
        newRoadType = cmd.createdObject()
        newRoadType.setName("fd0")
        newRoadType.setExternalId("fd0")
        newRoadType.setDrawMode(0) # default to road draw
    # add the road type to the dictionary
    roadTypes["fd0"] = newRoadType
    # Repeat the process for all road types in listOfNames
    for name in listOfNames:
        # Check if the type already exists
        newRoadType = catalog.findObjectByExternalId(name, roadTypeType)
        # otherwise make a new type
        if newRoadType is None:
            cmd = model.createNewCmd( model.getType( "GKRoadType" ))
            model.getCommander().addCommand( cmd )
            newRoadType = cmd.createdObject()
            newRoadType.setName(name)
            newRoadType.setExternalId(name)
            newRoadType.setDrawMode(0) # default to road draw mode
        # add the road type to the dictionary
        roadTypes[name] = newRoadType
    return roadTypes

def deleteAllObjectConnections():
    connectionType = model.getType("GKObjectConnection")
    catalog = model.getCatalog()
    allConnections = catalog.getObjectsByType(connectionType)
    if allConnections is not None:
        for connection in iter(allConnections.values()):
            object1 = connection.getOwner()
            object2 = connection.getConnectionObject()
            cmd = GKObjectConnectionDelCmd()
            cmd.init(object1, object2)
            model.getCommander().addCommand(cmd)

def loadModel(filepath, console):
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

def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    #networkDirectory = parameters["ModelDirectory"]
    #we are passing in the zip file to the _execute function
    networkPackage = parameters["NetworkPackageFile"]

    #run the execute function
    _execute(networkPackage, model, console)

def _execute(networkPackage, inputModel, console):
    """ 
    Main execute function to run the simulation 
    """
    overallStartTime = time.perf_counter()
    model = inputModel

    # Import the new network
    print("Import network")
    print("Define modes")
    
    #ZipFile object of the network file do this once
    networkZipFileObject = common.extract_network_packagefile(networkPackage)
    
    #get the modes
    modes = defineModes(networkZipFileObject, "modes.201", model)

    # Cache the vehicle types
    allVehicles=[]
    sectionType = model.getType("GKVehicle")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for vehicle in iter(types.values()):
            allVehicles.append(vehicle)
    print("Define road types")
    roadTypeNames = readFunctionsFile(networkZipFileObject, "functions.411")
    roadTypes = addRoadTypes(model, roadTypeNames)
    print("Read base network data file")
    links, nodes, centroids, centroidSet = readFile(networkZipFileObject, "base.211")
    layer = model.getGeoModel().findLayer("Network")
    nodeStartTime = time.perf_counter()
    print("Add nodes")
    print(f"Number of nodes to import: {len(nodes)}")
    allNodes = []
    counter = 0
    infoStepSize = int(len(nodes)/4)
    for node in nodes:
        counter += 1
        newNode = addNode(model, node)
        allNodes.append(newNode)
        # output the progress of the import
        if (counter % infoStepSize) == 0:
            print(f"{counter} nodes added")
    nodeConnections = initializeNodeConnections(allNodes)
    nodeEndTime = time.perf_counter()
    print(f"Time to import nodes: {nodeEndTime-nodeStartTime}s")
    linkStartTime = time.perf_counter()
    print("Add links")
    print(f"Number of links to import: {len(links)}")
    centroidConnections = []
    counter = 0
    infoStepSize = int(len(links)/4)
    for link in links:
        counter += 1
        # If the from or to nodes are centroids flag as a centroid connector
        if link[1] in centroidSet or link[2] in centroidSet:
            centroidConnections.append(link)
        # If from and to are both nodes, add the link
        else:
            addLink(model, link, allVehicles, roadTypes, layer, nodeConnections)
        # output the progress of the import
        if (counter % infoStepSize) == 0:
            print(f"{counter} links added")
    print("Add curvature to links")
    networkZipFileObject
    addLinkCurvatures(model, networkZipFileObject, "shapes.251", model.getCatalog())
    linkEndTime = time.perf_counter()
    print(f"Time to import links: {linkEndTime-linkStartTime}s")
    turnStartTime = time.perf_counter()
    # Build the turns (connections betweek links)
    createTurnsFromFile(model, networkZipFileObject, "turns.231", allNodes, nodeConnections)
    turnEndTime = time.perf_counter()
    print(f"Time to build turns: {turnEndTime-turnStartTime}s")
    # Add the centroids
    centroidStartTime = time.perf_counter()
    print("Add centroids")
    centroidConfig = createCentroidConfiguration(model, "baseCentroidConfig", centroids)
    buildCentroidConnections(model, centroidConnections)
    centroidEndTime = time.perf_counter()
    print(f"Time to add centroids: {centroidEndTime-centroidStartTime}")
    # Draw all graphical elements to the visible network layer
    drawLinksAndNodes(model, layer)
    print("Finished import")
    overallEndTime = time.perf_counter()
    print(f"Overall runtime: {overallEndTime-overallStartTime}s")
    return console

def saveNetwork(console, model, outputNetworkFile):
    """
    Function to save the network runs from terminal and called only 
    inside runFromConsole
    """
    # Save the network to file
    print("Save network")
    console.save(outputNetworkFile)
    # Reset the Aimsun undo buffer
    model.getCommander().addCommand( None )
    print ("Network saved Successfully")

def runFromConsole(inputArgs):
    """
    This function takes commands from the terminal, creates a console and model to pass
    to the _execute function 
    """
    # Start a console
    console = ANGConsole()
    Network = inputArgs[1]
    networkDirectory = inputArgs[2]
    outputNetworkFile = inputArgs[3]
    # generate a model of the input network
    model, catalog, geomodel = loadModel(Network, console)
    _execute(networkDirectory, model, console) 
    saveNetwork(console, model, outputNetworkFile)

if __name__ == "__main__":
    # function to parse the command line arguments and run network script
    runFromConsole(sys.argv)
