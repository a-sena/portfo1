import argparse
import socket
import time
import re
import threading
def parse_arguments():
    parser = argparse.ArgumentParser(description='Simpleperf')
#https://stackoverflow.com/questions/59773946/argparse-required-add-mutually-exclusive-group-parameters-list-as-optional
    server_or_client = parser.add_mutually_exclusive_group(required=True)
    server_or_client.add_argument('-s', '--server', action='store_true', help='Run server mode')
    server_or_client.add_argument('-c', '--client', action='store_true', help='Run client mode')
    parser.add_argument('-I', '--server_ip', type=str, default='127.0.0.1', help='IP address of server')
    parser.add_argument('-b', '--bind', type=str, default='127.0.0.1', help='Allows to select the ip address of the server’s interface')
    parser.add_argument('-p', '--server_port', type=int, default=8088, help='Allows to use select port number on which the server should listen')
    parser.add_argument('-t', '--total_time', type=int, default=25, help='The total duration in seconds for which data should be generated, default=25')
    parser.add_argument('-f', '--format', type=str, default='MB', choices=['B', 'KB', 'MB'], help='Allows  to choose the format of the summary of results')
    parser.add_argument('-i', '--interval', type=int, help='Print statistics per z seconds', default=None)
    parser.add_argument('-P', '--parallel', type=int, default=1, choices=range(1, 6), help='Number of parallel connections')
    parser.add_argument("-n", "--num", dest="no_of_bytes", type=str, help="Number of bytes", default=0)
   
    return parser.parse_args()


############### HANDLE_CLIENT FUNCTION STARTS HERE #######################################

def handle_client(client_socket, client_address, args):

    amount_of_bytes_received = 0
    start_time = time.time() #time before starting to receive data

    while True:
        data = client_socket.recv(1000) #receives data in the chunks of 1000 bytes
        if not data:
            break

        if b'BYE'in data:
            break

        amount_of_bytes_received += len(data)
  
    end_time = time.time() #data retrieval completed.
    total_duration = end_time - start_time 

    if args.format == "B":
        transfer_size = amount_of_bytes_received
    elif args.format == "KB":
        transfer_size = amount_of_bytes_received / 1000
    else:
        transfer_size = amount_of_bytes_received / 1000000

   
    rate_server = (transfer_size * 8) / total_duration
    #Outputs to be printed on the server page
    print("{:<25} {:<10} {:<15} {:<15}".format("ID", "Interval", "Received", "Rate"))
    print("{0}:{1:<15} 0.0 - {2}       {3:.0f} {4:<2}      {5:.2f} Mbps".format(client_address[0], client_address[1], int(total_duration), transfer_size, args.format, rate_server))

    client_socket.send(b"ACK: BYE") # message to client that indicates receiving data is finished
    client_socket.close()

############### SERVER FUNCTION STARTS HERE #######################################
def server(args):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((args.bind, args.server_port)) # binds it to the specified IP address and port
    server_socket.listen(1)#listens for incoming connection

    print("-" * 60)
    print("A simpleperf server is listening on port {}".format(args.server_port))
    print("-" * 60)

    while True:

        
        client_socket, client_address = server_socket.accept() #Accept client connections

        print("-" * 60)
        print("A simpleperf client with {}:{} is connected with {}:{}".format(client_address[0], client_address[1], args.bind, args.server_port))
        print("-" * 60)
        
        
        

        t = threading.Thread(target=handle_client, args=(client_socket, client_address, args))
        t.start()
# used sources: https://www.youtube.com/watch?v=3QiPPX-KeSc      


    
 ############### PARSE_SIZE FUNCTION STARTS HERE #######################################

def parse_size(val):
    unit_type = {'B': 1, 'KB': 1000, 'MB': 1000000}
    # copied from portfolio-guidelines.pdf, side 30
    match = re.match(r"([0-9]+)([a-z]+)", val, re.I) 
    number, unit = match.groups()
    number = int(number) # converts string type to integer type.
    unit = unit.upper() # accepts both mb and MB
    
    if unit in unit_type: # Checks if the unit value exists in the unit_type 
        return number * unit_type[unit]
    #if the unit value does not exist in unit_type, print error message
    else:
        print("!" * 60 )
        print("\n ERROR: Please write an invalid unit! {} is not invalid!! \n".format(unit))
        print("!" * 60 )

