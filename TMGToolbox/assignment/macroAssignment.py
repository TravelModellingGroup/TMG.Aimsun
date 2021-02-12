from PyANGBasic import *
from PyANGKernel import *
from PyANGDTA import *
from PyMacroKernelPlugin import *
from PyMacroToolPlugin import *
from PyMacroAdjustmentPlugin import *
from PyMacroPTPlugin import *
import sys
import os

sys.path.append(xtmf['toolboxPath'])
import utilities as _util

system = GKSystem.getSystem()
model = system.getActiveModel()
print
'got model'
cmd = model.createNewCmd(model.getType("MacroScenario"))
model.getCommander().addCommand(cmd)
scenario = cmd.createdObject()
scenario.setDemand(model.getCatalog().find(int(xtmf_parameters["matrix"])))
print
'created scenario %d' % int(scenario.getId())

cmd1 = model.createNewCmd(model.getType("GKPathAssignment"))
model.getCommander().addCommand(cmd1)
PathAssignment = cmd1.createdObject()
print
'created path assignment %d in %s with the name of %s' % (
	int(PathAssignment.getId()), str(PathAssignment.getFolderPath()), str(PathAssignment.getFileName()))

inputData = scenario.getOutputData()
inputData.setGenerateSkims(1)
inputData.setActivatePathStatistics(True)

scenario.setOutputData(inputData)

'''cmd2 = model.createNewCmd( model.getType( "MacroExperiment" ))
cmd2.setScenario( scenario )
model.getCommander().addCommand( cmd2 )
experiment = cmd2.createdObject()
experiment.setEngine('FrankeWolfe')
experiment.setOutputPathAssignment(PathAssignment)'''

experiment = GKSystem.getSystem().newObject("MacroExperiment", model)
experiment.setEngine("FrankWolfe")
params = experiment.createParameters()
params.setMaxIterations(50)
params.setMaxRelativeGap(0.001)

params.setFrankWolfeMethod(0)
experiment.setParameters(params)
experiment.setScenario(scenario)
experiment.setOutputPathAssignment(PathAssignment)
model.getCatalog().add(experiment)
print
"created experiment with id %d" % int(experiment.getId())

system.executeAction("execute", experiment, [], "static assignment")

skims = experiment.getOutputData().getSkimMatrices(model)
for skim in skims:
	name = "D:\Users\Bilal\Documents\GTA_AIMSUN\\" + str(skim.getId()) + "_" + str(
		skim.getVehicle().getId()) + "_" + str(skim.getVehicle().getName()) + "_" + str(
		skim.getFrom().toString()) + "_" + str(skim.getDuration().toString()) + ".csv"
	print
	name
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


