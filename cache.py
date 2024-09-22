""""
The cache.py acts as an intermediatory service between client and server applications.
The cache listens to the client requests to GET a file. The cache checks its availability in the cache files and sends it to the client.
If the requested file is not available, it requests the file from server, saves it in cache files and sends the file to client.
This functionality is implemented using 2 protocols. Either of TCP or snw can be invoked.

Cache operation can happen using tcp or snw protocols:
In TCP mode: The cache server establishes a TCP connection with client and server to process the file requests.

In SNW mode: The cache server communicates to server and client using UDP and implements stop and wait protocol for data transfer.

"""
import sys   #Import necessary libraries
sys.path.append("..")
import tcp_transport    #Import TCP related funcitons
import snw_transport as udp_transport   #Import SNW over UDP related funcitons
import os
import socket

CACHE_DIR = "cache_files"   #cache stores and retrives files to this directory

# Create the 'cache_files' directory if it doesn't exist
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def handle_client_request(client_socket, SERVER_HOST, SERVER_PORT):  #funciton to handle client requests
    try:
        command = tcp_transport.receive_data(client_socket)   #receive command from client

        if command.startswith('get'):  #If get method is invoked, check the availability in cache, if required connect to server to get the file required
            filename = command.split(' ')[1]
            filepath = os.path.join(CACHE_DIR, filename)  # Use filepath inside 'cache_files' directory

            if os.path.exists(filepath):  #to check if the file is present in cache
                tcp_transport.send_data(client_socket, "File delivered from Cache")
                tcp_transport.send_file(client_socket, filepath)

            else:  #if the file is not found in cache, fetch from server
                print("File not found in cache, trying to get from server!")
                server_socket_tcp = tcp_transport.create_tcp_socket()
                tcp_transport.connect_to_host(server_socket_tcp, SERVER_HOST, SERVER_PORT)
                tcp_transport.send_data(server_socket_tcp, command)
                response = tcp_transport.receive_data(server_socket_tcp)
                
                if response == "FileNotFound":  #If file found over server, send to client and cache it
                    tcp_transport.send_data(client_socket, "FileNotFound")
                else:
                    tcp_transport.send_data(client_socket, "File delivered from Server")
                    tcp_transport.receive_file(server_socket_tcp, filepath)
                    tcp_transport.send_file(client_socket, filepath)

                server_socket_tcp.close()  #close the client connection after handling request

    except Exception as e:
        print(f"Error while handling client request: {e}")
    finally:
        tcp_transport.close_connection(client_socket)

def main():  #main function to start the cache server and listen for client requests
    if len(sys.argv) != 5:
        print("Usage: python cache.py <CACHE_PORT> <SERVER_HOST> <SERVER_PORT> <PROTOCOL>")
        sys.exit(1)

    CACHE_PORT = int(sys.argv[1])
    CACHE_HOST="localhost"
    SERVER_HOST = sys.argv[2]
    SERVER_PORT = int(sys.argv[3])
    PROTOCOL = sys.argv[4]
 #Handle tcp protocol if the command invoked is TCP
    if(PROTOCOL == "tcp"):
        cache_socket_tcp = tcp_transport.create_tcp_socket()
        tcp_transport.bind_and_listen(cache_socket_tcp, CACHE_HOST, CACHE_PORT)
        print(f"Cache listening on {CACHE_HOST}:{CACHE_PORT}")

        try:
            while True:   #Accept client connection
                client_socket, _ = cache_socket_tcp.accept()
                print("Client connected to cache")
                handle_client_request(client_socket, SERVER_HOST, SERVER_PORT)
        except KeyboardInterrupt:
            print("Cache server shutting down...")  #Shut down the cache upon encountering a keyboard interupt
        finally:
            tcp_transport.close_connection(cache_socket_tcp)  #close cache server socket
            print("Cache server shut down") 

    else: # PROTOCOL=SNW  #Handle Stop and wait over UDP if the command encountered has snw argument
        cache_socket_udp = udp_transport.create_udp_socket()
        udp_transport.bind_socket(cache_socket_udp, CACHE_HOST, CACHE_PORT)
        print(f"Cache listening on {CACHE_HOST}:{CACHE_PORT}")

        printed_timeout = False

        while True:
            try:  #rececive command from client
                command, client_address = udp_transport.receive_data(cache_socket_udp)
                printed_timeout = False

                if command.startswith('GET:'):  #Handle GET method: check cache first and fetch from server if needed
                    filename = command.split(':')[1]
                    filepath = os.path.join(CACHE_DIR, filename)  # Use filepath inside 'cache_files' directory

                    if os.path.exists(filepath):  #Check if the file is present in cache
                        with open(filepath, 'rb') as f:
                            file_data = f.read()
                        udp_transport.send_data(cache_socket_udp, f"LEN:{len(file_data)}", client_address)
                        udp_transport.send_file(cache_socket_udp, file_data, client_address)
                        fin_message, _ = udp_transport.receive_data(cache_socket_udp)
                        if fin_message == "FIN":
                            print("File sent to client completed successfully.")
                        udp_transport.send_data(cache_socket_udp, "Message:File delivered from cache", client_address)
                    else:   #if the requested file is not in cache, fetch from server and cache it
                        udp_transport.send_data(cache_socket_udp, command, (SERVER_HOST, SERVER_PORT))
                        length_info, _ = udp_transport.receive_data(cache_socket_udp)
                        if length_info.startswith("LEN:"):
                            _, length = length_info.split(":")
                            file_data = udp_transport.receive_file(cache_socket_udp, int(length))
                            with open(filepath, 'wb') as f:
                                f.write(file_data)
                            udp_transport.send_fin(cache_socket_udp, (SERVER_HOST, SERVER_PORT))
                            udp_transport.send_data(cache_socket_udp, f"LEN:{len(file_data)}", client_address)
                            udp_transport.send_file(cache_socket_udp, file_data, client_address)
                            fin_message, _ = udp_transport.receive_data(cache_socket_udp)
                            if fin_message == "FIN":
                                print("File sent to client completed successfully.")
                            udp_transport.send_data(cache_socket_udp, "Message:File delivered from server", client_address)
                        else:
                            udp_transport.send_data(cache_socket_udp, "FileNotFound", client_address)

            except socket.timeout:
                if not printed_timeout:   #print timeout message 
                    print("Cache socket timed out, waiting for another packet.")
                    printed_timeout = True
                continue
#Execute main function when the script runs
if __name__ == "__main__":
    main()