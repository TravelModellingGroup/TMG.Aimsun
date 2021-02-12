import ast
from AimsunBridge import stackList
from PyANGBasic import *
from PyANGKernel import *
from PyANGConsole import *
import sys
import os
import warnings as _warn
import traceback as _tb
import subprocess as _sp


##argv = [ABridgeLocation, networkLocation, scriptLocation, parameters]
##"C:\Program Files\Aimsun\Aimsun Next 8.3\aconsole.exe" -script "D:\Users\Bilal\Desktop\ABridgeTest.py" "D:\Users\Bilal\Documents\GTA_AIMSUN\Tutorial1.ang" "D:\Users\Bilal\Desktop\AScriptTest.py" "{'type':'GKSection'}"
##"C:\Program Files\Aimsun\Aimsun Next 8.3\aconsole.exe" -script "D:\Users\Bilal\Desktop\ABridgeTest.py" "D:\Users\Bilal\Documents\GTA_AIMSUN\Tutorial1.ang" "D:\Users\Bilal\Desktop\AScriptTest2.py" "{'simulatorEngine':'eMicro', 'engineMode':'eOneShot', 'matrix':'1212'}"
##"C:\Program Files\Aimsun\Aimsun Next 8.3\aconsole.exe" -script "D:\Users\Bilal\Desktop\ABridgeTest.py" "D:\Users\Bilal\Documents\GTA_AIMSUN\MacroTutorial.ang" "D:\Users\Bilal\Desktop\AScriptTestMacroAssignment.py" "{'simulatorEngine':'eMicro', 'engineMode':'eOneShot', 'matrix':'1212'}"
##"C:\Program Files\Aimsun\Aimsun Next 8.3\aconsole.exe" -script "D:\Users\Bilal\Source\Repos\TMG.Aimsun\TMG.Aimsun\AimsunBridge.py" "D:\Users\Bilal\Documents\GTA_AIMSUN\MacroTutorial.ang" "D:\Users\Bilal\Source\Repos\TMG.Aimsun\TMGToolbox\assignment\macroAssignment.py" "{'toolboxPath':'D:\Users\Bilal\Source\Repos\TMG.Aimsun\TMGToolbox\','matrix':'1212'}"
def main( argv ):
    if len( argv ) < 4:
        raise Exception("Not enough arguments supplied. \n\
                         The format should be '-script ABridgeLocation networkLocation, scriptLocation, parameters'")
        return -1
    # Start a Console
    console = ANGConsole()
    # Load the network
    try:
        console.open(argv[1])
        model = console.getModel()
        # read the Tool
        with open(argv[2]) as codeFile:
            scriptCode = str(codeFile.read())
        # Add parameters to the tool
        try:
            nameSpace = {'xtmf_parameters': ast.literal_eval(str(argv[3]))}
        except:
            raise Exception("Please check xtmf parameters")
        # Execute the tool
        try:
            print
            "Executing Tool %s" % (argv[2])
            exec(scriptCode, nameSpace)
        except Exception as e:
            eType, eVal, eTb = sys.exc_info()
            stackList = _tb.extract_tb(eTb)
            msg = "%s: %s\n\n\Stack trace below:" % (eVal.__class__.__name__, str(eVal))
            stackList.reverse()
            for file, line, func, text in stackList:
                msg += "\n  File '%s', line %s, in %s" % (file, line, func)
            print
            msg
    except:
        print
        "Could not load network"
    finally:
        console.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv))



