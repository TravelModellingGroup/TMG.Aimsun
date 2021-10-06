# This script reads the network files from EMME and builds
# a road and transit network in Aimsun

# Load in the required libraries
import sys
import time
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
import shlex

# Function to read the base network file
def readFile(filename):
    lines = []
    nodes = []
    links = []
    centroids = []
    centroidSet = set()
    currentlyReading = 'nodes'
    with open(filename, 'r') as f:
        lines = f.readlines()
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
def addNode(node):
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
def addLink(link, allVehicles, roadTypes, layer, nodeConnections):
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
    # originConnection = GKSystem.getSystem().newObject("GKObjectConnection", model)
    # originConnection.setOwner(fromNode)
    # originConnection.setConnectionObject(newLink)
    # fromNode.addConnection(originConnection)
    # destinationConnection = GKSystem.getSystem().newObject("GKObjectConnection", model)
    # destinationConnection.setOwner(toNode)
    # destinationConnection.setConnectionObject(newLink)
    # toNode.addConnection(destinationConnection)
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
def readShapesFile(filename, catalog):
    curves = []
    lines = []
    link = None
    curvaturePoints = []
    sectionType = model.getType("GKSection")
    with open(filename, 'r') as f:
        lines = f.readlines()
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
def addLinkCurvatures(filename, catalog):
    curves = readShapesFile(filename, catalog)
    for curve in curves:
        addLinkCurvature(curve[0], curve[1])

# Function to read the turns.231
def readTurnsFile(filename):
    turns = []
    with open(filename, "r") as f:
        lines = f.readlines()
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
def createTurnsFromFile(filename, listOfAllNodes, nodeConnections):
    print("Build turns")
    # Copy the list of nodes
    nodes = listOfAllNodes.copy()
    # Make a set for tracking nodes with defined turns
    nodesWithDefinedTurns = set()
    # Try reading the turns from file
    try:
        turns = readTurnsFile(filename)
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
        buildTurnings(nodes, nodeConnections)
    except FileNotFoundError:
        # If the turns.231 file is not found build in all possible turns
        print("Turns file not found. Build all possible turns")
        buildTurnings(nodes, nodeConnections)

# Function to connect links (sections) in Aimsun
def buildTurnings(listOfNodes, nodeConnections):
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
def drawLinksAndNodes(layer):
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

def createCentroid(centroidInfo, centroidConfiguration):
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
def createCentroidConfiguration(name, listOfCentroidInfo):
    print("Create centroid config object")
    cmd = model.createNewCmd(model.getType("GKCentroidConfiguration"))
    model.getCommander().addCommand( cmd )
    centroidConfig = cmd.createdObject()
    centroidConfig.setName(name)
    centroidConfig.setExternalId(name)
    print("Create and add the centroids")
    for centroidInfo in listOfCentroidInfo:
        centroid = createCentroid(centroidInfo, centroidConfig)
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

def newCentroidConnection(fromNode, toNode, nodeType, centroidType, catalog):
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
def buildCentroidConnections(listOfCentroidConnections):
    nodeType = model.getType("GKNode")
    centroidType = model.getType("GKCentroid")
    catalog = model.getCatalog()
    for connectInfo in listOfCentroidConnections:
        fromNode = connectInfo[1]
        toNode = connectInfo[2]
        newCentroidConnection(fromNode, toNode, nodeType, centroidType, catalog)

# Create a pedestrian layer and return the object
def createPedestrianLayer():
    cmd = model.createNewCmd( model.getType( 'GKLayer' ) )
    model.getCommander().addCommand( cmd )
    ped_layer = cmd.createdObject()
	# Set Pedestrian Layer attributes
    ped_layer.setName( 'Pedestrians Layer' )
    ped_layer.setInternalName( 'Pedestrians_Layer' )
    ped_layer.setLevel( 150 )
    ped_layer.setAllowObjectsEdition( True )
    ped_layer.setStatus( GKObject.eModified )
    return ped_layer

