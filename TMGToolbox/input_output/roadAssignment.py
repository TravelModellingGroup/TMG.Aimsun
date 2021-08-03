# Load in the required libraries
import sys
import time
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
import shlex
import csv

# Function reads the csv file with the OD volumes
# csv file should have a header row
# columns should be fromNode, toNode, volumes
def readOdMatrix(filename):
    fromNodes = []
    toNodes = []
    volumes = []
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for line in reader:
            fromNodes.append(line[0])
            toNodes.append(line[1])
            volumes.append(float(line[2]))
    return fromNodes, toNodes, volumes

# Function checks for or creates a centroid and return the centroid
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
    nodeConnection = GKSystem.getSystem().newObject("GKObjectConnection", model)
    nodeConnection.setOwner(centroid)
    nodeConnection.setConnectionObject(node)
    centroid.addConnection(nodeConnection)
    centroid.setPositionByConnections()
    # add the centroid to the geomodel
    model.getGeoModel().add(node.getLayer(),centroid)
    return centroid

# Create centroid configuration
def createCentroidConfiguation(name, listOfCentroidIds):
    print("create centroid config object")
    cmd = model.createNewCmd(model.getType("GKCentroidConfiguration"))
    model.getCommander().addCommand( cmd )
    centroidConfig = cmd.createdObject()
    centroidConfig.setName(name)
    print("create and add the centroids")
    for centroidId in listOfCentroidIds:
        centroid = createCentroid(centroidId)
        if centroidConfig.contains(centroid):
            continue
        centroidConfig.addCentroid(centroid)
    
    for c in centroidConfig.getCentroids():
        print(c.getExternalId())
        print(f"Connections from {c.getNumberConnectionsFrom()}")
        print(f"Connections to {c.getNumberConnectionsTo()}")
        print(c.getLayer().getName())
    # save the centroid configuration
    print("save to folder")
    folderName = "GKModel::centroidsConf"
    folder = model.getCreateRootFolder().findFolder( folderName )
    if folder == None:
        folder = GKSystem.getSystem().createFolder( model.getCreateRootFolder(), folderName )
    folder.append(centroidConfig)
    return centroidConfig

# TODO create the OD matrix (set trips)
# TODO make the traffic demand object
# TODO run static traffic assignment

def main(argv):
    overallStartTime = time.perf_counter()
    if len(argv) < 4:
        print("Incorrect Number of Arguments")
        print("Arguments: -script script.py aimsunNetworkFile.ang odMatrix.csv outputNetworkFile.ang")
        return -1
    # Start a console
    console = ANGConsole()
    # Load a network
    if console.open(argv[1]): 
        global model
        model = console.getModel()
        print("open network")
    else:
        console.getLog().addError("Cannot load the network")
        print("cannot load network")
        return -1
    print("Open OD matrix file")
    odMatrixFile = argv[2]
    fromNodes, toNodes, volumes = readOdMatrix(odMatrixFile)
    print("Create Centroid configuration")
    centroidConfig = createCentroidConfiguation("testConfig", fromNodes)
    print("Save Network")
    console.save(argv[3])
    overallEndTime = time.perf_counter()
    print(f"Overall Runtime: {overallEndTime-overallStartTime}s")
    # Reset the Aimsun undo buffer
    model.getCommander().addCommand( None )

    return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
