# echo-server.py
import socketserver
import socket
import sys
import queue
import threading
from threading import Thread
import time


class PropagatingThread(Thread):
    def run(self):
        self.exc = None
        try:
            if hasattr(self, '_Thread__target'):
                # Thread uses name mangling prior to Python 3.
                self.ret = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
            else:
                self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None):
        super(PropagatingThread, self).join(timeout)
        if self.exc:
            raise self.exc
        return self.ret


class tcp_launcher:

    def __init__(self, port, host) -> None:
        if (host != None):
            self.host = host
        else:
            self.host = "127.0.0.1"
        
        self.port = port
        pass

    def run_tcp(self, *args, **kwargs):
        host = kwargs['host']
        port = kwargs['port']
        print(f"port: {port}, host: {host}")
        inbound_cmd = "NONE_RECEIVED"
        cmd_history = []
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()
            try:                    
                conn, addr = s.accept()
                while(inbound_cmd != "END_CONN\n"):
                    with conn:
                        print(f"Command Received from: {addr}")
                        while True:
                            try:
                                data = conn.recv(1024)
                                if (data):
                                    inbound_cmd =  "".join(chr(x) for x in data)
                                    cmd_history.append(inbound_cmd) # append the list of incoming commands
                                if (not data or inbound_cmd.__contains__('\n')):
                                    break
                                #conn.sendall(data)
                            except OSError: # Ignore reading attempts at empty commands
                                print("reading att at empty cmds")
                                time.sleep(0.5)
                                None

                    print(f"Received cmd: {inbound_cmd}")
            
            except KeyboardInterrupt:
                print("Local user shutdown")
            #except:
                #print("Error during TCP Server")    
        return

    # Launch TCP server
    def launch_tcp(self):
        t = PropagatingThread(target=self.run_tcp, args=(5,), kwargs={'port':self.port, 'host':self.host})
        t.start()
        #t.run()
        while (True):
            try:
                print("Checking for TCP Alive!")
                if (t.is_alive()):
                    t.join(1)
                if (not t.is_alive()):
                    print("TCP Server Shutdown")
                    break
            except KeyboardInterrupt:
                print("User Shutdown via Keyboard Interrupt")
                return
        print("TCP Service terminated")
        return