# Creates the pedestrian centroid configuration folder in the location aimsun is expecting
def createPedestrianCentroidConfigFolder():
    folderName = 'GKModel::pedestrianCentroidsConfiguration'
    folder = model.getCreateRootFolder().findFolder(folderName)
    if folder == None:
        folder = GKSystem.getSystem().createFolder(model.getCreateRootFolder(), folderName)
    return folder

# creates a pedestrian centroid configuration
def createPedestrianCentroidConfig():
    folder = createPedestrianCentroidConfigFolder()
    pedestrianCentroidConfig = GKSystem.getSystem().newObject( 'GKPedestrianCentroidConfiguration', model )
    pedestrianCentroidConfig.setName("Pedestrian Centroid Configuration")
    pedestrianCentroidConfig.setExternalId("ped_baseCentroidConfig")
    pedestrianCentroidConfig.setStatus(GKObject.eModified)
    pedestrianCentroidConfig.activate()
    folder.append(pedestrianCentroidConfig)
    return pedestrianCentroidConfig

def createSquarePedArea(centre, size, geomodel, layer, name):
    x = centre.x
    y = centre.y
    pedArea = GKSystem.getSystem().newObject("GKPedestrianArea", model)
    pedArea.setName(f"pedArea_{name}")
    pedArea.setExternalId(f"pedArea_{name}")
    pedArea.addPoint(GKPoint(x-size,y+size))
    pedArea.addPoint(GKPoint(x+size,y+size))
    pedArea.addPoint(GKPoint(x+size,y-size))
    pedArea.addPoint(GKPoint(x-size,y-size))
    geomodel.add(layer, pedArea)
    return pedArea

# Create a Pedestrian area that will cover all nodes in the network
def createGlobalPedArea(geomodel, layer, name):
    # Get all the nodes and centroids in model
    nodeType = model.getType("GKNode")
    nodes = GKPoints()
    for types in model.getCatalog().getUsedSubTypesFromType( nodeType ):
        for s in iter(types.values()):
            nodes.append(s.getPosition())
    centroidType = model.getType("GKCentroid")
    for types in model.getCatalog().getUsedSubTypesFromType( centroidType ):
        for s in iter(types.values()):
            nodes.append(s.getPosition())
    # create the pedestrian area
    pedArea = GKSystem.getSystem().newObject("GKPedestrianArea", model)
    pedArea.setName(f"pedArea_{name}")
    pedArea.setExternalId(f"pedArea_{name}")
    # get a bounding box that contains all the nodes and centroids
    box = GKBBox()
    box.set(nodes)
    # add a buffer around the edge
    box.expandWidth(20.0)
    box.expandHeight(20.0)
    # set the pedestrian area
    for p in box.as2DPolygon():
        pedArea.addPoint(p)
    geomodel.add(layer, pedArea)
    return pedArea

def findNearbySections(centroid, nodeConnections):
    nearbySections = []
    nodeType = model.getType("GKNode")
    sectionType = model.getType("GKSection")
    # Get the nodes connected to the centroid
    centroidConnections = centroid.getConnections()
    for centroidConnection in iter(centroidConnections):
        node = centroidConnection.getConnectionObject()
        if node.getType() == nodeType:
            # Get the links from/to the nodes
            linkConnections = nodeConnections[node]
            for link in linkConnections:
                if link.getType() == sectionType:
                    nearbySections.append(link)
    if len(nearbySections) == 0:
        nearbySections = None
    return nearbySections

# Method takes a centroid as argument and returns a list of nearby bus stops
# Nearby bus stops are stops on any link to or from a node on a centroid connector
def findNearbyStops(centroid, nodeConnections):
    nearbyStops = []
    nearbySections = findNearbySections(centroid, nodeConnections)
    if nearbySections is not None:
        for section in nearbySections:
            potentialStops = section.getTopObjects()
            if potentialStops is not None:
                for stop in potentialStops:
                    nearbyStops.append(stop)
    # If no stops found make output none
    if len(nearbyStops) == 0:
        nearbyStops = None
    return nearbyStops

