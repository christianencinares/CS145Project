import socket
import time
import os
import argparse
import requests
import math
#DEFAULT VALUES
FILEPATH = "ecd04286.txt"
ADDRESS = "10.0.7.141"
RECEIVERPORT = 9000
SENDERPORT = 6696
UID =  "ecd04286"
#Gets the arguments from the command line
def GetArgs():
    parser = argparse.ArgumentParser()  #Initialize the parser. Can handle switched and missing arguments.     
    #Define the arguments filepath,address,receiverport,senderport,and uniqueid.                   
    parser.add_argument("-f", "--filepath", help="File path of the payload to send", type=str, default= FILEPATH)           
    parser.add_argument("-a", "--address", help="IP address of receiver", type=str, default= ADDRESS)     
    parser.add_argument("-s", "--receiverport", help="Port receiver will listen to", type=int, default= RECEIVERPORT)  
    parser.add_argument("-c", "--senderport", help="Port sender will listen to", type=int, default= SENDERPORT)     
    parser.add_argument("-i", "--uniqueid", help="Unique Student ID", type=str, default = UID)         
    args = parser.parse_args() #Parse the entered command line arguments according to the arguments defined in parser 
    return args

#Send the intent message to the receiver 
def SendIntentMessage(socket,args):
    while True: 
        message = ("ID{}".format(args.uniqueid)).encode()   #Encode the intent message IDWWWWWWWW 
        socket.sendto(message, (args.address, args.receiverport))    #Send the intent message using receiver's IP and port
        TID, server = socket.recvfrom(8)          #Receive the response from receiver
        TID = TID.decode()                        #Decode the response
        if TID == 'Existing':
            time.sleep(0.2)
            print("ERROR: Transaction ID currently in use. Reattempting...")
            continue
        print("TID:",TID)                          #Print the transcation ID from the receiver
        return TID                                

#Initialize the UDP socket
def InitSocket(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Create a UDP socket
    sock.bind(('',args.senderport))                         #Bind the socket to the sender port
    return sock                                             #Return the socket

#Retrieve payload from specified file
def GetFileContents(args):
    if os.path.isfile(args.filepath):              #Check if the file exists
        f = open(args.filepath, 'rt')              #Open the file in read-text mode
        file_size = os.path.getsize(args.filepath) #Get the size of the file
        file_contents = f.read(file_size)          #Read the file contents using the size of the file
        f.close()                                  #Close the file
        return file_contents                      #Return the payload
    else:
        print("ERROR: File does not exist")   #Print an error msg if file does not exist
        return -1

def FetchNewPayload(args):
    url = "http://3.0.248.41:5000/get_data?student_id={}".format(args.uniqueid)
    response = requests.get(url)
    open(args.filepath, 'wb').write(response.content) #Automatically creates file if DNE

def SendPayload(args,socket,TID,payload):
    sequence_number = 0
    Z = 0
    payload_length = len(payload)
    transmitted_payload = 0
    payload_start = 0
    payload_end = 1
    payload_size = 1
    adaptive_size_mode = 0
    Ave_RTT = 10
    RTT = 0
    incrementer = 1
    start_elapsed_time = time.time()
    while (transmitted_payload != payload_length) and (time.time() - start_elapsed_time < 125):
        data_packet = ("ID{}SN{:07d}TXN{:07d}LAST{}{}".format(args.uniqueid,int(sequence_number),int(TID),Z,payload[payload_start:payload_end])).encode()
        print("------------------------------------------------------")
        print("Attempting to send: ",data_packet)
        print("SIZE: ",payload_size,"SN:",sequence_number,"Adapative Size Mode:",adaptive_size_mode)
        socket.settimeout(Ave_RTT+0.5)
        try:
            start = time.time()
            socket.sendto(data_packet, (args.address, args.receiverport))
            receiver_ack, server = socket.recvfrom(100)
            end = time.time()
            RTT = end - start

            transmitted_payload = transmitted_payload + payload_size
            elapsed_time = time.time() - start_elapsed_time
            print("[SUCCESS] ACK:",receiver_ack,"RTT:",RTT,"Transmitted:",transmitted_payload,"/",payload_length,"Elapsed Time:",elapsed_time)
            print("------------------------------------------------------")
            if payload_size >  payload_length - payload_end: #Last packet, just send the rest of the payload.
                payload_size = payload_length - payload_end
                payload_start = payload_end
                payload_end = payload_length
                Z = 1
            else:
                if adaptive_size_mode == 0:   
                    print(sequence_number)
                    if sequence_number == 0:    #Initial guess
                        numofpackets = math.ceil(120/RTT) 
                        payload_size = int(payload_length//numofpackets)
                    else:
                        adaptive_size_mode = 1 #Try increasing payload size
                elif adaptive_size_mode == 1: #Increment
                    incrementer = incrementer * 3
                    payload_size = payload_size + incrementer 
                elif adaptive_size_mode == 2:
                    payload_size = payload_size + 1                   
                #else Optimal payload size attained, no payload size change
            
                payload_start = payload_end
                payload_end = payload_end + payload_size
            sequence_number = sequence_number+1
        except:
            elapsed_time = time.time() - start_elapsed_time
            end = time.time()
            
            payload_start = payload_end - payload_size
            if adaptive_size_mode == 0: #bad initial guess
                payload_size = payload_size * 2/3
                adaptive_size_mode = 1
            elif adaptive_size_mode == 1: #Switch to decrement mode
                payload_size = payload_size - incrementer 
                adaptive_size_mode = 2   #optimal payload size attained
            elif adaptive_size_mode == 2: #Switch to decrement mode
                payload_size = payload_size - 1 
                adaptive_size_mode = 3   #optimal payload size attained    
            payload_end = payload_start + payload_size
            print("[TIMEOUT] RTT:",end-start,"Transmitted:",transmitted_payload,"/",payload_length,"Elapsed Time:",elapsed_time)
        
        if sequence_number == 1:
            Ave_RTT = RTT + 0.5
        else:
            Ave_RTT = (Ave_RTT*sequence_number + RTT)/(sequence_number+1)
        print("Average RTT is: ",Ave_RTT)
        

def main():
    cmd_args = GetArgs()
    print("Fetching payload file...") 
    #FetchNewPayload(cmd_args)

    print("Reading payload file...")
    payload = GetFileContents(cmd_args)
    if payload == -1:  #Error Occured
        return -1

    print("Initializing socket...") 
    udp_socket = InitSocket(cmd_args)

    print("Sending intent message...")                            
    TID = SendIntentMessage(udp_socket,cmd_args) 

    print("Sending payload...")
    SendPayload(cmd_args,udp_socket,TID,payload)

if __name__ == "__main__":
    main()

