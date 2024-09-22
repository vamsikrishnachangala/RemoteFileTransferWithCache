"""
The server.py file consists of the server side implementation of this application. This application supports TCP and also Stop and wait protocol over UDP.
The following information gives a simple breakdown structure of the server side application:
1. Import required libraries
2. Define functions to handle the reception and sending of files over the protocol invoked.
3. The main function:
   (a) accept the command input if it is in the expected format
   (b) Invoke relavant blocks of code based on the protocol input
4. TCP protocol Handling:
   (a) put functionality in handle_client method receives the file from client
   (b) get  functionality in handle_client method will sned file to cache
   (c) quit command will exit the program
5. UDP protocol Handling
   (a) PUT method recieves the file from client in chunks on 1000 bytes
   (b) GET method will send file to cache in chunks of 1000 bytes
"""



import sys
sys.path.append("..")
import tcp_transport                    #tcp_transport file is the library consisting the tcp related functions
import snw_transport as udp_transport  #snw_transport file is the library consisting the snw related functions
import os
import socket

SERVER_FILES_DIR = "server_files" #The folder to which server stores the downloaded files/Uploads the files from this folder to the client or cache.

# Ensure the server_files directory exists
if not os.path.exists(SERVER_FILES_DIR):
    os.makedirs(SERVER_FILES_DIR)
# This function handles the tcp client or cache request either put or get.
def handle_client(client_socket):
    try:
        command = tcp_transport.receive_data(client_socket)
        #If the encountered command is put, receive and save file from the client
        if command.startswith('put'):
            filename = command.split(' ')[1]
            filepath = os.path.join(SERVER_FILES_DIR, filename)
            tcp_transport.receive_file(client_socket, filepath)
            print(f"Received and saved {filename}")
            tcp_transport.send_data(client_socket, "Server response: File successfully uploaded")

        #If the encountered command is get, then send file or respond with relavant messages based on the availibility of file at the server
        elif command.startswith('get'):
            filename = command.split(' ')[1]
            filepath = os.path.join(SERVER_FILES_DIR, filename)

            if os.path.exists(filepath):
                tcp_transport.send_data(client_socket, "File delivered from origin")
                tcp_transport.send_file(client_socket, filepath)
            
            else:
                tcp_transport.send_data(client_socket, "FileNotFound")

    except Exception as e:
        print(f"Error while handling client: {e}")
    finally:  #close the connection after handlding the request
        tcp_transport.close_connection(client_socket)
#The main function will start the server and invoke the functions based on clients arguments in command
def main():
    if len(sys.argv) != 3:
        print("Usage: python tcp_snw_server.py <PORT> <PROTOCOL>")
        sys.exit(1)

    HOST = 'localhost'
    PORT = int(sys.argv[1])
    PROTOCOL = sys.argv[2]
#If the protocol invoked is TCP, handle it using necessary functions
    if PROTOCOL == "tcp":
        server_socket_tcp = tcp_transport.create_tcp_socket()
        tcp_transport.bind_and_listen(server_socket_tcp, HOST, PORT)
        print(f"Server listening on {HOST}:{PORT}")

        try:
            while True:  #Accept the client connection and handle the requests
                client_socket, _ = server_socket_tcp.accept()
                print("Client connected")
                handle_client(client_socket)
        except KeyboardInterrupt:
            print("Server shutting down...")  #shutdown the server using the keypad interupts
        finally:
            tcp_transport.close_connection(server_socket_tcp)  #close the server sockets
            print("Server shut down")

    else: #PROTOCOL=SNW    #Handle the UDP protocol along with stop and wait mechanisms
        server_socket_udp = udp_transport.create_udp_socket()
        udp_transport.bind_socket(server_socket_udp, HOST, PORT)
        print(f"Server listening on {HOST}:{PORT}")

        printed_timeout = False

        while True:
            try:   #receive command from client
                command, client_address = udp_transport.receive_data(server_socket_udp)
                printed_timeout = False

                if command.startswith('PUT:'):   #If the method is PUT, Receive and save files from client
                    filename = command.split(':')[1]
                    filepath = os.path.join(SERVER_FILES_DIR, filename)

                    length_info, _ = udp_transport.receive_data(server_socket_udp)
                    if length_info.startswith("LEN:"):
                        _, length = length_info.split(":")
                        file_data = udp_transport.receive_file(server_socket_udp, int(length))
                        with open(filepath, 'wb') as f:
                            f.write(file_data)
                        print(f"Received and saved {filepath}")
                        udp_transport.send_fin(server_socket_udp, client_address)
                        udp_transport.send_data(server_socket_udp, "Message:File Successfully uploaded", client_address)

                elif command.startswith('GET:'):  #If the method is GET, send the file or respond with error message if file not found
                    filename = command.split(':')[1]
                    filepath = os.path.join(SERVER_FILES_DIR, filename)

                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            file_data = f.read()
                        udp_transport.send_data(server_socket_udp, f"LEN:{len(file_data)}", client_address)
                        udp_transport.send_file(server_socket_udp, file_data, client_address)
                        fin_message, _ = udp_transport.receive_data(server_socket_udp)
                        if fin_message == "FIN":
                            print("File sent to cache completed successfully.")

                    else:
                        udp_transport.send_data(server_socket_udp, "FileNotFound", client_address)

            except socket.timeout:    #Print time out message once until next packet arrives
                if not printed_timeout:
                    print("Socket timed out, waiting for another packet.")
                    printed_timeout = True
                continue
#Execute main function when server.py runs
if __name__ == "__main__":
    main()