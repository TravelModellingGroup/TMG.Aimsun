# Load in the required libraries
import sys
import datetime
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
import shlex
import csv
from importTransitNetwork import readTransitFile

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

def buildTransitVehDict(transitFile):
    transitVehDict = dict()
    vehType = model.getType("GKVehicle")
    node, stops, lines = readTransitFile(transitFile)
    for i in range(len(lines)):
        lineId = lines[i][0]
        lineVehicle = model.getCatalog().findObjectByExternalId(f"transitVeh_{lines[i][2]}", vehType)
        transitVehDict[lineId] = lineVehicle
    return transitVehDict

# Function uses the dummy link at the start of the transit line to find the transit vehicle
def findTransitVehicle(transitLine, transitVehDict):
    lineId = transitLine.getExternalId()
    transitVehicle = transitVehDict[lineId]
    return transitVehicle

def addServiceToLine(lineId, departures, arrivals, transitVehDict, vehicle=None):
    sectionType = model.getType("GKPublicLine")
    transitLine = model.getCatalog().findObjectByExternalId(lineId, sectionType)
    if transitLine is None:
        print(f"Could not find line {lineId}")
        return None
    timeTable = GKSystem.getSystem().newObject("GKPublicLineTimeTable", model)
    schedule = timeTable.createNewSchedule()
    startTime = departures[0].split(":")
    hour = int(startTime[0])
    minute = int(startTime[1])
    second = int(startTime[2])
    if hour>23:
        hour = 23
        minute = 59
        second = 59
    startTimeTime = datetime.time(hour,minute,second)
    schedule.setTime(startTimeTime)
    endTime = arrivals[-1].split(":")
    hour = int(endTime[0])
    minute = int(endTime[1])
    second = int(endTime[2])
    if hour>23:
        hour = 23
        minute = 59
        second = 59
    endTimeTime = datetime.time(hour,minute,second)
    timeDelta = (datetime.datetime.combine(datetime.date.today(),endTimeTime)-datetime.datetime.combine(datetime.date.today(),startTimeTime)).total_seconds()
    duration = GKTimeDuration(0,0,0)
    duration = duration.addSecs(timeDelta)
    schedule.setDuration(duration)
    departureVeh = vehicle
    if departureVeh is None:
        departureVeh = findTransitVehicle(transitLine, transitVehDict)
    for d in departures:
        timeElements = d.split(":")
        hour = int(timeElements[0])
        minute = int(timeElements[1])
        second = int(timeElements[2])
        if hour>23:
            hour = 23
            minute = 59
            second = 59
        departureTime = datetime.time(hour,minute,second)
        departure = GKPublicLineTimeTableScheduleDeparture()
        departure.setDepartureTime(departureTime)
        departure.setVehicle(departureVeh)
        schedule.addDepartureTime(departure)
    # add in dwell times
    stops = transitLine.getStops()
    for stop in stops:
        if stop is not None:
            stopTime = GKPublicLineTimeTableScheduleStopTime()
            # stop time determined based on pedestrians during simulation
            stopTime.pedestriansToGenerate = 0 # Aimsun will use HCM to determine time for on/off
            schedule.setStopTime(stop, 1, stopTime)
    timeTable.addSchedule(schedule)
    transitLine.addTimeTable(timeTable)
    return transitLine

def main(argv):
    print("Import transit schedules")
    if len(argv)<5:
        print("Incorrect Number of Arguments")
        print("Arguments: -script script.py aimsunProjectFile.ang serviceTable.csv transitFile.221 outputNetworkFile.ang")
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
    transitFile = argv[3]
    transitVehDict = buildTransitVehDict(transitFile)
    serviceTables = readServiceTables(argv[2])
    for serviceTable in serviceTables:
        addServiceToLine(serviceTable[0], serviceTable[1], serviceTable[2], transitVehDict)
    # Save the network file
    print("Save Network")
    console.save(argv[4])
    return 0

if __name__ == "__main__":
    main(sys.argv)