# seppo.py
"""simple embarrassingly parallel python"""

## Copyright (c) 2005, Andrew Straw. All rights reserved.

## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:

##     * Redistributions of source code must retain the above copyright
##       notice, this list of conditions and the following disclaimer.

##     * Redistributions in binary form must reproduce the above
##       copyright notice, this list of conditions and the following
##       disclaimer in the documentation and/or other materials provided
##       with the distribution.

##     * Neither the name of the Andrew Straw nor the names of its
##       contributors may be used to endorse or promote products derived
##       from this software without specific prior written permission.

## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys, math, time, threading

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

class SeppoError(Exception):
    pass

class SeppoNoWorkersError(SeppoError):
    pass

def worker_thread_func( func, val_list, done_callback_proxy, debug=0):
    if debug: print 'working...'
    results = [func(v) for v in val_list]
    if debug: print 'done with work, worker thread finishing'
    done_callback_proxy.done( results )

class SeppoWorker(Pyro.core.ObjBase):
    def register_done_callback( self, func, val_list, done_callback_proxy, debug=0 ):
        if debug: print 'received work request, staring worker thread...'
        worker_thread = threading.Thread(target=worker_thread_func,
                                         args=(func,
                                               val_list,
                                               done_callback_proxy,
                                               debug),
                                         )
        worker_thread.setDaemon(True)
        worker_thread.start()
        if debug: print 'worker thread started'
        
def start_seppo_enslaved_server(hostname=None,port=9876,debug=0):
    if hostname is None:
        hostname = ''
    
    Pyro.core.initServer(banner=0)
    # locate the NS
    daemon = Pyro.core.Daemon()
    locator = Pyro.naming.NameServerLocator()
    if debug: print 'seppo enslaved server getting Pyro Name Server...'
    ns = locator.getNS()
    if debug: print 'seppo enslaved server found Pyro Name Server'
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
        daemon.requestLoop()
    finally:
        daemon.disconnect(obj)
        daemon.shutdown()

class SeppoDoneCallbackListener(Pyro.core.ObjBase):
    def done(self,results):
        self.seppo_results = results

class SeppoPyroProxyHolder:
    def __init__(self,debug=0):
        Pyro.core.initClient(banner=0)
        self.debug = debug
        self.refind_workers()

    def refind_workers(self):
	# locate the NS
	locator = Pyro.naming.NameServerLocator()
        if self.debug: print 'client getting Pyro Name Server...'
	ns = locator.getNS()
        if self.debug: print 'got Pyro Name Server'

        #self.worker_list = ns.list(Pyro.config.PYRO_NS_DEFAULTGROUP)
        vts = ns.list(Pyro.config.PYRO_NS_DEFAULTGROUP)
        names = []
        for v,t in vts:
            if t==1: # leaf
                names.append( v )
        self.worker_list = [ ns.resolve(':seppo.'+n).getProxy() for n in names ]
        self.n_workers = len(self.worker_list)
        if self.debug: print '%d worker processes available'%(self.n_workers,)

class SeppoClientServer:
    def __init__(self):
        Pyro.core.initServer(banner=0)
        self.daemon = Pyro.core.Daemon()
        locator = Pyro.naming.NameServerLocator()
        NS = locator.getNS()
	self.daemon.useNameServer(NS)
        
seppo_cs = None
seppo_pph = None

def map_parallel( func, val_list ,debug=0 ):
    global seppo_pph, seppo_cs

    if seppo_cs is None:
        seppo_cs = SeppoClientServer()
    if seppo_pph is None:
        seppo_pph = SeppoPyroProxyHolder()
    seppo_pph.debug=debug

    if seppo_pph.n_workers == 0:
        raise SeppoNoWorkersError()
        
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
        #worker_proxy._setOneway(['register_done_callback'])
        if debug: print 'registering done callback with server(s)...'
        worker_proxy.register_done_callback( func,
                                             this_val_list,
                                             seppo_dcl.getProxy(),
                                             debug=debug)
        if debug: print 'returned from register commnad (oneway, so no guarantee)'
        # remember my callback functions
        callbacks.append( seppo_dcl )
        
    while 1:
        # handle commands
        if debug: print 'awaiting done callback(s)...'
        
        # If done callbacks never come, check to make sure func
        # signature matches (especially number of arguments). XXX
        # TODO: should figure how to raise exception in this case.
        
        seppo_cs.daemon.handleRequests()
        if debug: print 'checking...'            

        # check to see if we're done
        finished = True
        for seppo_dcl in callbacks:
            if not hasattr( seppo_dcl, 'seppo_results'):
                finished = False
        if finished:
            if debug: print 'done'
            results = []
            for seppo_dcl in callbacks:
                results.extend( seppo_dcl.seppo_results )
                seppo_cs.daemon.disconnect(seppo_dcl)
            return results
        if debug: print 'not done'
    
def map_parallel_serial( func, val_list ):
    """for testing, same interface as map_parallel"""
    results = []
    for val in val_list:
        result = func(val)
        results.append( result )
    return results
