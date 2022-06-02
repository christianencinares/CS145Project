import socket
import sys
import os
import argparse
import requests

#Gets the arguments from the command line
def GetArgs():
    parser = argparse.ArgumentParser()  #Initialize the parser. Can handle switched and missing arguments.     
    #Define the arguments filepath,address,receiverport,senderport,and uniqueid.                   
    parser.add_argument("-f", "--filepath", help="File path of the payload to send", type=str, required=True)           
    parser.add_argument("-a", "--address", help="IP address of receiver", type=str, required=True)     
    parser.add_argument("-s", "--receiverport", help="Port receiver will listen to", type=int, required=True)  
    parser.add_argument("-c", "--senderport", help="Port sender will listen to", type=int, required=True)     
    parser.add_argument("-i", "--uniqueid", help="Unique Student ID", type=str, required=True)         
    args = parser.parse_args() #Parse the entered command line arguments according to the arguments defined in parser 
    return args

#Send the intent message to the receiver 
def SendIntentMessage(socket,args):
    message = ("ID{}".format(args.uniqueid)).encode()   #Encode the intent message IDWWWWWWWW in ascii
    socket.sendto(message, (args.address, args.receiverport))    #Send the intent message using receiver's IP and port
    TID, server = socket.recvfrom(8)          #Receive the response from receiver
    print(TID.decode())                          #Print the transcation ID from the receiver
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

def GenerateDataPacket(args,sequence_number,transaction_id,Z,payload):
    sequence_number = int(sequence_number)
    transaction_id = int(transaction_id)
    packet = ("ID{}SN{:07d}TXN{:07d}LAST{}{}".format(args.uniqueid,sequence_number,transaction_id,Z,payload)).encode(encoding="ascii")
    return packet

def FetchNewPayload(args):
    url = "http://3.0.248.41:5000/get_data?student_id={}".format(args.uniqueid)
    response = requests.get(url)
    open(args.filepath, 'wb').write(response.content) #Automatically creates file if DNE

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

    print("Generating Data Packet...")
    data_packet = GenerateDataPacket(cmd_args,0,TID,0,payload)
    print("Sending Data Packet...")
    udp_socket.sendto(data_packet, (cmd_args.address, cmd_args.receiverport))
    receiver_ack, server = udp_socket.recvfrom(100)
    print(receiver_ack)

if __name__ == "__main__":
    main()

