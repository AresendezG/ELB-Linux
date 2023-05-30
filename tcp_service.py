# echo-server.py
import socket

class TCPServer:

    HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
    PORT = 13085 

    def __init__(self, settings_file:str, limits_file:str, seq_file:str) -> None:
        pass

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.HOST, self.PORT))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    conn.sendall(data)
