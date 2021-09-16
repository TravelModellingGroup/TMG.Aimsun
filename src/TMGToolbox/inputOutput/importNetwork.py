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
                    nodes.append(line.split())
                    # a* indicates that the node is a centroid
                    if line[1] == "*":
                        centroids.append(line.split()[1])
                elif currentlyReading == 'links':
                    links.append(line.split())
    return links, nodes, centroids

# Function to create a node object in Aimsun
def addNode(node):
    # Create new node
    newNode = GKSystem.getSystem().newObject("GKNode", model)
    # Set the name to the node number
    newNode.setName(f"node{node[1]}")
    newNode.setExternalId(node[1])
    model.getCatalog().catalogObjectExternalId(newNode)
    # Set the position of the node in space
    newNode.setPosition(GKPoint(float(node[2]), float(node[3])))
    # For now ignoring the Data1, Data 2, Data 3, and Label columns

# Function to create a link (section) object in Aimsun
def addLink(link, allVehicles):
    # Create the link
    newLink = GKSystem.getSystem().newObject("GKSection", model)
    # Set the name to reflect start and end nodes
    name = f"link{link[1]}_{link[2]}"
    newLink.setName(name)
    newLink.setExternalId(name)
    # Set the start and end nodes for the link
    sectionType = model.getType("GKNode")
    fromNode = model.getCatalog().findObjectByExternalId(link[1], sectionType)
    newLink.setOrigin(fromNode)
    toNode = model.getCatalog().findObjectByExternalId(link[2], sectionType)
    newLink.setDestination(toNode)
    newLink.addPoint(newLink.getOrigin().getPosition())
    newLink.addPoint(newLink.getDestination().getPosition())
    newLink.setFromPoints(newLink.getPoints(), 0)
    # Connect the origin and destination nodes to the link
    originConnection = GKSystem.getSystem().newObject("GKObjectConnection", model)
    originConnection.setOwner(fromNode)
    originConnection.setConnectionObject(newLink)
    fromNode.addConnection(originConnection)
    destinationConnection = GKSystem.getSystem().newObject("GKObjectConnection", model)
    destinationConnection.setOwner(toNode)
    destinationConnection.setConnectionObject(newLink)
    toNode.addConnection(destinationConnection)
    # add the lanes
    numberOfLanes = int(float(link[6]))
    for l in range(numberOfLanes):
        lane = GKSectionLane()
        newLink.addLane(lane)
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

    #TODO add the type, not sure how to represent this
    #TODO add the volume delay function
    # Add Data 2 which is free flow speed
    freeFlowSpeed = float(link[9])
    newLink.setSpeed(freeFlowSpeed)
    # Add Data 3 which is capacity per lane per hour
    capacityPerLane = float(link[10])
    newLink.setCapacity(float(numberOfLanes) * capacityPerLane)

def addDummyLink(transitVehicle, node, nextLink, transitLine, allVehicles):
    # Create the link
    newLink = GKSystem.getSystem().newObject("GKSection", model)
    newLink.setName(f"dummylink_{transitLine.getExternalId()}")
    newLink.setExternalId(f"dummylink_{transitLine.getExternalId()}")
    # Set the start end end points of the link
    nodePoint = node.getPosition()
    linkLength = 20.00
    newLink.addPoint(GKPoint(nodePoint.x-linkLength, nodePoint.y))
    newLink.addPoint(nodePoint)
    newLink.setFromPoints(newLink.getPoints(), 0)
    # Set the desination link to the node
    newLink.setDestination(node)
    destinationConnection = GKSystem.getSystem().newObject("GKObjectConnection", model)
    destinationConnection.setOwner(node)
    destinationConnection.setConnectionObject(newLink)
    node.addConnection(destinationConnection)
    # make one lane for dummy link
    lane = GKSectionLane()
    newLink.addLane(lane)
    # Set the allowed mode to only include transit vehicle
    newLink.setUseRoadTypeNonAllowedVehicles(False)
    # create list of banned vehicles
    bannedVehicles = []
    for vehicle in allVehicles:
        if vehicle is not transitVehicle:
            bannedVehicles.append(vehicle)
    # set the banned vehicles on the section
    if len(bannedVehicles)>0:
        newLink.setNonAllowedVehicles(bannedVehicles)
    # Make the turning object to the first link in the transit line
    newTurn = GKSystem.getSystem().newObject("GKTurning", model)
    newTurn.setConnection(newLink, nextLink)
    node.addTurning(newTurn, True)
    # add a transit stop
    busStop = GKSystem.getSystem().newObject("GKBusStop", model)
    model.getCatalog().add(busStop)
    busStop.setName(f"stop_{node.getExternalId()}_{newLink.getExternalId()}")
    busStop.setExternalId(f"stop_{node.getExternalId()}_{newLink.getExternalId()}")
    busStop.setStopType(0) # set the stop type to normal
    nextLink.addTopObject(busStop)
    busStop.setLanes(0,0) # dummy link only has one lane
    busStop.setPosition(linkLength/2) # stop at midpoint of link
    return newLink, busStop

