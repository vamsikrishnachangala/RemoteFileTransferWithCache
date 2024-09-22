"""
The snw_transport.py file contains the utility functions required to process a file transfer using the stop and wait mechanism over UDP.
The file consists functions to create sockets, bind sockets, send and receive data, and also perform data transmission in the form of
1000 byte chunks in UDP.
These mechanisms invlove sending and receiving of ACKS in order to ensure reception of chunks
This file also has timeout mechanisms to detect potential data loss
"""
import socket

def create_udp_socket(): #create and return a new udp socket
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def bind_socket(s, host, port):  #bind the socket to the host and port
    s.bind((host, port))

def send_data(s, data, address):  #Send the data to address specified
    s.sendto(data.encode(), address)

def receive_data(s, buffer_size=1024): #receive data form socket and return data to sender's address
    data, addr = s.recvfrom(buffer_size)
    return data.decode(), addr

def send_fin(s, address):  #send FIN message as an indication of the end of transmission
    send_data(s, "FIN", address)

def send_file(s, file_data, address): #send file data in chunks of 1000 bytes to the address specified
    length = len(file_data)
    chunks = [file_data[i:i+1000] for i in range(0, length, 1000)]
    for chunk in chunks:
        while True:
            s.sendto(chunk, address)  #send a chunk of data
            s.settimeout(1)   #set a timeout to wait for an ACK
            try:
                ack, _ = receive_data(s)
                if ack == "ACK":
                    break  #if ACK is received break the loop
            except socket.timeout:  #if timeout occurs print error message
                print("Did not receive ACK. Terminating.")
                exit()

def receive_file(s, expected_length):  #receive a file of expected length in chunks of 1000 bytes
    received_data = b""
    while len(received_data) < expected_length:
        s.settimeout(1)   #set a time out to wait to incoming data
        try:
            data, addr = s.recvfrom(1000)  #receive data
            received_data += data   #add received data to buffer
            send_data(s, "ACK", addr)   #send acknowledgement ot sender
        except socket.timeout:   #if timeout occurs, print error message
            print("Data transmission terminated prematurely.")
            exit()
    return received_data  #return the complete received data
