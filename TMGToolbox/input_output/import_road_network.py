import sys
from PyANGKernel import *
from PyANGApp import *
from PyANGConsole import *
from PyANGKernel import *

'''
'''
class ImportRoadNetwork:

    def __init__(argv: list):
        '''

        '''
        pass

    def run(self):
        '''

        :return:
        '''
        print('inside run')

        return 0


if __name__ == "__main__":
    console = ANGConsole()

    print(sys.argv[1])
    if console.open(sys.argv[1]):
        model = console.getModel()
        print(dir(model))
        console.save(sys.argv[1])
        console.close()
    else:
        print('unable to open model.')
        console.close()

    tool = ImportRoadNetwork()
    result = tool.run()
    sys.exit(result)