def createTransitCentroidConnections(centroidConfiguration, nodeConnections):
    print("Create pedestrian centroid configuration")
    # create pedestrian layer
    geomodel = model.getGeoModel()
    pedestrianLayer = geomodel.findLayer("Pedestrians Layer")
    if pedestrianLayer is None:
        pedestrianLayer = createPedestrianLayer()
    # Create a new pedestrian centroid configuration
    pedCentroidConfig = createPedestrianCentroidConfig()
    centroids = centroidConfiguration.getCentroids()
    # Create a global pedestrian area
    pedArea = createGlobalPedArea(geomodel, pedestrianLayer, "full")
    # Create centroids and connect all nearby bus stops
    print("Create pedestiran centroids and connections")
    sectionType = model.getType("GKBusStop")
    for centroid in centroids:
        pedCentroids = list()
        # Get all nearby stops
        nearbyStops = findNearbyStops(centroid, nodeConnections)
        # If no stops found get the closest stop
        if nearbyStops is None:
            nearbyStops = [geomodel.findClosestObject(centroid.getPosition(), sectionType)]
        # If no stops found move to the next centroid
        if nearbyStops is not None:
            # check if there is an existing pedestrian centroid
            pedCentroidType = model.getType("GKPedestrianEntranceCentroid")
            entranceCentroid = model.getCatalog().findObjectByExternalId(f"ped_entrance_{centroid.getExternalId()}", pedCentroidType)
            # if no existing pedestrian centroid create one
            if entranceCentroid is None:
                entranceCentroid = GKSystem.getSystem().newObject("GKPedestrianEntranceCentroid", model)
                entranceCentroid.setExternalId(f"ped_entrance_{centroid.getExternalId()}")
                entranceCentroid.setName(f"ped_entrance_{centroid.getExternalId()}")
                entranceCentroid.setFromPosition(centroid.getPosition())
                entranceCentroid.setWidth(3.0)
                entranceCentroid.setHeight(3.0)
                entranceCentroid.recalculateAreaPoints()
                pedCentroids.append(entranceCentroid)
                exitCentroid = GKSystem.getSystem().newObject("GKPedestrianExitCentroid", model)
                exitCentroid.setExternalId(f"ped_exit_{centroid.getExternalId()}")
                exitCentroid.setName(f"ped_exit_{centroid.getExternalId()}")
                exitCentroid.setFromPosition(centroid.getPosition())
                exitCentroid.setWidth(3.0)
                exitCentroid.setHeight(3.0)
                exitCentroid.recalculateAreaPoints()
                pedCentroids.append(exitCentroid) 
            # Connect the nearby transit stops to the centroids
            for stop in nearbyStops:
                # TODO change to newCmd for centroid connection causes crash
                entranceConnection = GKSystem.getSystem().newObject("GKCenConnection", model)
                entranceConnection.setOwner(entranceCentroid)
                entranceConnection.setConnectionObject(stop)
                entranceConnection.setConnectionType(1) # from connection
                entranceCentroid.addConnection(entranceConnection)
                exitConnection = GKSystem.getSystem().newObject("GKCenConnection", model)
                exitConnection.setOwner(exitCentroid)
                exitConnection.setConnectionObject(stop)
                exitConnection.setConnectionType(2) # to connection
                exitCentroid.addConnection(exitConnection)
        # Add the newly created pedestrian centroids to the centroid configuration and layer
        for pedCentroid in pedCentroids:
            pedCentroid.setPedestrianArea(pedArea)
            pedCentroid.setCentroidConfiguration(pedCentroidConfig)
            pedArea.addCentroid(pedCentroid)
            geomodel.add(pedestrianLayer, pedCentroid)
    
    return pedCentroidConfig

# Reads the modes file and defines all possible modes on the netowrk
def defineModes(filename):
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
    # read the file
    with open(filename, 'r') as f:
        lines = f.readlines()
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
    # save vehicle in netowrk file
    folderName = "GKModel::vehicles"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    for veh in vehicleTypes:
        folder.append(veh)
    return modes, vehicleTypes