############### CLIENT FUNCTION STARTS HERE #######################################
def client(args):
    def single_connection():
        nonlocal successful_connections
#Creates socket in order to connect server 
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((args.server_ip, args.server_port))
        client_address = client_socket.getsockname()

        print("Simpleperf client connecting to server {}, port {}".format(args.bind, args.server_port))
        
        start_time = time.time() #Start time when client connects to server

        amount_of_bytes_sent = 0
        print("---------------------------------------------")
        print("ID                        Interval   Transfer        Bandwidth")
        
        # Num (-n) flag 
        #If the user specifies the size of data to be sent:
        if args.no_of_bytes:
            bytes_to_send = parse_size(args.no_of_bytes)
            while amount_of_bytes_sent < bytes_to_send:
                data = bytes(1000) #send data in the chunks of 1000 bytes
                client_socket.sendall(data)
                amount_of_bytes_sent += len(data)
        
        else:
            #interval flag
            if args.interval:
                interval_start_time = start_time
                interval_bytes_sent = 0
#for i in range(start, stop + step, step)
#https://stackoverflow.com/questions/60131021/understanding-interval-function-and-its-parameters-in-python-hetlands-book-exam

                for i in range(args.interval, args.total_time + args.interval, args.interval):
#The loop will run until data is sent for the interval time. 
                    while time.time() - interval_start_time <= args.interval: 
                        data = bytes(1000) # send data in the chunks of 1000 bytes
                        client_socket.sendall(data)
                        amount_of_bytes_sent += len(data)
                        interval_bytes_sent += len(data)
                    duration=args.interval
                    rate_client = (interval_bytes_sent * 8) / (duration * 1000000)
                    #print 0-5, 5-10, 10-15, 15-20, 20-25
                    #sending data at regular intervals takes place
                    print("{:<25} {:<10} {:<15} {:.2f} Mbps".format("{}:{}".format(client_address[0], client_address[1]), "{}-{}".format(i - args.interval, i), "{:.1f} MB".format(interval_bytes_sent / 1000000), rate_client))
                    interval_bytes_sent = 0
                    interval_start_time = time.time()
            else: #if args.no_of_bytes and args.interval is not entered 
                while time.time() - start_time < args.total_time:
                    data = bytes(1000)
                    client_socket.sendall(data)
                    amount_of_bytes_sent += len(data)
        #data sending is completed and the client sends the message "BYE" to the server 
        client_socket.sendall(b'BYE')

        while True:
            response = client_socket.recv(1000)
            if response == b"ACK: BYE": #The server sends the message "ACK: BYE" as a response
                break
#the client receives the message from the server and the socket is closed
        client_socket.close()

        
       
#client calculates statistics and prints the statistics on the client page.
        end_time = time.time()
        elapsed_time = end_time - start_time
        total_size = amount_of_bytes_sent / 1000000
        rate_client = (total_size * 8 ) / elapsed_time
        print("-" * 60)
    
        print("{:<25} {:<10} {:<15} {:.2f} Mbps".format("{}:{}".format(client_address[0], client_address[1]), "0-{:.1f}".format(int(elapsed_time)), "{:.1f} MB".format(total_size), rate_client))


       
# When multiple parallel connections are requested on the client side

    threads = []
  

    for _ in range(args.parallel):
        thread = threading.Thread(target=single_connection) 
        thread.start()
        threads.append(thread)
        time.sleep(1)
    successful_connections = 0
    for thread in threads:
        thread.join()
        successful_connections += 1
 


#I used those sources in order to write thread-section https://superfastpython.com/join-a-thread-in-python/ 
# and https://stackoverflow.com/questions/33470760/python-threads-object-append-to-list

#Either run the server or the client
if __name__ == '__main__':
    args = parse_arguments()
    if args.server:
        server(args)
    elif args.client:
        client(args)