# Function to add curvature to links
def addLinkCurvature(link, pointsToAdd):
    for point in reversed(pointsToAdd):
        link.addPointAt(1,point)
    # TODO check on curve type
    link.setFromPoints(link.getPoints(), 0)
    return link

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

def addLinkCurvatures(filename, catalog):
    curves = readShapesFile(filename, catalog)
    for curve in curves:
        addLinkCurvature(curve[0], curve[1])

# Function to connect links (sections) in Aimsun
def buildTurnings():
    # Get all of the links and nodes
    print("Build lane turns")
    # Assume that all links that are connected by nodes have all lanes 
    # turning to each other
    nodeType = model.getType("GKNode")
    geomodel = model.getGeoModel()
    for types in model.getCatalog().getUsedSubTypesFromType( nodeType ):
        for node in iter(types.values()):
            linksIn = []
            linksOut = []
            linkType = model.getType("GKSection")
            connectedLinks = node.getConnections()
            for linkConnection in iter(connectedLinks):
                link = linkConnection.getConnectionObject()
                origin = link.getOrigin()
                destination = link.getDestination()
                if origin is node:
                    linksOut.append(link)
                if destination is node:
                    linksIn.append(link)
            for entering in linksIn:
                for exiting in linksOut:
                    newTurn = GKSystem.getSystem().newObject("GKTurning", model)
                    newTurn.setConnection(entering, exiting)
                    node.addTurning(newTurn, True)

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

# Function to read the transit.221 file and return the relevant information for the import to Aimsun
def readTransitFile(filename):
    nodes = []
    stops = []
    lines = []
    transitLines = []
    currentlyReadingLine = None
    lineInfo = None
    lineNodes = []
    lineStops = []
    with open(filename, 'r') as f:
        lines = f.readlines()
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

# Function to create the bus stop objects in the Aimsun network
def addBusStop(fromNodeId, toNodeId, link, start):
    # Check if the stop already exists
    busStopType = model.getType("GKBusStop")
    if start is True:
        externalId = f"stop_{fromNodeId}_{link.getExternalId()}"
    else:
        externalId = f"stop_{toNodeId}_{link.getExternalId()}"
    existingBusStop = model.getCatalog().findObjectByExternalId(externalId, busStopType)
    # If the stop exists return it
    if existingBusStop is not None:
        return existingBusStop
    # Otherwise create a new object
    busStop=GKSystem.getSystem().newObject("GKBusStop",model)
    model.getCatalog().add(busStop)
    busStop.setName(externalId)
    busStop.setExternalId(externalId)
    busStop.setStopType(0) # set the stop type to normal
    stopLink = link
    stopLink.addTopObject(busStop)
    lanes = stopLink.getNbFullLanes()
    if lanes <1:
        lanes=1
    busStop.setLanes(lanes-1,lanes-1) #default to the rightmost lane
    # TODO add a parameter that allows trams to be added to the centre lane
    if start is True:
        busStop.setPosition(10.0) # 10m from start of link
    else:
        busStop.setPosition(stopLink.getLaneLength2D(lanes-1)-10.0) # 10m back from end of link
    busStop.setLength(10.0) # Placeholder default length
    # TODO add a parameter to set the stop length and position
    return busStop

