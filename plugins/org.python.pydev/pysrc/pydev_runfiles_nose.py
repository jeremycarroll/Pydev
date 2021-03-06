from nose.plugins.multiprocess import MultiProcessTestRunner #@UnresolvedImport
from nose.plugins.base import Plugin #@UnresolvedImport
import sys
import pydev_runfiles_xml_rpc
import time
from pydev_runfiles_coverage import StartCoverageSupport

#=======================================================================================================================
# PydevPlugin
#=======================================================================================================================
class PydevPlugin(Plugin):
    
    def __init__(self, configuration):
        self.configuration = configuration
        Plugin.__init__(self)
        
    
    def begin(self):
        #Called before any test is run (it's always called, with multiprocess or not)
        self.start_time = time.time()
        self.coverage_files, self.coverage = StartCoverageSupport(self.configuration)
    
    
    def finalize(self, result):
        #Called after all tests are run (it's always called, with multiprocess or not)
        self.coverage.stop()
        self.coverage.save()

        pydev_runfiles_xml_rpc.notifyTestRunFinished('Finished in: %.2f secs.' % (time.time() - self.start_time,))
    
    
    
    #===================================================================================================================
    # Methods below are not called with multiprocess (so, we monkey-patch MultiProcessTestRunner.consolidate
    # so that they're called, but unfortunately we loose some info -- i.e.: the time for each test in this
    # process).
    #===================================================================================================================
    
    
    def reportCond(self, cond, test, captured_output, error=''):
        '''
        @param cond: fail, error, ok
        '''
        
        #test.address() is something as:
        #('D:\\workspaces\\temp\\test_workspace\\pytesting1\\src\\mod1\\hello.py', 'mod1.hello', 'TestCase.testMet1')
        #
        #and we must pass: location, test
        #    E.g.: ['D:\\src\\mod1\\hello.py', 'TestCase.testMet1']
        try:
            if hasattr(test, 'address'):
                address = test.address()
                address = address[0], address[2]
            else:
                #multiprocess
                try:
                    address = test[0], test[1]
                except TypeError:
                    #It may be an error at setup, in which case it's not really a test, but a Context object.
                    f = test.context.__file__
                    if f.endswith('.pyc'):
                        f = f[:-1]
                    address = f, '?'
        except:
            sys.stderr.write("PyDev: Internal pydev error getting test address. Please report at the pydev bug tracker\n")
            import traceback;traceback.print_exc()
            sys.stderr.write("\n\n\n")
            address = '?', '?'

        error_contents = self.getIoFromError(error)
        try:
            time_str = '%.2f' % (time.time() - test._pydev_start_time)
        except:
            time_str = '?'
            
        pydev_runfiles_xml_rpc.notifyTest(cond, captured_output, error_contents, address[0], address[1], time_str)
        
        
    def startTest(self, test):
        test._pydev_start_time = time.time()
        if hasattr(test, 'address'):
            address = test.address()
            file, test = address[0], address[2]
        else:
            #multiprocess
            file, test = test
        pydev_runfiles_xml_rpc.notifyStartTest(file, test)

    
    def getIoFromError(self, err):
        if type(err) == type(()):
            if len(err) != 3:
                if len(err) == 2:
                    return err[1] #multiprocess
            try:
                from StringIO import StringIO
            except:
                from io import StringIO
            s = StringIO()
            etype, value, tb = err
            import traceback;traceback.print_exception(etype, value, tb, file=s)
            return s.getvalue()
        return err
    
    
    def getCapturedOutput(self, test):
        if test.capturedOutput:
            return test.capturedOutput
        return ''
    
    
    def addError(self, test, err):
        self.reportCond(
            'error', 
            test, 
            self.getCapturedOutput(test),
            err, 
        )


    def addFailure(self, test, err):
        self.reportCond(
            'fail', 
            test, 
            self.getCapturedOutput(test),
            err, 
        )


    def addSuccess(self, test):
        self.reportCond(
            'ok', 
            test,
            self.getCapturedOutput(test),
            '',
        )
        
        
PYDEV_NOSE_PLUGIN_SINGLETON = None
def StartPydevNosePluginSingleton(configuration):
    global PYDEV_NOSE_PLUGIN_SINGLETON
    PYDEV_NOSE_PLUGIN_SINGLETON = PydevPlugin(configuration)
    return PYDEV_NOSE_PLUGIN_SINGLETON
        
        


original = MultiProcessTestRunner.consolidate
#=======================================================================================================================
# NewConsolidate
#=======================================================================================================================
def NewConsolidate(self, result, batch_result):
    '''
    Used so that it can work with the multiprocess plugin. 
    Monkeypatched because nose seems a bit unsupported at this time (ideally
    the plugin would have this support by default).
    '''
    ret = original(self, result, batch_result)
    
    parent_frame = sys._getframe().f_back
    #addr is something as D:\pytesting1\src\mod1\hello.py:TestCase.testMet4
    #so, convert it to what reportCond expects
    addr = parent_frame.f_locals['addr']
    i = addr.rindex(':')
    addr = [addr[:i], addr[i+1:]]
    
    output, testsRun, failures, errors, errorClasses = batch_result
    if failures or errors:
        for failure in failures:
            PYDEV_NOSE_PLUGIN_SINGLETON.reportCond('fail', addr, output, failure)
            
        for error in errors:
            PYDEV_NOSE_PLUGIN_SINGLETON.reportCond('error', addr, output, error)
    else:
        PYDEV_NOSE_PLUGIN_SINGLETON.reportCond('ok', addr, output)
        
    
    return ret
    
MultiProcessTestRunner.consolidate = NewConsolidate
