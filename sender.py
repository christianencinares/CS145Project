from cmath import exp
import socket
import time
import os
import argparse
import requests

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
    message = ("ID{}".format(args.uniqueid)).encode()   #Encode the intent message IDWWWWWWWW 
    socket.sendto(message, (args.address, args.receiverport))    #Send the intent message using receiver's IP and port
    TID, server = socket.recvfrom(8)          #Receive the response from receiver
    print("TID:",TID.decode())                          #Print the transcation ID from the receiver
    return TID.decode()                                   

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
    exponential_lock = 0
    fine_tune_lock = 0
    Ave_RTT = 10
    incrementer = 0
    n = 0
    while transmitted_payload != payload_length:
        data_packet = ("ID{}SN{:07d}TXN{:07d}LAST{}{}".format(args.uniqueid,int(sequence_number),int(TID),Z,payload[payload_start:payload_end])).encode()
        print("------------------------------------------------------")
        print("Attempting to send: ",data_packet)
        print("SIZE: ",payload_size,"SN:",sequence_number,"EL:",exponential_lock,"FTL:",fine_tune_lock)
        start = time.time()
        socket.settimeout(Ave_RTT)
        try:
            socket.sendto(data_packet, (args.address, args.receiverport))
            receiver_ack, server = socket.recvfrom(100)
            end = time.time()
            RTT = end - start
            sequence_number = sequence_number+1
            transmitted_payload = transmitted_payload + payload_size
            print("SUCCESS:",receiver_ack,"RTT:",RTT,"Transmitted:",transmitted_payload,"/",payload_length)
            print("------------------------------------------------------")
            if payload_size >  payload_length - payload_end: #Last packet, just send the rest of the payload.
                payload_size = payload_length - payload_end
                payload_start = payload_end
                payload_end = payload_length
                Z = 1
            else:
                if exponential_lock == 0:   #Exponential payload size increase
                    payload_size = payload_size * 2
                    payload_start = payload_end
                    payload_end = payload_end + payload_size
                elif fine_tune_lock == 0:   #Incremental payload size increase
                    incrementer = incrementer + 1
                    payload_size = payload_size + incrementer
                    payload_start = payload_end
                    payload_end = payload_end + payload_size
                else:                       #Optimal payload size attained
                    payload_start = payload_end
                    payload_end = payload_end + payload_size
        except:
            if exponential_lock == 0:
                #revert
                payload_start = payload_end - payload_size
                payload_size = payload_size//2 
                payload_end = payload_start + payload_size
                exponential_lock = 1
            elif fine_tune_lock == 0:
                payload_start = payload_end - payload_size
                payload_size = payload_size - incrementer #revert
                payload_end = payload_start + payload_size
                fine_tune_lock = 1
            print("Timeout")
            
        
        n = n+1
        Ave_RTT = (Ave_RTT*n + RTT)/(n+1)
        print("Average RTT is: ",Ave_RTT)
        

def main():
    cmd_args = GetArgs()
    print("Fetching payload file...") 
    #FetchNewPayload(cmd_args)

    print("Initializing socket...") 
    udp_socket = InitSocket(cmd_args)

    print("Sending intent message...")                            
    TID = SendIntentMessage(udp_socket,cmd_args) 

    print("Reading payload file...")
    payload = GetFileContents(cmd_args)
    if payload == -1:  #Error Occured
        return -1

    print("Sending payload...")
    SendPayload(cmd_args,udp_socket,TID,payload)

if __name__ == "__main__":
    main()

