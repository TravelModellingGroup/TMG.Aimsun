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
        if len(line)==0 or line[0] == 'c':
            continue
        elif line[0] == 't':
            currentlyReading = line.split()[1]
        elif line[0] == 'a':
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
    newLink.setName(f"link{link[1]}_{link[2]}")
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
    #TODO add set the allowed modes on the link
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
        if vehicle != transitVehicle:
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
    busStop.setName(f"stop_{node.getExternalId()}_line_{transitLine.getExternalId()}")
    busStop.setExternalId(f"stop_{node.getExternalId()}_line_{transitLine.getExternalId()}")
    busStop.setStopType(0) # set the stop type to normal
    nextLink.addTopObject(busStop)
    busStop.setLanes(0,0) # dummy link only has one lane
    busStop.setPosition(linkLength/2) # stop at midpoint of link
    return newLink

# Function to connect links (sections) in Aimsun
def buildTurnings():
    # Get all of the links and nodes
    print("Adding lane turnings")
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
                if origin == node:
                    linksOut.append(link)
                if destination == node:
                    linksIn.append(link)
            for entering in linksIn:
                for exiting in linksOut:
                    newTurn = GKSystem.getSystem().newObject("GKTurning", model)
                    newTurn.setConnection(entering, exiting)
                    node.addTurning(newTurn, True)
    print("Build Turnings Complete")

# Function to add all visual objects to the gui network layer
def drawLinksAndNodes(layer):
    modelToAddTo = model.getGeoModel()
    print("Adding Nodes")
    sectionType = model.getType("GKNode")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            modelToAddTo.add(layer, s)
    print("Adding Links")
    sectionType = model.getType("GKSection")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            modelToAddTo.add(layer, s)
    print("Adding Turnings")
    sectionType = model.getType("GKTurning")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            modelToAddTo.add(layer, s)
    print("Adding Transit Stops")
    sectionType = model.getType("GKBusStop")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            modelToAddTo.add(layer, s)
    print("Adding Centroids")
    sectionType = model.getType("GKCentroid")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            modelToAddTo.add(layer, s)
    print("Object drawn to Geo Model")

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
def addBusStop(fromNodeId, toNodeId, lineId, start):
    line = lineId
    busStop=GKSystem.getSystem().newObject("GKBusStop",model)
    model.getCatalog().add(busStop)
    if start==True:
        busStop.setName(f"stop_{fromNodeId}_line_{line}")
        busStop.setExternalId(f"stop_{fromNodeId}_line_{line}")
    else:
        busStop.setName(f"stop_{toNodeId}_line_{line}")
        busStop.setExternalId(f"stop_{toNodeId}_line_{line}")
    busStop.setStopType(0) # set the stop type to normal
    # Set the start and end nodes for the link
    sectionType = model.getType("GKNode")
    fromNode = model.getCatalog().findObjectByExternalId(fromNodeId, sectionType)
    toNode = model.getCatalog().findObjectByExternalId(toNodeId, sectionType)
    connectedLinks = fromNode.getConnections()
    stopLink = None
    for linkConnection in iter(connectedLinks):
        link = linkConnection.getConnectionObject()
        origin = link.getOrigin()
        destination = link.getDestination()
        if (origin == fromNode and destination == toNode):
            stopLink = link
            break
    stopLink.addTopObject(busStop)
    lanes = stopLink.getNbFullLanes()
    if lanes <1:
        lanes=1
    busStop.setLanes(lanes-1,lanes-1) #default to the rightmost lane
    # TODO add a parameter that allows trams to be added to the centre lane
    if start==True:
        busStop.setPosition(10.0) # 10m from start of link
    else:
        busStop.setPosition(stopLink.getLaneLength2D(lanes-1)-10.0) # 10m back from end of link
    busStop.setLength(10.0) # Placeholder default length
    # TODO add a parameter to set the stop length and position

