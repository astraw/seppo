import socket, os

def hello_world( value ):
    value2 = value*value
    fqdn = socket.getfqdn()
    pid = os.getpid()
    host_str = "%s, process %d"%(fqdn,pid)
    result = 'hello world from %s (input=%f, value*value=%f)'%(host_str,value,value2)
    return result
