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
import time
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
from importNetwork import loadModel
from importTransitNetwork import parseArguments, cacheAllOfTypeByExternalId, cacheNodeConnections

def definePedestrianType(model):
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

# Create a pedestrian layer and return the object
def createPedestrianLayer(model):
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
def createPedestrianCentroidConfigFolder(model):
    folderName = 'GKModel::pedestrianCentroidsConfiguration'
    folder = model.getCreateRootFolder().findFolder(folderName)
    if folder == None:
        folder = GKSystem.getSystem().createFolder(model.getCreateRootFolder(), folderName)
    return folder

# creates a pedestrian centroid configuration
def createPedestrianCentroidConfig(model):
    folder = createPedestrianCentroidConfigFolder(model)
    pedestrianCentroidConfig = GKSystem.getSystem().newObject( 'GKPedestrianCentroidConfiguration', model )
    pedestrianCentroidConfig.setName("Pedestrian Centroid Configuration")
    pedestrianCentroidConfig.setExternalId("ped_baseCentroidConfig")
    pedestrianCentroidConfig.setStatus(GKObject.eModified)
    pedestrianCentroidConfig.activate()
    folder.append(pedestrianCentroidConfig)
    return pedestrianCentroidConfig

def createSquarePedArea(centre, size, geomodel, layer, name, model):
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
def createGlobalPedArea(model, geomodel, catalog, layer, name):
    # Get all the nodes and centroids in model
    nodeType = model.getType("GKNode")
    nodes = GKPoints()
    for types in catalog.getUsedSubTypesFromType( nodeType ):
        for s in iter(types.values()):
            nodes.append(s.getPosition())
    centroidType = model.getType("GKCentroid")
    for types in catalog.getUsedSubTypesFromType( centroidType ):
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

def findNearbySections(centroid, nodeConnections, model):
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
def findNearbyStops(centroid, nodeConnections, model):
    nearbyStops = []
    nearbySections = findNearbySections(centroid, nodeConnections, model)
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

def createTransitCentroidConnections(centroidConfiguration, nodeConnections, model, catalog, geomodel):
    print("Create pedestrian centroid configuration")
    # create pedestrian layer
    pedestrianLayer = geomodel.findLayer("Pedestrians Layer")
    if pedestrianLayer is None:
        pedestrianLayer = createPedestrianLayer(model)
    # Create a new pedestrian centroid configuration
    pedCentroidConfig = createPedestrianCentroidConfig(model)
    centroids = centroidConfiguration.getCentroids()
    # Create a global pedestrian area
    pedArea = createGlobalPedArea(model, geomodel, catalog, pedestrianLayer, "full")
    # Create centroids and connect all nearby bus stops
    print("Create pedestiran centroids and connections")
    sectionType = model.getType("GKBusStop")
    for centroid in centroids:
        pedCentroids = list()
        # Get all nearby stops
        nearbyStops = findNearbyStops(centroid, nodeConnections, model)
        # If no stops found get the closest stop
        if nearbyStops is None:
            nearbyStops = [geomodel.findClosestObject(centroid.getPosition(), sectionType)]
        # If no stops found move to the next centroid
        if nearbyStops is not None:
            # check if there is an existing pedestrian centroid
            pedCentroidType = model.getType("GKPedestrianEntranceCentroid")
            entranceCentroid = catalog.findObjectByExternalId(f"ped_entrance_{centroid.getExternalId()}", pedCentroidType)
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

def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    networkDirectory = parameters["ModelDirectory"]
    _execute(networkDirectory, model, console)

def _execute(networkDirectory, inputModel, console):
    """ 
    Main execute function to run the simulation 
    """
    overallStartTime = time.perf_counter()
    loadModelStartTime = time.perf_counter()

    model = inputModel
    catalog = model.getCatalog()
    geomodel = model.getGeoModel()
    
    nodes = cacheAllOfTypeByExternalId("GKNode", model, catalog)
    sections = cacheAllOfTypeByExternalId("GKSection", model, catalog)
    nodeConnections = cacheNodeConnections(nodes.values(), sections.values())
    loadModelEndTime = time.perf_counter()
    print(f"Time to load model: {loadModelEndTime-loadModelStartTime}")
    pedStartTime = time.perf_counter()
    print("Add pedestrians")
    pedestrianType = definePedestrianType(model)
    centroidConfig = catalog.findObjectByExternalId("baseCentroidConfig", model.getType("GKCentroidConfiguration"))
    createTransitCentroidConnections(centroidConfig, nodeConnections, model, catalog, geomodel)
    pedEndTime = time.perf_counter()
    print(f"Time to import pedestrians: {pedEndTime-pedStartTime}")
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
    networkDirectory = inputArgs[2]
    outputNetworkFile = inputArgs[3]
    # generate a model of the input network
    model, catalog, geomodel = loadModel(Network, console)
    #run the _execute function
    _execute(networkDirectory, model, console)
    saveNetwork(console, model, outputNetworkFile)

if __name__ == "__main__":
    # function to parse the command line arguments and run network script
    runFromConsole(sys.argv)