def definePedestrianType():
    sectionType = model.getType("GKPedestrianType")
    # save vehicle in netowrk file
    folderName = "GKModel::pedestrianTypes"
    newVeh = GKSystem.getSystem().newObject("GKPedestrianType", model)
    newVeh.setName("Pedestrian")
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    folder.append(newVeh)
    return newVeh

# Method to read the functions.411 file
def readFunctionsFile(filename):
    vdfNames = []
    with open(filename, "r") as f:
        lines = f.readlines()
    for line in lines:
        if len(line)!=0:
            if line[0] == "a":
                splitLine = line.split()
                vdfNames.append(splitLine[1])
    return vdfNames

def addRoadTypes(listOfNames):
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
    # add the road type to the dict
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
        # add the road type to the dict
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

# Main script to complete the full netowrk import
def main(argv):
    overallStartTime = time.perf_counter()
    if len(argv) < 3:
        print("Incorrect Number of Arguments")
        print("Arguments: -script script.py blankAimsunProjectFile.ang networkDirectory outputNetworkFile.ang")
        return -1
    # Start a console
    console = ANGConsole()
    global model
    model, catalog, geomodel = loadModel(argv[1], console)
    # Import the new network
    print("Import network")
    print("Define modes")
    modes = defineModes(f"{argv[2]}/modes.201")
    # Cache the vehicle types
    allVehicles=[]
    sectionType = model.getType("GKVehicle")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for vehicle in iter(types.values()):
            allVehicles.append(vehicle)
    print("Define road types")
    roadTypeNames = readFunctionsFile(f"{argv[2]}/functions.411")
    roadTypes = addRoadTypes(roadTypeNames)
    print("Read base network data file")
    links, nodes, centroids, centroidSet = readFile(f"{argv[2]}/base.211")
    layer = model.getGeoModel().findLayer("Network")
    nodeStartTime = time.perf_counter()
    print("Add nodes")
    print(f"Number of nodes to import: {len(nodes)}")
    allNodes = []
    counter = 0
    infoStepSize = int(len(nodes)/4)
    for node in nodes:
        counter += 1
        newNode = addNode(node)
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
            addLink(link, allVehicles, roadTypes, layer, nodeConnections)
        # output the progress of the import
        if (counter % infoStepSize) == 0:
            print(f"{counter} links added")
    print("Add curvature to links")
    addLinkCurvatures(f"{argv[2]}/shapes.251", model.getCatalog())
    linkEndTime = time.perf_counter()
    print(f"Time to import links: {linkEndTime-linkStartTime}s")
    turnStartTime = time.perf_counter()
    # Build the turns (connections betweek links)
    createTurnsFromFile(f"{argv[2]}/turns.231", allNodes, nodeConnections)
    turnEndTime = time.perf_counter()
    print(f"Time to build turns: {turnEndTime-turnStartTime}s")
    # Add the centroids
    centroidStartTime = time.perf_counter()
    print("Add centroids")
    centroidConfig = createCentroidConfiguration("baseCentroidConfig", centroids)
    buildCentroidConnections(centroidConnections)
    centroidEndTime = time.perf_counter()
    print(f"Time to add centroids: {centroidEndTime-centroidStartTime}")
    # TODO move the transit centroid connections and pedestrian types to file
    # createTransitCentroidConnections(centroidConfig, nodeConnections)
    # pedestrianType = definePedestrianType()
    # Draw all graphical elements to the visible network layer
    drawLinksAndNodes(layer)
    # remove the object connections used for performance improvements
    # these are not needed for the final network
    print("Finished import")
    # Save the network to file
    print("Save network")
    console.save(argv[3])
    overallEndTime = time.perf_counter()
    print(f"Overall runtime: {overallEndTime-overallStartTime}s")
    # Reset the Aimsun undo buffer
    model.getCommander().addCommand( None )
    return 0

# This node positions is in the Aimsun docs as needed for macro models
# Not sure what it does for now
# print("Update Node Positions")
# sectionType = model.getType("GKNode")
# for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
#     for s in iter(types.values()):
#         s.updatePosition()

if __name__ == "__main__":
    main(sys.argv)
