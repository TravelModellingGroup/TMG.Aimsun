# Load in the required libraries
import sys
import time
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *

def readFile(filename):
    lines = []
    nodes = []
    links = []
    currentlyReading = 'nodes'
    with open(filename, 'r') as f:
        lines = f.readlines()
    for line in lines:
        if line[0] == 'c':
            continue
        elif line[0] == 't':
            currentlyReading = line.split()[1]
        elif line[0] == 'a':
            if currentlyReading == 'nodes':
                nodes.append(line.split())
            elif currentlyReading == 'links':
                links.append(line.split())
    
    # test if the function is working properly
    # for node in nodes:
    #     print(node)
    # for link in links:
    #     print(link)

    return links, nodes

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
    # Add node to the active layer
    # layer = model.getGeoModel().getActiveLayer()
    # model.getGeoModel().add(layer, newNode)

def addLink(link):
    # Create the link
    newLink = GKSystem.getSystem().newObject("GKSection", model)
    # Set the name to reflect start and end nodes
    newLink.setName(f"link{link[1]}_{link[2]}")
    # newLink.setName(f"link{linkNumber}")

    # Set the start and end nodes for the link
    sectionType = model.getType("GKNode")
    # fromNode = model.getCatalog().findByName(f"node{link[1]}", sectionType, True)
    fromNode = model.getCatalog().findObjectByExternalId(link[1], sectionType)
    newLink.setOrigin(fromNode)
    # toNode = model.getCatalog().findByName(f"node{link[2]}", sectionType, True)
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
    # originConnection.setConnectionType(0)
    destinationConnection = GKSystem.getSystem().newObject("GKObjectConnection", model)
    destinationConnection.setOwner(toNode)
    destinationConnection.setConnectionObject(newLink)
    toNode.addConnection(destinationConnection)
    # destinationConnection.setConnectionType(0)
    

    # add the lanes
    numberOfLanes = int(float(link[6]))
    # cmd = GKSectionChangeNbLanesCmd()
    # model.getCommander().addCommand(cmd)
    # cmd.setData(newLink, numberOfLanes)
    for l in range(numberOfLanes):
        # lane = GKSystem.getSystem().newObject("GKSectionLane", model)
        lane = GKSectionLane()
        newLink.addLane(lane)
    #TODO add set the allowed modes on the link
    #TODO add the type, not sure how to represent this
    #TODO add the volume delay function
    # Add Data 2 which is free flow speed
    freeFlowSpeed = float(link[9])
    newLink.setSpeed(freeFlowSpeed)
    # Add Data 3 which is capacity per lane per hour
    capacityPerLane = float(link[10])
    newLink.setCapacity(float(numberOfLanes) * capacityPerLane)
    # Add the link to the active layer
    # layer = model.getGeoModel().getActiveLayer()
    # model.getGeoModel().add(layer, newLink)

def buildTurnings():
    # Get all of the links and nodes
    print("Adding lane turnings")
    # Assume that all links that are connected by nodes have all lanes 
    # turning to each other
    nodeType = model.getType("GKNode")

    geomodel = model.getGeoModel()
    # layer = model.getGeoModel().getActiveLayer()
    for types in model.getCatalog().getUsedSubTypesFromType( nodeType ):
        for node in iter(types.values()):
            # print(f"node: {node.getName()}")
            linksIn = []
            linksOut = []
            linkType = model.getType("GKSection")
            connectedLinks = node.getConnections()
            for linkConnection in iter(connectedLinks):
                link = linkConnection.getConnectionObject()
                # print(f"connected link: {link.getName()}")
                origin = link.getOrigin()
                destination = link.getDestination()
                if origin == node:
                    linksOut.append(link)
                if destination == node:
                    linksIn.append(link)
            # This uses the builtin function to find links within 1m of the node
            # nearbyLinks = geomodel.findClosestObjects(node.getPosition(), 1.0, linkType)
            # for link in nearbyLinks:
            #     origin = link.getOrigin()
            #     destination = link.getDestination()
            #     if origin == node:
            #         linksOut.append(link)
            #     if destination == node:
            #         linksIn.append(link)
            # This looks through all the links to find the ones connected to the node
            # for linkTypes in model.getCatalog().getUsedSubTypesFromType( linkType ):
            #     for link in iter(linkTypes.values()):
            #         origin = link.getOrigin()
            #         destination = link.getDestination()
            #         if origin == node:
            #             linksOut.append(link)
            #         if destination == node:
            #             linksIn.append(link)
            for entering in linksIn:
                # print(f"from link: {entering.getName()}")
                for exiting in linksOut:
                    # print(f"to link: {exiting.getName()}")
                    newTurn = GKSystem.getSystem().newObject("GKTurning", model)
                    newTurn.setConnection(entering, exiting)
                    node.addTurning(newTurn, True)
                    # Add the link to the active layer
                    # model.getGeoModel().add(layer, newTurn)
    print("Complete")

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
    

def main(argv):
    overallStartTime = time.perf_counter()
    if len(argv) < 4:
        print("Incorrect Number of Arguments")
        print("Arguments: -script script.py blankAimsunProjectFile.ang baseNetowrkFile.211 outputNetworkFile.ang")
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
    # print("Set Active Layer Draw Mode")
    # layer = model.getGeoModel().getActiveLayer()
    # print(layer.getDrawMode())
    # layer.setDrawMode(1)
    # print(layer.getDrawMode())
    print("Read Data File")
    # File for Frabitztown Test Network
    # links, nodes = readFile('Y:/Research/2021/AimsunScripts/Frabitztown/base.211')
    # File for Toronto
    links, nodes = readFile(argv[2])
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
        addLink(link)
        # output the progress of the import
        if (counter % infoStepSize) == 0:
            print(f"{counter} links added")
    linkEndTime = time.perf_counter()
    print(f"Link Import Time: {linkEndTime-linkStartTime}s")
    turnStartTime = time.perf_counter()
    buildTurnings()
    turnEndTime = time.perf_counter()
    print(f"Time to Build Turns: {turnEndTime-turnStartTime}s")

    layer = model.getGeoModel().findLayer("Network")
    drawLinksAndNodes(layer)

    
    print("Finished Import")
    print("Save Network")
    console.save(argv[3])

    overallEndTime = time.perf_counter()
    print(f"Overall Runtime: {overallEndTime-overallStartTime}s")

# This node positions is in the Aimsun docs as needed for macro models
# print("Update Node Positions")
# sectionType = model.getType("GKNode")
# for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
#     for s in iter(types.values()):
#         s.updatePosition()

if __name__ == "__main__":
    sys.exit(main(sys.argv))