# Function to build the transit lines Aimsun
def addTransitLine(lineId, lineName, pathList, stopsList, transitVehicle, allVehicles):
    cmd = model.createNewCmd( model.getType( "GKPublicLine" ) )
    cmd.setModel( model )
    model.getCommander().addCommand( cmd )
    ptLine = cmd.createdObject()
    ptLine.setExternalId(lineId)
    ptLine.setName(lineName)
    busStops = []
    links = []
    # Add the dummy link at the start of the line
    sectionType = model.getType("GKNode")
    startNode = model.getCatalog().findObjectByExternalId(pathList[0], sectionType)
    sectionType = model.getType("GKSection")
    firstLink = model.getCatalog().findByName(f"link{pathList[0]}_{pathList[1]}", sectionType)
    dummyLink = addDummyLink(transitVehicle, startNode, firstLink, ptLine, allVehicles)
    ptLine.add(dummyLink, None)
    # Build the list of bus stops
    # If there is no stop at a node add None to the list
    for i in range(len(pathList)):
        stop = pathList[i]
        # add a stop if there is a non zero dwell time or if is end of line
        if stopsList[i] != 0.0 or i==(len(pathList)-1):
            sectionType = model.getType("GKBusStop")
            busStop=model.getCatalog().findObjectByExternalId(f"stop_{stop}_line_{lineId}")
            if busStop != None:
                busStops.append(busStop)
            else:
                print(f"stop_{stop}_line_{lineId} not found")
                busStops.append(None)
        else:
            busStops.append(None)
    # Build the public transit line out of the path defined in the node list names pathList
    for i in range(1, len(pathList)):
        sectionType = model.getType("GKNode")
        fromNode = model.getCatalog().findObjectByExternalId(pathList[i-1], sectionType)
        toNode = model.getCatalog().findObjectByExternalId(pathList[i], sectionType)
        connectedLinks = fromNode.getConnections()
        pathLink = None
        for linkConnection in iter(connectedLinks):
            link = linkConnection.getConnectionObject()
            origin = link.getOrigin()
            destination = link.getDestination()
            if (origin == fromNode and destination == toNode):
                pathLink = link
                break
        if pathLink!=None:
            ptLine.add(pathLink, None)
        else:
            continue
    # add the stop list to the line
    ptLine.setStops(busStops)
    if ptLine.isCorrect()[0]==True:
        print (f"Transit Line {lineId} {lineName} was imported")
    else:
        print (f"Issue importing Transit Line {lineId} {lineName}")

# Function to create the transit lines from reading the file to adding to the network
def importTransit(fileName):
    # read the transit file
    print("Importing Transit Network")
    print("Reading transit file")
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
    for i in range(len(lines)):
        lineName = lines[i][5]
        lineId = lines[i][0]
        sectionType = model.getType("GKVehicle")
        lineVehicle = model.getCatalog().findObjectByExternalId(f"transitVeh_{lines[i][2]}", sectionType)
        pathList = nodes[i]
        stopsList = stops[i]
        print(f"Adding Line {lineId} {lineName}")
        # add all of the stops in the line to the network
        for j in range(len(pathList)):
            # fist stop will be on dummy link so don't add bus stop
            if j==0:
                continue
            # add a stop if there is a non zero dwell time or if is end of line
            if stopsList[j] != 0.0 or j==(len(pathList)-1):
                addBusStop(pathList[j-1],pathList[j],lineId,False)
        # add the transit line
        addTransitLine(lineId,lineName,pathList,stopsList,lineVehicle,allVehicles)
    print("Transit Import Complete")

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
    print(f"node {node.getName()}")
    nodeConnection = GKSystem.getSystem().newObject("GKCenConnection", model)
    nodeConnection.setOwner(centroid)
    nodeConnection.setConnectionObject(node)
    nodeConnection.setConnectionType(3)
    centroid.addConnection(nodeConnection)
    centroid.setPositionByConnections()
    return centroid

