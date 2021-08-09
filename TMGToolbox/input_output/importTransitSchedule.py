# Load in the required libraries
import sys
import datetime
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
import shlex
import csv

def readServiceTables(fileLocation, header=True):
    serviceTables = []
    transitLine = None
    departures = []
    arrivals = []
    with open(fileLocation) as csvfile:
        reader = csv.reader(csvfile)
        if header is True:
            next(reader)
        for line in reader:
            # Check that the line has reuqired number of values
            if len(line) >= 3:
                # if there is a change in the transit line being read add to the output
                if transitLine != None and line[0] != transitLine:
                    serviceTables.append((transitLine, departures, arrivals))
                    transitLine = None
                    departures = []
                    arrivals = []
                # Read the current line in
                transitLine = line[0]
                departures.append(line[1])
                arrivals.append(line[2])
    # add in the last line
    if transitLine != None:
        serviceTables.append((transitLine, departures, arrivals))
    return serviceTables

# Function uses the dummy link at the start of the transit line to find the transit vehicle
def findTransitVehicle(transitLine):
    transitVehicle = None
    vehType = model.getType("GKVehicle")
    sectionType = model.getType("GKSection")
    dummyLinkId = f"dummylink_{transitLine.getExternalId()}"
    dummyLink = model.getCatalog().findObjectByExternalId(dummyLinkId, sectionType)
    for types in model.getCatalog().getUsedSubTypesFromType( vehType ):
        for veh in iter(types.values()):
            if dummyLink.canUseVehicle(veh) is True:
                transitVehicle = veh
                return transitVehicle
    return transitVehicle

def addServiceToLine(lineId, departures, arrivals, vehicle=None):
    sectionType = model.getType("GKPublicLine")
    transitLine = model.getCatalog().findObjectByExternalId(lineId, sectionType)
    timeTable = GKSystem.getSystem().newObject("GKPublicLineTimeTable", model)
    schedule = timeTable.createNewSchedule()
    startTime = departures[0].split(":")
    startTimeTime = datetime.time(int(startTime[0]),int(startTime[1]),int(startTime[2]))
    schedule.setTime(startTimeTime)
    endTime = arrivals[-1].split(":")
    endTimeTime = datetime.time(int(endTime[0]),int(endTime[1]),int(endTime[2]))
    timeDelta = (datetime.datetime.combine(datetime.date.today(),endTimeTime)-datetime.datetime.combine(datetime.date.today(),startTimeTime)).total_seconds()
    duration = GKTimeDuration(0,0,0)
    duration = duration.addSecs(timeDelta)
    schedule.setDuration(duration)
    departureVeh = vehicle
    if departureVeh is None:
        departureVeh = findTransitVehicle(transitLine)
    for d in departures:
        timeElements = d.split(":")
        departureTime = datetime.time(int(timeElements[0]),int(timeElements[1]),int(timeElements[2]))
        departure = GKPublicLineTimeTableScheduleDeparture()
        departure.setDepartureTime(departureTime)
        departure.setVehicle(departureVeh)
        schedule.addDepartureTime(departure)
    # TODO add in the dwell times
    timeTable.addSchedule(schedule)
    transitLine.addTimeTable(timeTable)
    return transitLine

def main(argv):
    print("Import transit schedules")
    if len(argv)<4:
        print("Incorrect Number of Arguments")
        print("Arguments: -script script.py aimsunProjectFile.ang serviceTable.csv outputNetworkFile.ang")
        return 1
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
    serviceTables = readServiceTables(argv[2])
    for serviceTable in serviceTables:
        addServiceToLine(serviceTable[0], serviceTable[1], serviceTable[2])
    # Save the network file
    print("Save Network")
    console.save(argv[3])
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))