# Function to build the transit lines Aimsun
def addTransitLine(lineId, lineName, pathLinks, busStops, transitVehicle, allVehicles):
    cmd = model.createNewCmd( model.getType( "GKPublicLine" ) )
    cmd.setModel( model )
    model.getCommander().addCommand( cmd )
    ptLine = cmd.createdObject()
    ptLine.setExternalId(lineId)
    ptLine.setName(lineName)
    links = []
    # Add the dummy link at the start of the line
    firstLink = pathLinks[0]
    dummyLink, dummyLinkStop = addDummyLink(transitVehicle, firstLink.getOrigin(), firstLink, ptLine, allVehicles)
    ptLine.add(dummyLink, None)
    # add the dummyLink to the busStops list
    allBusStops = busStops
    allBusStops.insert(0,dummyLinkStop)
    # Build the public transit line out of the path defined in the node list names pathList
    for link in pathLinks:
        ptLine.add(link, None)
    # add the stop list to the line
    ptLine.setStops(allBusStops)
    if ptLine.isCorrect()[0] is False:
        print (f"Issue importing transit line {lineId} {lineName}")

# Takes a path list as argument
# Returns the nodes and links that make up the path
def getPath(pathList):
    nodes = []
    links = []
    nodeType = model.getType("GKNode")
    for nodeNumber in pathList:
        node = model.getCatalog().findObjectByExternalId(nodeNumber, nodeType)
        nodes.append(node)
    for i in range(1, len(nodes)):
        fromNode = nodes[i-1]
        toNode = nodes[i]
        link = None
        connectedLinks = fromNode.getConnections()
        for linkConnection in iter(connectedLinks):
            testLink = linkConnection.getConnectionObject()
            origin = testLink.getOrigin()
            if origin == fromNode:
                destination = testLink.getDestination()
                if destination == toNode:
                    link = testLink
                    break
        links.append(link)
    return nodes, links

# Function to create the transit lines from reading the file to adding to the network
def importTransit(fileName):
    # read the transit file
    print("Import transit network")
    print("Read transit file")
    nodes, stops, lines = readTransitFile(fileName)
    # Cache the vehicle types
    allVehicles=[]
    sectionType = model.getType("GKVehicle")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for vehicle in iter(types.values()):
            allVehicles.append(vehicle)
    # add each line one at a time
    lineName = None
    lineId = None
    pathList = None
    stopsList = None
    print(f"Number of transit lines to import: {len(lines)}")
    for i in range(len(lines)):
        lineName = lines[i][5]
        lineId = lines[i][0]
        sectionType = model.getType("GKVehicle")
        lineVehicle = model.getCatalog().findObjectByExternalId(f"transitVeh_{lines[i][2]}", sectionType)
        pathList = nodes[i]
        stopsList = stops[i]
        busStops = []
        # print(f"Adding Line {lineId} {lineName}")
        # Get the path links and nodes
        nodePath, linkPath = getPath(pathList)
        # add all of the stops in the line to the network
        # fist stop will be on dummy link so don't add bus stop
        for j in range(1, len(nodePath)):
            # add a stop if there is a non zero dwell time or if is end of line
            if stopsList[j] != 0.0 or j==(len(nodePath)-1):
                link = linkPath[j-1]
                newBusStop = addBusStop(nodePath[j-1].getExternalId(),nodePath[j].getExternalId(),link,False)
                busStops.append(newBusStop)
            else:
                busStops.append(None)
        # add the transit line
        addTransitLine(lineId,lineName,linkPath,busStops,lineVehicle,allVehicles)
    print("Transit import complete")

def createCentroid(nodeId):
    # First check if the centroid already exists
    # If yes return centroid
    # If no create new centroid and connect to the node
    sectionType = model.getType("GKCentroid")
    existingCentroid = model.getCatalog().findObjectByExternalId(f"centroid_{nodeId}", sectionType)
    if existingCentroid != None:
        return existingCentroid
    # Create the centroid
    centroid = GKSystem.getSystem().newObject("GKCentroid", model)
    centroid.setExternalId(f"centroid_{nodeId}")
    centroid.setName(f"centroid_{nodeId}")
    sectionType = model.getType("GKNode")
    node = model.getCatalog().findObjectByExternalId(nodeId, sectionType)
    nodeConnection = GKSystem.getSystem().newObject("GKCenConnection", model)
    nodeConnection.setOwner(centroid)
    nodeConnection.setConnectionObject(node)
    nodeConnection.setConnectionType(3) # to and from connection
    centroid.addConnection(nodeConnection)
    centroid.setPositionByConnections()
    return centroid

