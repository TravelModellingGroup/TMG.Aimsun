"""
    Copyright 2022 Travel Modelling Group, Department of Civil Engineering, University of Toronto

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
import datetime
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
import csv
from common.common import extract_network_packagefile, getTransitNodesStopsAndLinesFromNWP, loadModel


def readServiceTables(fileLocation, header=True):
    """Read and parse the ServiceTableCV csv file
    input: the servicetable csv file
    output: servicetables list
    """
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

def buildTransitVehDict(networkZipFileObject, model):
    transitVehDict = dict()
    vehType = model.getType("GKVehicle")
    node, stops, lines = getTransitNodesStopsAndLinesFromNWP(networkZipFileObject)
    for i in range(len(lines)):
        lineId = lines[i][0]
        lineVehicle = model.getCatalog().findObjectByExternalId(f"transitVeh_{lines[i][2]}", vehType)
        transitVehDict[lineId] = lineVehicle
    return transitVehDict


def findTransitVehicle(transitLine, transitVehDict):
    """
    Function uses the dummy link at the start of the transit line to find the transit vehicle
    """
    lineId = transitLine.getExternalId()
    transitVehicle = transitVehDict[lineId]
    return transitVehicle

def addServiceToLine(model, lineId, departures, arrivals, transitVehDict, vehicle=None):
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

def run_xtmf(parameters, model, console):
    """
    A general function called in all python modules called by bridge. Responsible
    for extracting data and running appropriate functions.
    """
    _execute(model, console, parameters)

def _execute(model, console, parameters):
    """
    Main execute function to run the tool
    """
    networkPackage = parameters["NetworkPackageFile"]
    # ZipFile object of the network file do this once
    networkZipFileObject = extract_network_packagefile(networkPackage)
    
    # get the transitfile
    transitVehDict = buildTransitVehDict(networkZipFileObject, model)
    
    serviceTables = readServiceTables(parameters["ServiceTableCSV"])
    for serviceTable in serviceTables:
        addServiceToLine(model, serviceTable[0], serviceTable[1], serviceTable[2], transitVehDict)
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

    #extract the arguments from the command line
    #incoming network
    Network = inputArgs[1]
    #output network file name
    outputNetworkFile = inputArgs[4]
    #create a dictionary of additional argument parameters from the command line
    parameters = {
                    "TransitFile":inputArgs[3],
                    "ServiceTableCSV": inputArgs[2]
                 }
    # generate a model of the input network
    model, catalog, geomodel = loadModel(Network, console)
    #run the _execute function
    _execute(model, console, parameters)
    saveNetwork(console, model, outputNetworkFile)

if __name__ == "__main__":
    # function to parse the command line arguments and run network script
    runFromConsole(sys.argv)
