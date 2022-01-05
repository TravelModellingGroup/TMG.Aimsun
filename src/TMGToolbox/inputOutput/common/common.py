"""
    Copyright 2022 Travel Modelling Group, Department of Civil Engineering, University of Toronto

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
import os
import time
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
import shlex
import zipfile
import io

def extract_network_packagefile(network_package_file):
    """
    Function that is going to be migrated to common once resolved and 
    fully functional and working
    input the path to the network package
    this reads the zipfile and turns it to a zipfile object and returns it
    """
    print ('this function ran')
    #network_packgage_file = "C:\\Users\\sandhela\\source\\repos\\TravelModellingGroup\\TMG.Aimsun\\inputFiles\\Frabitztown.zip"
    zip_data_file = zipfile.ZipFile(network_package_file, 'r')
    #print (archive, dir(archive))
    #this could be used for error messaging list back all tools avaialble
    #print ( zip_data_file.infolist() )
    return zip_data_file

def read_datafile(binary_file):
    """
    a test function which we will read the file inside the zip file of interet using the iotextwrapper
    this is to access the data so the various functions can then extract the data
    """
    with io.TextIOWrapper(binary_file, encoding="utf-8") as f:
        lines = f.readlines()
        return lines
