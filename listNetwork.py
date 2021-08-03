import sys
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *

def listAllOfType(typeName):
    sectionType = model.getType(typeName)
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            print("Section ID: %i Name: %s" % (s.getId(), s.getName()))
            print(f"Length: {s.length2D()}")
            print(f"Points: {s.nbPoints()}")
            print(f"Lanes: {s.getNbFullLanes()}")
            print(f"Lane Lengths: {s.getLanesLength2D()}")


def main(argv):
    if len(argv) < 2:
        print("Incorrect Number of Arguments")
        print("Arguments: -script script.py aimsunProjectFile.ang")
        return -1
    # Start a console
    console = ANGConsole()
    # Load a network
    if console.open(argv[1]): 
        global model
        model = console.getModel()
        print("network open")
    else:
        console.getLog().addError("Cannot load the network")
        print("cannot load network")
    print("Nodes")
    sectionType = model.getType("GKNode")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            print("Node ID: %i Name: %s" % (s.getId(), s.getName()))
            print(f"Number of Entrance Sections {s.getNumEntranceSections()}")
            print(f"Number of Exit Sections {s.getNumExitSections()}")

    print("Links (Sections)")
    sectionType = model.getType("GKSection")
    for types in model.getCatalog().getUsedSubTypesFromType( sectionType ):
        for s in iter(types.values()):
            print("Section ID: %i Name: %s" % (s.getId(), s.getName()))
            print(f"Length: {s.length2D()}")
            print(f"Points: {s.nbPoints()}")
            print(f"Lanes: {s.getNbFullLanes()}")
            print(f"Lane Lengths: {s.getLanesLength2D()}")
            # print(f"From node: {s.getOrigin().getName()}, To node: {s.getDestination().getName()}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
