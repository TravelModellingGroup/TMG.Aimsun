"""
    Copyright 2021 Travel Modelling Group, Department of Civil Engineering, University of Toronto

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
import time
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
import shlex
from common.common import read_datafile, extract_network_packagefile, createTurn, loadModel, getTransitNodesStopsAndLinesFromNWP, cacheAllOfTypeByExternalId, cacheNodeConnections


def addAllowedVehicle(section, vehicle):
    if section.canUseVehicle(vehicle) is False:
        bannedVehicles = []
        for veh in section.getNonAllowedVehicles():
            if veh != vehicle:
                bannedVehicles.append(veh)
        if len(bannedVehicles)>0:
            section.setUseRoadTypeNonAllowedVehicles(False)
            section.setNonAllowedVehicles(bannedVehicles)

def turnCheck(fromSection, toSection, model):
    turnsOut = fromSection.getDestTurnings()
    for turn in turnsOut:
        destination = turn.getDestination()
        if destination == toSection:
            return
    createTurn(fromSection.getDestination(), fromSection, toSection, model)

def addDummyLink(transitVehicle, node, nextLink, allVehicles, roadTypes, layer, catalog, model):
    # Check if the dummy link already exists
    sectionType = model.getType("GKSection")
    busStopType = model.getType("GKBusStop")
    existingDummyLink = catalog.findObjectByExternalId(f"dummylink_at_{node.getExternalId()}", sectionType)
    if existingDummyLink is not None:
        # Find the bus stop on the dummy link
        busStop = None
        dummyLink = existingDummyLink
        potentialStops = dummyLink.getTopObjects()
        if potentialStops is not None:
            for stop in potentialStops:
                if stop.getType() == busStopType:
                    busStop = stop
        # Check the allowed vehicles
        addAllowedVehicle(dummyLink, transitVehicle)
        # Check can turn onto nextLink
        turnCheck(dummyLink, nextLink, model)
        if busStop is not None:
            return dummyLink, busStop
    # Create the link
    numberOfLanes = 1
    laneWidth = 2.0
    nodePoint = node.getPosition()
    linkLength = 20.00
    points = GKPoints()
    points.append(GKPoint(nodePoint.x-linkLength, nodePoint.y))
    points.append(nodePoint)
    roadType = roadTypes["dummyLinkRoadType"]
    cmd = model.createNewCmd(model.getType("GKSection"))
    cmd.setPoints(numberOfLanes, laneWidth, points, layer)
    cmd.setRoadType(roadType)
    model.getCommander().addCommand(cmd)
    newLink = cmd.createdObject()

    newLink.setName(f"dummylink_at_{node.getExternalId()}")
    newLink.setExternalId(f"dummylink_at_{node.getExternalId()}")

    # Set the desination link to the node
    newLink.setDestination(node)

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
    newTurn = createTurn(node, newLink, nextLink, model)
    # add a transit stop
    busStop = GKSystem.getSystem().newObject("GKBusStop", model)
    catalog.add(busStop)
    busStop.setName(f"stop_{node.getExternalId()}_{newLink.getExternalId()}")
    busStop.setExternalId(f"stop_{node.getExternalId()}_{newLink.getExternalId()}")
    busStop.setStopType(0) # set the stop type to normal
    newLink.addTopObject(busStop)
    busStop.setLanes(0,0) # dummy link only has one lane
    busStop.setPosition(linkLength/2) # stop at midpoint of link
    busStop.setLength(linkLength/2)
    return newLink, busStop

def importTransitVehicles(networkZipFileObject, filename, catalog, model):
    vehicles = []
    # read the file
    lines = read_datafile(networkZipFileObject, filename)
    next(lines)
    for line in lines:
        lineItems = shlex.split(line)
        if len(line)>0 and len(lineItems)>=12 and line[0]=='a':
            newVeh = GKSystem.getSystem().newObject("GKVehicle", model)
            newVeh.setName(lineItems[2])
            newVeh.setExternalId(f"transitVeh_{lineItems[1]}")
            sectionType = model.getType("GKTransportationMode")
            mode = catalog.findObjectByExternalId(lineItems[3], sectionType)
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

def addBusStop(fromNodeId, toNodeId, link, start, repeatNumber, catalog, model):
    """
    Function to create the bus stop objects in the Aimsun network
    repeatNumber is the number of times that same busStop is in a line
    """
    # Check if the stop already exists
    busStopType = model.getType("GKBusStop")
    if start is True:
        externalId = f"stop_{fromNodeId}_{link.getExternalId()}_{repeatNumber}"
    else:
        externalId = f"stop_{toNodeId}_{link.getExternalId()}_{repeatNumber}"
    existingBusStop = catalog.findObjectByExternalId(externalId, busStopType)
    # If the stop exists return it
    if existingBusStop is not None:
        return existingBusStop
    # Otherwise create a new object
    busStop=GKSystem.getSystem().newObject("GKBusStop",model)
    catalog.add(busStop)
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


def addTransitLine(lineId, lineName, pathLinks, busStops, transitVehicle, allVehicles, roadTypes, layer, catalog, model):
    """
    Function to build the transit lines Aimsun
    """
    cmd = model.createNewCmd( model.getType( "GKPublicLine" ) )
    cmd.setModel( model )
    model.getCommander().addCommand( cmd )
    ptLine = cmd.createdObject()
    ptLine.setExternalId(lineId)
    ptLine.setName(lineName)
    links = []
    # Add the dummy link at the start of the line
    firstLink = pathLinks[0]
    dummyLink, dummyLinkStop = addDummyLink(transitVehicle, firstLink.getOrigin(), firstLink, allVehicles, roadTypes, layer, catalog, model)
    ptLine.add(dummyLink, None)
    # add the dummyLink to the busStops list
    allBusStops = busStops
    allBusStops.insert(0,dummyLinkStop)
    # Build the public transit line out of the path defined in the node list names pathList
    for link in pathLinks:
        ptLine.add(link, None)
    # add the stop list to the line
    ptLine.setStops(allBusStops)
    # Check that the route defined by the line is valid
    check = ptLine.isCorrect()
    # Set a max number of attempts to fix the line
    fixTries = 5
    while check[0] is False and fixTries > 0:
        print(f"Fix a discontinuity in transit line {lineId} {lineName}")
        # create a new turn to fix the discrepancy
        fromLink = catalog.find(check[3])
        toLink = catalog.find(check[1])
        node = fromLink.getDestination()
        createTurn(node, fromLink, toLink, model)
        # update the check and the maximum tries counter
        check = ptLine.isCorrect()
        fixTries -= 1
    if check[0] is False:
        print (f"Issue importing transit line {lineId} {lineName}")

def getPath(pathList, nodeConnections, catalog, model):
    """
    Takes a path list as argument
    Returns the nodes and links that make up the path
    """
    nodes = []
    links = []
    nodeType = model.getType("GKNode")
    linkType = model.getType("GKSection")
    for nodeNumber in pathList:
        node = catalog.findObjectByExternalId(nodeNumber, nodeType)
        nodes.append(node)
    for i in range(1, len(nodes)):
        fromNode = nodes[i-1]
        toNode = nodes[i]
        link = None
        connectedLinks = nodeConnections[fromNode]
        for testLink in connectedLinks:
            # Check that the connected object is a link
            if testLink.getType() == linkType:
                origin = testLink.getOrigin()
                if origin == fromNode:
                    destination = testLink.getDestination()
                    if destination == toNode:
                        link = testLink
                        break
        links.append(link)
    return nodes, links

def importTransit(networkZipFileObject, fileName, roadTypes, layer, nodeConnections, catalog, model):
    """
    Function to create the transit lines from reading the file to adding to the network
    """
    # read the transit file
    print("Import transit network")
    print("Read transit file")
    nodes, stops, lines = getTransitNodesStopsAndLinesFromNWP(networkZipFileObject)
    # Cache the vehicle types
    allVehicles=[]
    sectionType = model.getType("GKVehicle")
    for types in catalog.getUsedSubTypesFromType( sectionType ):
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
        lineVehicle = catalog.findObjectByExternalId(f"transitVeh_{lines[i][2]}", sectionType)
        pathList = nodes[i]
        stopsList = stops[i]
        busStops = []
        # print(f"Adding Line {lineId} {lineName}")
        # Get the path links and nodes
        nodePath, linkPath = getPath(pathList, nodeConnections, catalog, model)
        # add all of the stops in the line to the network
        # fist stop will be on dummy link so don't add bus stop
        for j in range(1, len(nodePath)):
            # add a stop if there is a non zero dwell time or if is end of line
            if stopsList[j] != 0.0 or j==(len(nodePath)-1):
                link = linkPath[j-1]
                repeatNumber = 0
                newBusStop = addBusStop(nodePath[j-1].getExternalId(),nodePath[j].getExternalId(),link,False, repeatNumber, catalog, model)
                # Check to see if the bus stop is already used in the line
                # if yes make a new stop in the same place
                while newBusStop in busStops:
                    repeatNumber = repeatNumber + 1
                    newBusStop = addBusStop(nodePath[j-1].getExternalId(),nodePath[j].getExternalId(),link,False, repeatNumber, catalog, model)
                busStops.append(newBusStop)
            else:
                busStops.append(None)
        # add the transit line
        addTransitLine(lineId,lineName,linkPath,busStops,lineVehicle,allVehicles, roadTypes, layer, catalog, model)
    print("Transit import complete")

def addWalkingTimes(busStop, geomodel, transferDistance, maxTransfers, busStopType, model):
    location = busStop.absolutePosition()
    walkingTime = busStop.getWalkingTime() # map to store the walking times
    times = walkingTime.getWalkingTimes(busStop, model)
    # Search for all points within the specified transfer distance
    nearbyStops = geomodel.findClosestObjects(location, transferDistance, busStopType)
    walkingSpeed = 1.4 # walking speed in m/s
    walkingSpeedInv = 1.0/walkingSpeed
    # limit to a maximum number of stops
    transferDistances = []
    for stop in nearbyStops:
        transferDistances.append((stop,walkingSpeedInv*location.distance2D(stop.absolutePosition())))
    transferDistances.sort(key=lambda tup: tup[1])
    if len(transferDistances) < maxTransfers:
        maxTransfers = len(transferDistances)
    for i in range(maxTransfers):
        times[transferDistances[i][0]] = transferDistances[i][1]
    walkingTime.setWalkingTimes(times)
    busStop.setWalkingTime(walkingTime)

def buildWalkingTransfers(catalog, geomodel, model):
    busStopType = model.getType("GKBusStop")
    busStops = catalog.getObjectsByType(busStopType)
    for stop in iter(busStops.values()):
        addWalkingTimes(stop, geomodel, 200.0, 10, busStopType, model)

def findNearbySections(centroid, nodeConnections, model):
    """
    function to find nearby sections around a centroid
    """
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
    return nearbySections

def findNearbyStops(centroid, nodeConnections, model):
    """
    Method takes a centroid as argument and returns a list of nearby transit stops
    Nearby bus stops are stops on any link to or from a node on a centroid connector
    """
    nearbyStops = []
    nearbySections = findNearbySections(centroid, nodeConnections, model)
    for section in nearbySections:
        potentialStops = section.getTopObjects()
        if potentialStops is not None:
            for stop in potentialStops:
                nearbyStops.append(stop)
    return nearbyStops

def createTransitCentroidConnections(centroidConfiguration, nodeConnections, model, catalog, geomodel):
    """
    function to connect the transit stops to the centroids
    """
    centroids = centroidConfiguration.getCentroids()
    sectionType = model.getType("GKBusStop")
    for centroid in centroids:
        # Get all nearby stops
        nearbyStops = findNearbyStops(centroid, nodeConnections, model)
        # If no stops found get the closest stop
        if len(nearbyStops) == 0:
            nearbyStops = [geomodel.findClosestObject(centroid.getPosition(), sectionType)]
        # If no stops found move to the next centroid
        if nearbyStops is not None:
            # Connect the nearby transit stops to the centroids
            for stop in nearbyStops:
                # TODO change to newCmd for centroid connection causes crash
                entranceConnection = GKSystem.getSystem().newObject("GKCenConnection", model)
                entranceConnection.setOwner(centroid)
                entranceConnection.setConnectionObject(stop)
                entranceConnection.setConnectionType(1) # from connection
                centroid.addConnection(entranceConnection)
                exitConnection = GKSystem.getSystem().newObject("GKCenConnection", model)
                exitConnection.setOwner(centroid)
                exitConnection.setConnectionObject(stop)
                exitConnection.setConnectionType(2) # to connection
                centroid.addConnection(exitConnection)

def run_xtmf(parameters, model, console):
    """
     A general function called in all python modules called by bridge. Responsible
     for extracting data and running appropriate functions.
    """
    networkPackage = parameters["NetworkPackageFile"]
    _execute(networkPackage, model, console)

def _execute(networkPackage, inputModel, console):
    """ 
    Main execute function to run the simulation 
    """
    overallStartTime = time.perf_counter()
    loadModelStartTime = time.perf_counter()
    networkDir = networkPackage
    model = inputModel
    catalog = model.getCatalog()
    geomodel = model.getGeoModel()

    #ZipFile object of the network file do this once
    networkZipFileObject = extract_network_packagefile(networkPackage)

    networkLayer = geomodel.findLayer("Network")
    nodes = cacheAllOfTypeByExternalId("GKNode", model, catalog)
    sections = cacheAllOfTypeByExternalId("GKSection", model, catalog)
    nodeConnections = cacheNodeConnections(nodes.values(), sections.values())
    loadModelEndTime = time.perf_counter()
    print(f"Time to load model: {loadModelEndTime-loadModelStartTime}")
    transitStartTime = time.perf_counter()
    transitVehicles = importTransitVehicles(networkZipFileObject, "vehicles.202", catalog, model)
    allVehicles = cacheAllOfTypeByExternalId("GKVehicle", model, catalog)
    roadTypes = cacheAllOfTypeByExternalId("GKRoadType", model, catalog)
    importTransit(networkZipFileObject, "transit.221", roadTypes, networkLayer, nodeConnections, catalog, model)
    buildWalkingTransfers(catalog, geomodel, model)
    transitEndTime = time.perf_counter()
    print(f"Time to import transit: {transitEndTime-transitStartTime}")
    centroidConfig = catalog.findObjectByExternalId("baseCentroidConfig", model.getType("GKCentroidConfiguration"))
    createTransitCentroidConnections(centroidConfig, nodeConnections, model, catalog, geomodel)
    overallEndTime = time.perf_counter()
    print(f"Overall runtime: {overallEndTime-overallStartTime}")
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
    networkPackageFile = inputArgs[2]
    outputNetworkFile = inputArgs[3]
    # generate a model of the input network
    model, catalog, geomodel = loadModel(Network, console)
    #run the _execute function
    _execute(networkPackageFile, model, console)
    saveNetwork(console, model, outputNetworkFile)

if __name__ == "__main__":
    # function to parse the command line arguments and run network script
    runFromConsole(sys.argv)
