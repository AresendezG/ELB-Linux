# echo-server.py
import socketserver
import socket
import sys
import queue
import threading
from threading import Thread
from prog_mgr_tcp import ProgramControl
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
        # Launch Test Controller 
        self.test_ctrl = ProgramControl()
        pass

    def run_tcp(self, *args, **kwargs):
        host = kwargs['host']
        port = kwargs['port']
        print(f"port: {port}, host: {host}")
        inbound_cmd = "NONE_RECEIVED"
        cmd_history = []
        ret_history = []
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()
            try:    
                while(inbound_cmd != "END_CONN\n"):
                    conn, addr = s.accept()     
                    with conn:
                        print(f"Command Received from: {addr}")
                        while (not inbound_cmd.__contains__('FIN_CMD\n') or not inbound_cmd.__contains__('END_CONN\n')):
                            try:
                                data = conn.recv(1024)
                                if (data):
                                    inbound_cmd =  "".join(chr(x) for x in data)
                                    cmd_history.append(inbound_cmd) # append the list of incoming commands
                                    # ret_data_str = f"Echo Back Message: {inbound_cmd}"
                                    ret_data_str = self.process_test_cmd(inbound_cmd)
                                    ret_history.append(ret_data_str)
                                    conn.sendall(bytes(ret_data_str, 'UTF-8'))
                                if (not data or inbound_cmd.__contains__('FIN_CMD\n') or inbound_cmd.__contains__('END_CONN\n')):
                                    self.process_test_cmd("END_TEST")
                                    break
                            except OSError: # Ignore reading attempts at empty commands
                                print("Invalid Connection Status")
                                time.sleep(0.5)
                                inbound_cmd = "FIN_CMD\n"
                                break

                    print(f"Received Termination Cmd: {inbound_cmd}")
                print("Terminating TCP/IP Connection")
                raise KeyboardInterrupt
            except KeyboardInterrupt:
                print("Local user shutdown")
            #except:
                #print("Error during TCP Server")    
        return

    
    def process_test_cmd(self, inbound_cmd:str) -> str:
        # Cmd contains Start Test:
        if (inbound_cmd.__contains__('START_TEST') and not self.test_ctrl.test_started):
            print("Start Test")
            if (self.test_ctrl.start_test(inbound_cmd)):
                return 'TEST_START_CORRECT'
            else:
                return 'TEST_START_ERROR'
        elif (inbound_cmd.__contains__('RUN_TEST') and self.test_ctrl.test_started):
            print("Run Test")
            res_str = self.test_ctrl.run_test(inbound_cmd)
            return res_str
        elif (inbound_cmd.__contains__('END_TEST')):
            return self.test_ctrl.end_test()
        else:
            return "INVALID_CMD"


    
    # Launch TCP server
    def launch_tcp(self):
        t = PropagatingThread(target=self.run_tcp, args=(5,), kwargs={'port':self.port, 'host':self.host})
        t.start()
        #t.run()
        while (True):
            try:
                #print("Checking for TCP Alive!")
                if (t.is_alive()):
                    t.join(1)
                if (not t.is_alive()):
                    print("TCP Server Shutdown")
                    break
            except KeyboardInterrupt:
                print("User Shutdown via Keyboard Interrupt")
                try:
                    self.test_ctrl.end_test()
                    del self.test_ctrl
                except:
                    return
                return
            except AttributeError:
                None
        print("TCP Service terminated")
        return

