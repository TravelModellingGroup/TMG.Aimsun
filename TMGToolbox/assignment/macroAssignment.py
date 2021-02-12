from PyANGBasic import *
from PyANGKernel import *
from PyANGDTA import *
from PyMacroKernelPlugin import *
from PyMacroToolPlugin import *
from PyMacroAdjustmentPlugin import *
from PyMacroPTPlugin import *
from PyFrankWolfePlugin import *
import sys
import os
sys.path.append( xtmf_parameters['toolboxPath'] )
from common import utilities as _util


system = GKSystem.getSystem()
model = system.getActiveModel()
print 'got model'
cmd = model.createNewCmd( model.getType( "MacroScenario" ))
model.getCommander().addCommand( cmd )
scenario = cmd.createdObject()
scenario.setDemand(model.getCatalog().find(int(xtmf_parameters["matrix"])))
print 'created scenario %d' % int(scenario.getId())

cmd1 = model.createNewCmd( model.getType( "GKPathAssignment" ))
model.getCommander().addCommand( cmd1 )
PathAssignment = cmd1.createdObject()
print 'created path assignment %d in %s with the name of %s' % (int(PathAssignment.getId()), str( PathAssignment.getFolderPath()), str(PathAssignment.getFileName()))

dataToOutput = scenario.getOutputData()
dataToOutput.setGenerateSkims(1)

scenario.setOutputData(dataToOutput)

'''cmd2 = model.createNewCmd( model.getType( "MacroExperiment" ))
cmd2.setScenario( scenario )
model.getCommander().addCommand( cmd2 )
experiment = cmd2.createdObject()
experiment.setEngine('FrankeWolfe')
experiment.setOutputPathAssignment(PathAssignment)'''

'''experiment = GKSystem.getSystem().newObject( "MacroExperiment", model )
experiment.setEngine("FrankWolfe")
params = experiment.createParameters()
params.setMaxIterations ( 50 )
params.setMaxRelativeGap ( 0.001 )
params.setFrankWolfeMethod ( 0 )
experiment.setParameters( params ) '''

experiment = GKSystem.getSystem().newObject( "MacroExperiment", model )
experiment.setEngine( "FrankWolfe" )
params = experiment.createParameters()
params.setMaxIterations ( 50 )
params.setMaxRelativeGap ( 0.001 )
params.setFrankWolfeMethod ( CFrankWolfeParams.eNormal )
experiment.setParameters( params )


model.getCatalog().add( experiment )

print "created experiment with id %d" %int(experiment.getId())

experiment.setScenario( scenario )
experiment.setOutputPathAssignment( PathAssignment )


system.executeAction( "execute", experiment, [], "static assignment")
experiment.getStatsManager().createTrafficState()

skims = experiment.getOutputData().getSkimMatrices(model)
for skim in skims:
    def convert_to_int(time):
        time = time.split(':')
        return str(time[0])+str(time[1])+str(time[2])
    int_start_time = convert_to_int(skim.getFrom().toString())
    int_duration_time = convert_to_int(skim.getDuration().toString())
    name = "D:\Users\Bilal\Documents\GTA_AIMSUN\\" + str(skim.getId()) + "_" + str(skim.getVehicle().getId())+ "_"+ str(skim.getVehicle().getName())+ "_" + int_start_time + "_" + int_duration_time + ".csv"
    print name
    _util.exportMatrixCSV(name, skim)


'''
replication = system.newObject( "GKReplication", model )
replication.setExperiment(experiment)
print 'created replication'
cmd3 = model.createNewCmd( model.getType( "GKPathAssignment" ))
model.getCommander().addCommand( cmd3 )
res = cmd.createdObject()
cool = system.executeAction( "execute", replication, [], "")
print cool
print 'executed replication'
print replication.getId()
GKSystem.getSystem().executeAction( "retrieve", replication, [], "" )
'''


model.getCommander().addCommand( None )