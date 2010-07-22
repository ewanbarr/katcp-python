#!/usr/bin/env python

import os, re, sys

sys.path.insert(0, '.') # not sure why python adds '.' or not depending on
# obscure details how you run it
from katcp.server import DeviceServer
from twisted.internet.protocol import ProcessProtocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.error import ProcessDone
from twisted.internet.protocol import ClientCreator

class TestServer(DeviceServer):
    def setup_sensors(self):
        pass

    def _bind(self, *args):
        sock = DeviceServer._bind(self, *args)
        print "PORT: %d" % sock.getsockname()[1]
        return sock

class ServerSubprocess(ProcessProtocol):
    initiated = False

    def __init__(self, server_run, server_ended, failed):
        self.failed = failed
        self.server_run = server_run
        self.server_ended = server_ended

    def outReceived(self, data):
        if not self.initiated:
            m = re.match('PORT: (\d+)', data)
            if m is not None:
                self.port = int(m.group(1))
                self.server_run(self.port)
            else:
                self.failed(data)
            self.initiated = True
        else:
            print "RECEIVED: " + data

    def processExited(self, status):
        self.server_ended(status)

PORT = 0

def run_subprocess(connected, ClientClass):
    def failed_to_run(error):
        print error
        reactor.stop()

    def server_ended(status):
        assert status.type is ProcessDone
        d.callback(None)

    def server_running(port):
        cc = ClientCreator(reactor, ClientClass)
        d = cc.connectTCP('localhost', port)
        if connected is not None:
            d.addCallback(connected)

    dname = os.path.dirname
    protocol = ServerSubprocess(server_running, server_ended, failed_to_run)
    process = reactor.spawnProcess(protocol, sys.executable,
                                   [sys.executable, __file__], {},
                                   dname(dname(dname(__file__))),
                                   usePTY=True)
    d = Deferred()
    d.addErrback(failed_to_run)
    return d, protocol

if __name__ == '__main__':
    TestServer('localhost', PORT).run()