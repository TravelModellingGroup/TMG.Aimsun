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
    Function which takes a zipped file in this case the networkpackage file and
    returns a ZipFile object which can be further used 
    input: string path to zip file
    return: ZipFile object
    """
    zip_data_file = zipfile.ZipFile(network_package_file, 'r')
    return zip_data_file

def read_datafile(networkZipFileObject, filename):
    """
    Function takes ZipFileObject and filename to open the file and read the lines.
    Returns a list of the extract data for further processing.
    input: ZipFile object 
    input2: string filename
    return: a List of the data in string format 
    """
    fileToOpen = networkZipFileObject.open(filename)
    with io.TextIOWrapper(fileToOpen, encoding="utf-8") as f:
        lines = f.readlines()
        return lines


#this could be used for error messaging list back all tools avaialble
#print ( zip_data_file.infolist() )