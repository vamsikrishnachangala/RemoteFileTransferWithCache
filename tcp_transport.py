"""
The tcp_transport.py has utilty fucntions that can support the TCP type of communication between server, cache and client.
The functions involve mechanisms for creation of sockets, binding sockets, listening for request, establishing connecitons,
closing the TCP sockets.
The functions in tcp_transport.py also handle the reception and sending of files.
"""

import socket

EOF_MARKER = b'EOF_MARKER'  #To denote the end of a file transmission

def create_tcp_socket():     #to create a TCP socket
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def bind_and_listen(s, host, port):  #to bind the socket to a host port and listen for connections
    s.bind((host, port)) 
    s.listen(5)
    return s

def connect_to_host(s, host, port): #to connect to a remote host
    s.connect((host, port))  #establish a connection
    return s

def send_data(s, data):  #function to send data
    s.sendall(data.encode())

def receive_data(s, buffer_size=1024):  #function to receive data
    return s.recv(buffer_size).decode()

def send_file(s, file_path):   #to send file over a socket
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(1024)
            if not chunk:
                break   #end of file reached
            s.sendall(chunk)
        s.sendall(EOF_MARKER)

def receive_file(s, file_path):  #to receive a file over socket
    with open(file_path, 'wb') as f:
        buffer = bytearray()
        while True:   #receive data in chunks
            chunk = s.recv(1024)
            if not chunk:
                print("Connection lost while receiving the file!")
                return
            buffer.extend(chunk)
            if EOF_MARKER in buffer:   #check for EOF_MARKER in the buffer
                buffer = buffer[:-len(EOF_MARKER)]
                f.write(buffer)
                break
            else:
                f.write(chunk)
                buffer = bytearray()

def close_connection(s):  #close the socket
    s.close()