# Create centroid configuration
def createCentroidConfiguration(name, listOfCentroidIds):
    print("create centroid config object")
    cmd = model.createNewCmd(model.getType("GKCentroidConfiguration"))
    model.getCommander().addCommand( cmd )
    centroidConfig = cmd.createdObject()
    centroidConfig.setName(name)
    centroidConfig.setExternalId(name)
    print("create and add the centroids")
    for centroidId in listOfCentroidIds:
        centroid = createCentroid(centroidId)
        if centroidConfig.contains(centroid):
            continue
        centroidConfig.addCentroid(centroid)
    # save the centroid configuration
    print("save to folder")
    folderName = "GKModel::centroidsConf"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder == None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    folder.append(centroidConfig)
    return centroidConfig

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
    if folder == None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    for veh in vehicleTypes:
        folder.append(veh)
    return modes, vehicleTypes

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
            # TODO find where to add auto equivalent value
            vehicles.append(newVeh)
    # Save the transit vehicles within the aimsun network file
    folderName = "GKModel::vehicles"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder == None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    for veh in vehicles:
        folder.append(veh)
    return vehicles

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
        print("open blank network")
    else:
        console.getLog().addError("Cannot load the network")
        print("cannot load network")
        return -1
    # Import the new network
    print("Import Network")
    print("Define modes")
    modes = defineModes(f"{argv[2]}/modes.201")
    importTransitVehicles(f"{argv[2]}/vehicles.202")
    # Cache the vehicle types
    allVehicles=[]
    sectionType = model.getType("GKVehicle")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for vehicle in iter(types.values()):
            allVehicles.append(vehicle)
    print("Read Data File")
    links, nodes, centroids = readFile(f"{argv[2]}/base.211")
    nodeStartTime = time.perf_counter()
    print("Adding Nodes")
    print(f"Number of Nodes to Import: {len(nodes)}")
    counter = 0
    infoStepSize = int(len(nodes)/4)
    for node in nodes:
        counter += 1
        addNode(node)
        # output the progress of the import
        if (counter % infoStepSize) == 0:
            print(f"{counter} nodes added")
    nodeEndTime = time.perf_counter()
    print(f"Node Import Time: {nodeEndTime-nodeStartTime}s")
    linkStartTime = time.perf_counter()
    print("Adding Links")
    print(f"Number of Links to Import: {len(links)}")
    counter = 0
    infoStepSize = int(len(links)/10)
    for link in links:
        counter += 1
        addLink(link, allVehicles)
        # output the progress of the import
        if (counter % infoStepSize) == 0:
            print(f"{counter} links added")
    linkEndTime = time.perf_counter()
    print(f"Link Import Time: {linkEndTime-linkStartTime}s")
    turnStartTime = time.perf_counter()
    # Build the turns (connections betweek links)
    buildTurnings()
    turnEndTime = time.perf_counter()
    print(f"Time to Build Turns: {turnEndTime-turnStartTime}s")
    # Add the centroids
    centroidStartTime = time.perf_counter()
    print("Add centroids")
    centroidConfig = createCentroidConfiguration("baseCentroidConfig", centroids)
    centroidEndTime = time.perf_counter()
    print(f"Time to add centroids: {centroidEndTime-centroidStartTime}")
    # Import the transit network
    transitStartTime = time.perf_counter()
    importTransit(f"{argv[2]}/transit.221")
    transitEndTime = time.perf_counter()
    print(f"Time to import transit: {transitEndTime-transitStartTime}s")
    # Draw all graphical elements to the visible network layer
    layer = model.getGeoModel().findLayer("Network")
    drawLinksAndNodes(layer)
    print("Finished Import")
    # Save the network to file
    print("Save Network")
    console.save(argv[3])
    overallEndTime = time.perf_counter()
    print(f"Overall Runtime: {overallEndTime-overallStartTime}s")
    # Reset the Aimsun undo buffer
    model.getCommander().addCommand( None )

# This node positions is in the Aimsun docs as needed for macro models
# Not sure what it does for now
# print("Update Node Positions")
# sectionType = model.getType("GKNode")
# for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
#     for s in iter(types.values()):
#         s.updatePosition()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