# Create centroid configuration
def createCentroidConfiguration(name, listOfCentroidIds):
    print("Create centroid config object")
    cmd = model.createNewCmd(model.getType("GKCentroidConfiguration"))
    model.getCommander().addCommand( cmd )
    centroidConfig = cmd.createdObject()
    centroidConfig.setName(name)
    centroidConfig.setExternalId(name)
    print("Create and add the centroids")
    for centroidId in listOfCentroidIds:
        centroid = createCentroid(centroidId)
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
    # Get all the nodes in model
    sectionType = model.getType("GKNode")
    nodes = GKPoints()
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            nodes.append(s.getPosition())
    # create the pedestrian area
    pedArea = GKSystem.getSystem().newObject("GKPedestrianArea", model)
    pedArea.setName(f"pedArea_{name}")
    pedArea.setExternalId(f"pedArea_{name}")
    # get a bounding box that contains all the nodes
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

# Method takes a centroid as argument and returns a list of nearby bus stops
# Nearby bus stops are stops on any link connected to the connected nodes
def findNearbyStops(centroid):
    nearbyStops = []
    nodeType = model.getType("GKNode")
    sectionType = model.getType("GKSection")
    stopType = model.getType("GKBusStop")
    # Get the nodes connected to the centroid (should only be 1)
    nodeConnections = centroid.getConnections()
    for nodeConnection in iter(nodeConnections):
        node = nodeConnection.getConnectionObject()
        if node.getType() == nodeType:
            # Get the links from/to the nodes
            linkConnections = node.getConnections()
            for linkConnection in iter(linkConnections):
                link = linkConnection.getConnectionObject()
                if link.getType() == sectionType:
                    # Get the node at the other end of the link
                    origin = link.getOrigin()
                    destination = link.getDestination()
                    if node == origin:
                        outLinkConnections = destination.getConnections()
                    elif node == destination:
                        outLinkConnections = origin.getConnections()
                    else:
                        outLinkConnections = []
                    # Get all the links radiating out
                    for outLinkConnection in outLinkConnections:
                        outLink = outLinkConnection.getConnectionObject()
                        if outLink.getType() == sectionType:
                            # If the links have a bus stop add it to output
                            potentialStops = outLink.getTopObjects()
                            if potentialStops is not None:
                                for stop in potentialStops:
                                    if stop.getType() == stopType:
                                        nearbyStops.append(stop)
    # If no stops foudn make output none
    if len(nearbyStops) == 0:
        nearbyStops = None
    return nearbyStops

def createTransitCentroidConnections(centroidConfiguration):
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
        nearbyStops = findNearbyStops(centroid)
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

def importTransitVehicles(filename):
    vehicles = []
    # read the file
    with open(filename, 'r') as f:
        lines = f.readlines()
    for line in lines:
        lineItems = shlex.split(line)
        if len(line)>0 and len(lineItems)>=12 and line[0]=='a':
            newVeh = GKSystem.getSystem().newObject("GKVehicle", model)
            newVeh.setName(lineItems[2])
            newVeh.setExternalId(f"transitVeh_{lineItems[1]}")
            sectionType = model.getType("GKTransportationMode")
            mode = model.getCatalog().findObjectByExternalId(lineItems[3], sectionType)
            if mode != None:
                newVeh.setTransportationMode(mode)
            # Set capacity type to passengers
            newVeh.setCapacityType(0)
            newVeh.setCapacity(float(lineItems[6]))
            newVeh.setSeatingCapacity(float(lineItems[5]))
            # TODO check PCUs are being used correctly in static assignment
            newVeh.pcus = int(float(lineItems[11]))
            vehicles.append(newVeh)
    # Save the transit vehicles within the aimsun network file
    folderName = "GKModel::vehicles"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder is None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    for veh in vehicles:
        folder.append(veh)
    return vehicles

