"""
The client.py file consists of the client side implementation of this application. This application supports TCP and also Stop and wait protocol over UDP.
The following information gives a simple breakdown structure of the client side application:
1. Import required libraries
2. Define functions to handle the reception and sending of files over the protocol invoked.
3. The main function:
   (a) accept the command input if it is in the expected format
   (b) Invoke relavant blocks of code based on the protocol input
4. TCP protocol Handling:
   (a) PUT method sends the file to server
   (b) GET method can download file from server or cache based on the availability
   (c) quit command will exit the program
5. UDP protocol Handling
   (a) PUT method sends the file to server in chunks on 1000 bytes
   (b) GET method can download file from server or cache based on the availability in chunks of 1000 bytes
   (c) quit command will exit the program
"""

import sys
import os
sys.path.append("..")
import snw_transport as udp_transport     #snw_transport file is the library consisting the snw related functions
import tcp_transport                      #tcp_transport file is the library consisting the tcp related functions

CLIENT_DIR = "client_files"   #The folder to which client stores the donwloaded files/Uploads the files from this folder to the origin

# Create the 'client_files' directory if it doesn't exist
if not os.path.exists(CLIENT_DIR):
    os.makedirs(CLIENT_DIR)
#This function will allow the client to send/upload files to the server using the TCP protocol
def put_file(client_socket, command):    
    filename = command.split(' ')[1]
    filepath = os.path.join(CLIENT_DIR, filename)
    if os.path.exists(filepath):
        tcp_transport.send_file(client_socket, filepath)   #to send file, if it exits
        print(tcp_transport.receive_data(client_socket)) #print the response
    else:
        print(f"File '{filename}' not found!")
#This function will allow the client to receive/upload files from the server using the TCP protocol
def get_file(client_socket, command):     
    filename = command.split(' ')[1]
    filepath = os.path.join(CLIENT_DIR, filename)
    response = tcp_transport.receive_data(client_socket)  #to get the response
    if response == "FileNotFound":
        print("File not found on cache or server!")   #print relavant message if file not found
        return
    else:
        print(response)                
        tcp_transport.receive_file(client_socket, filepath)   #To receive and save the file
        #print(f"Received file {filename}")


def main():
    if len(sys.argv)!=6:
        print("Usage: python client.py <SERVER_HOST> <SERVER_PORT> <CACHE_HOST> <CACHE_PORT> <PROTOCOL>")
        sys.exit(1)
#to extract the command line arguments
    SERVER_HOST = sys.argv[1]    #To extract the server host
    SERVER_PORT = int(sys.argv[2])    #To extract server port
    CACHE_HOST = sys.argv[3]      #to extract cache host
    CACHE_PORT = int(sys.argv[4])   #To extract cache port
    PROTOCOL=sys.argv[5]    

    if(PROTOCOL=="tcp"):
       while True:
            command = input("Enter command: ")   #To get the user command input
            

            if command.startswith('put'):           #If method is 'PUT'
                print("Awaiting server response.")
                client_socket = tcp_transport.create_tcp_socket()   #create a tcp socket
                tcp_transport.connect_to_host(client_socket, SERVER_HOST, SERVER_PORT)   #connect to server
                tcp_transport.send_data(client_socket, command)   #send command to server
                put_file(client_socket, command)    #upload the file
                
                tcp_transport.close_connection(client_socket)   #close the connection

            elif command.startswith('get'):        #If method is 'GET'
                print("Awaiting server response.")
                client_socket = tcp_transport.create_tcp_socket()   #create a tcp socket
                tcp_transport.connect_to_host(client_socket, CACHE_HOST, CACHE_PORT)  #connect to cache
                tcp_transport.send_data(client_socket, command)   #send command to cache 
                get_file(client_socket, command)   #download the file

                tcp_transport.close_connection(client_socket)    #close connenction

            elif command == 'quit':        #Exit program on encountering a quit command
                print("Exiting Program....")    #print relavant message to the user
                break

            else:
                print("Invalid command! Please use 'put', 'get', or 'quit'.")   #If an invalid command is enter print error message

    else: #PROTOCOL=SNW               # If the protocol invoked is stop and wait
        client_socket = udp_transport.create_udp_socket()     #create a UDP Socket

        while True:
            command = input("Enter command: ")

            if command.startswith('put'):              #Handle PUT command 
                filename = command.split(' ')[1]
                filepath = os.path.join(CLIENT_DIR, filename)  # Use filepath inside 'client_files' directory
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:    #open and read the file to be sent
                        file_data = f.read()

                    udp_transport.send_data(client_socket, f"PUT:{filename}", (SERVER_HOST, SERVER_PORT))
                    udp_transport.send_data(client_socket, f"LEN:{len(file_data)}", (SERVER_HOST, SERVER_PORT))
                    udp_transport.send_file(client_socket, file_data, (SERVER_HOST, SERVER_PORT))

                    fin_message, _ = udp_transport.receive_data(client_socket)
                    if fin_message == "FIN":
                        None# print("Received FIN from server.")   Receive FIN message from server upon complete transmission of data
                    response, _ = udp_transport.receive_data(client_socket)
                    if response.startswith("Message:"):
                        print("Server response: ",response.split(":", 1)[1])

            elif command.startswith('get'):    #Handle GET command
                filename = command.split(' ')[1]
                udp_transport.send_data(client_socket, f"GET:{filename}", (CACHE_HOST, CACHE_PORT))

                length_info, _ = udp_transport.receive_data(client_socket)
                if length_info.startswith("LEN:"):
                    _, length = length_info.split(":")
                    file_data = udp_transport.receive_file(client_socket, int(length))
                    filepath = os.path.join(CLIENT_DIR, filename)  # Use filepath inside 'client_files' directory
                    with open(filepath, 'wb') as f:
                        f.write(file_data)
                    
                    udp_transport.send_fin(client_socket, (CACHE_HOST, CACHE_PORT))
                    message, _ = udp_transport.receive_data(client_socket)
                    if message.startswith("Message:"):
                        print("Server response: ",message.split(":", 1)[1])

                else:
                    print("File not found on server!")

            elif command == 'quit':     #Handle quit command
                client_socket.close()     #close UDP socket
                print("Exiting Program....")
                break

if __name__ == "__main__":
    main()
