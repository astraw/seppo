# seppo.py
"""simple embarrassingly parallel python"""
import sys, math, time

import Pyro.core
import Pyro.naming
from Pyro.protocol import getHostname
import Pyro.protocol
import Pyro.util
from Pyro.errors import PyroError,NamingError

__all__ = ['map_parallel']

Pyro.config.PYRO_MOBILE_CODE = True
Pyro.config.PYRO_MULTITHREADED = 0 # We do the multithreading around here...

Pyro.config.PYRO_TRACELEVEL = 3
Pyro.config.PYRO_USER_TRACELEVEL = 3
Pyro.config.PYRO_DETAILED_TRACEBACK = 1
Pyro.config.PYRO_PRINT_REMOTE_TRACEBACK = 1
Pyro.config.PYRO_NS_DEFAULTGROUP=':seppo'

class SeppoWorker(Pyro.core.ObjBase):
    def register_done_callback( self, func, val_list, done_callback_proxy ):
        results = [func(v) for v in val_list]
        done_callback_proxy.done( results )

def start_seppo_enslaved_server(hostname=None,port=9876):
    if hostname is None:
        hostname = ''
    
    Pyro.core.initServer(banner=0)
    # locate the NS
    daemon = Pyro.core.Daemon()
    locator = Pyro.naming.NameServerLocator()
    ns = locator.getNS()
    # make sure our namespace group exists
    try:
        ns.createGroup(Pyro.config.PYRO_NS_DEFAULTGROUP)
    except NamingError:
        pass

    daemon.useNameServer(ns)

    obj = SeppoWorker()
    objName=Pyro.util.getGUID()
    daemon.connect(obj,objName)

    # enter the service loop.
    try:
            # daemon.setTimeout(5)
            daemon.requestLoop()
    except KeyboardInterrupt:
            # allow shut down gracefully
            pass
    daemon.disconnect(obj)
    daemon.shutdown()

class SeppoDoneCallbackListener(Pyro.core.ObjBase):
    def done(self,results):
        self.seppo_results = results

class SeppoPyroProxyHolder:
    def __init__(self):
        Pyro.core.initClient(banner=0)
        self.refind_workers()

    def refind_workers(self):
	# locate the NS
	locator = Pyro.naming.NameServerLocator()
	ns = locator.getNS()

        #self.worker_list = ns.list(Pyro.config.PYRO_NS_DEFAULTGROUP)
        vts = ns.list(Pyro.config.PYRO_NS_DEFAULTGROUP)
        names = []
        for v,t in vts:
            if t==1: # leaf
                names.append( v )
        self.worker_list = [ ns.resolve(':seppo.'+n).getProxy() for n in names ]
        self.n_workers = len(self.worker_list)

class SeppoClientServer:
    def __init__(self):
        Pyro.core.initServer(banner=0)
        self.daemon = Pyro.core.Daemon()
        locator = Pyro.naming.NameServerLocator()
        NS = locator.getNS()
	self.daemon.useNameServer(NS)
seppo_cs = SeppoClientServer()

seppo_pph = None
def map_parallel( func, val_list ):
    global seppo_pph, seppo_cs
    if seppo_pph is None:
        seppo_pph = SeppoPyroProxyHolder()
        
    # divvy up val_list
    stop_idx = 0
    n_per_worker = int(math.ceil( len(val_list)/float(seppo_pph.n_workers)))
    
    callbacks = []
    i=-1
    while stop_idx < len(val_list):
        i+=1
        
        # divvy up val_list
        start_idx = i*n_per_worker     
        stop_idx = (i+1)*n_per_worker
        if stop_idx > len(val_list):
            stop_idx = len(val_list)

        # send commands to workers
        seppo_dcl = SeppoDoneCallbackListener()
        seppo_cs.daemon.connect(seppo_dcl)
        this_val_list = val_list[start_idx:stop_idx]
        worker_proxy = seppo_pph.worker_list[i]
        worker_proxy._setOneway(['register_done_callback'])
        worker_proxy.register_done_callback( func,
                                             this_val_list,
                                             seppo_dcl.getProxy() )
        # remember my callback functions
        callbacks.append( seppo_dcl )
        
    while 1:
        # handle commands
        seppo_cs.daemon.handleRequests()

        # check to see if we're done
        finished = True
        for seppo_dcl in callbacks:
            if not hasattr( seppo_dcl, 'seppo_results'):
                finished = False
        if finished:
            results = []
            for seppo_dcl in callbacks:
                results.extend( seppo_dcl.seppo_results )
                seppo_cs.daemon.disconnect(seppo_dcl)
            return results
    
def map_parallel_serial( func, val_list ):
    """for testing, same interface as map_parallel"""
    results = []
    for val in val_list:
        result = func(val)
        results.append( result )
    return results