# Test script for running the import network from the aimsun bridge
# Takes the console and model objects opened in the aimsun bridge
# networkDirectory is the path the the unzipped network file
# outputNetworkFile is the path to file name of the output file
def importFromBrigde(console, model, networkDirectory, outputNetworkFile):
    # Import the new network
    modes = defineModes(networkDirectory + "/modes.201")
    importTransitVehicles(networkDirectory + "/vehicles.202")
    # Cache the vehicle types
    allVehicles=[]
    sectionType = model.getType("GKVehicle")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for vehicle in iter(types.values()):
            allVehicles.append(vehicle)
    links, nodes, centroids = readFile(networkDirectory + "/base.211")
    for node in nodes:
        addNode(node)
    for link in links:
        addLink(link, allVehicles)
    # Build the turns (connections betweek links)
    buildTurnings()
    # Add the centroids
    centroidConfig = createCentroidConfiguration("baseCentroidConfig", centroids)
    # Import the transit network
    importTransit(networkDirectory+"/transit.221")
    createTransitCentroidConnections(centroidConfig)
    pedestrianType = definePedestrianType()
    # Draw all graphical elements to the visible network layer
    layer = model.getGeoModel().findLayer("Network")
    drawLinksAndNodes(layer)
    # Save the network to file
    console.save(outputNetworkFile)
    # Reset the Aimsun undo buffer
    model.getCommander().addCommand( None )
    return console, model

# Main script to complete the full netowrk import
def main(argv):
    overallStartTime = time.perf_counter()
    if len(argv) < 3:
        print("Incorrect Number of Arguments")
        print("Arguments: -script script.py blankAimsunProjectFile.ang networkDirectory outputNetworkFile.ang")
        return -1
    # Start a console
    console = ANGConsole()
    # Load a network
    if console.open(argv[1]): 
        global model
        model = console.getModel()
        print("Open blank network")
    else:
        console.getLog().addError("Cannot load the network")
        print("Cannot load network")
        return -1
    # Import the new network
    print("Import network")
    print("Define modes")
    modes = defineModes(f"{argv[2]}/modes.201")
    importTransitVehicles(f"{argv[2]}/vehicles.202")
    # Cache the vehicle types
    allVehicles=[]
    sectionType = model.getType("GKVehicle")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for vehicle in iter(types.values()):
            allVehicles.append(vehicle)
    print("Read base network data file")
    links, nodes, centroids = readFile(f"{argv[2]}/base.211")
    nodeStartTime = time.perf_counter()
    print("Add nodes")
    print(f"Number of nodes to import: {len(nodes)}")
    counter = 0
    infoStepSize = int(len(nodes)/4)
    for node in nodes:
        counter += 1
        addNode(node)
        # output the progress of the import
        if (counter % infoStepSize) == 0:
            print(f"{counter} nodes added")
    nodeEndTime = time.perf_counter()
    print(f"Time to import nodes: {nodeEndTime-nodeStartTime}s")
    linkStartTime = time.perf_counter()
    print("Add links")
    print(f"Number of links to import: {len(links)}")
    counter = 0
    infoStepSize = int(len(links)/4)
    for link in links:
        counter += 1
        addLink(link, allVehicles)
        # output the progress of the import
        if (counter % infoStepSize) == 0:
            print(f"{counter} links added")
    print("Add curvature to links")
    addLinkCurvatures(f"{argv[2]}/shapes.251", model.getCatalog())
    linkEndTime = time.perf_counter()
    print(f"Time to import links: {linkEndTime-linkStartTime}s")
    turnStartTime = time.perf_counter()
    # Build the turns (connections betweek links)
    buildTurnings()
    turnEndTime = time.perf_counter()
    print(f"Time to build turns: {turnEndTime-turnStartTime}s")
    # Add the centroids
    centroidStartTime = time.perf_counter()
    print("Add centroids")
    centroidConfig = createCentroidConfiguration("baseCentroidConfig", centroids)
    centroidEndTime = time.perf_counter()
    print(f"Time to add centroids: {centroidEndTime-centroidStartTime}")
    # Import the transit network
    transitStartTime = time.perf_counter()
    importTransit(f"{argv[2]}/transit.221")
    createTransitCentroidConnections(centroidConfig)
    pedestrianType = definePedestrianType()
    transitEndTime = time.perf_counter()
    print(f"Time to import transit: {transitEndTime-transitStartTime}s")
    # Draw all graphical elements to the visible network layer
    layer = model.getGeoModel().findLayer("Network")
    drawLinksAndNodes(layer)
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
