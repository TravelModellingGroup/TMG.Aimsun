from PyANGBasic import *
from PyANGKernel import *
from PyANGDTA import *
from PyMacroKernelPlugin import *
from PyMacroToolPlugin import *
from PyMacroAdjustmentPlugin import *
from PyMacroPTPlugin import *


system = GKSystem.getSystem()
model = system.getActiveModel()
print 'got model'
cmd1 = model.createNewCmd( model.getType( "GKScenario" ))
model.getCommander().addCommand( cmd1 )
scenario = cmd1.createdObject()
scenario.setDemand(model.getCatalog().find(int(xtmf_parameters["matrix"])))
print 'created scenario'


cmd2 = model.createNewCmd( model.getType( "GKExperiment" ))
cmd2.setScenario( scenario )
model.getCommander().addCommand( cmd2 )
experiment = cmd2.createdObject()

if str(xtmf_parameters["simulatorEngine"]) == "eMicro":
    experiment.setEngineMode( GKExperiment.EngineMode(0))
elif str(xtmf_parameters["simulatorEngine"]) == "eMeso":
    experiment.setEngineMode( GKExperiment.EngineMode(1))
elif str(xtmf_parameters["simulatorEngine"]) == "eHybrid":
    experiment.setEngineMode( GKExperiment.EngineMode(2))
elif str(xtmf_parameters["simulatorEngine"]) == "eDynamicMacro":
    experiment.setEngineMode( GKExperiment.EngineMode(3))


if xtmf_parameters["engineMode"] == "eIterative":
    experiment.setSimulatorEngine(0)
elif xtmf_parameters["engineMode"] == "eOneShot":
    experiment.setSimulatorEngine(1)




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



model.getCommander().addCommand( None )


