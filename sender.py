import socket
import sys
import os
import argparse

def GetArgs():
    #Initialize the parser. Can handle switched and missing arguments.
    parser = argparse.ArgumentParser()                          
    parser.add_argument("-f", "--file", help="File containing payload to send", type=str, required=True)           
    parser.add_argument("-a", "--address", help="IP address of receiver", type=str, required=True)     
    parser.add_argument("-s", "--receiverport", help="Port receiver will listen to", type=int, required=True)  
    parser.add_argument("-c", "--senderport", help="Port sender will listen to", type=int, required=True)     
    parser.add_argument("-i", "--uniqueid", help="Unique Student ID", type=str, required=True)         
    #Parse the entered command line arguments according to the arguments defined in parser 
    args = parser.parse_args() 
    return args.file, args.address, args.receiverport, args.senderport, args.uniqueid

def SendIntentMessage(RECEIVER_IP,RECEIVER_PORT,SENDER_PORT,UNIQUE_ID):
    Message = "ID%s"%UNIQUE_ID.encode(encoding="ascii")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('',SENDER_PORT))
    sock.sendto(Message, (RECEIVER_IP, RECEIVER_PORT))
    data, server = sock.recvfrom(1024)
    print(data.decode(decoding="ascii"))

def main():
    file,address,receiverport,senderport,uniqueid = GetArgs()
    print(file,address,receiverport,senderport,uniqueid)
    SendIntentMessage(address,receiverport,senderport,uniqueid)
    
    #Check if the file exists
    """
    if os.path.isfile(args.file):   
        print("File exists")
        f = open(args.file, 'rb')
        file_size = os.path.getsize(args.file)
        data = f.read(file_size)
        f.close()
        print(data)
        IntentMessage()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(data, (args.address, args.receiverport))
        data, server = sock.recvfrom(1024)
        print(data.decode())
    else:
        print("File does not exist")
    """
if __name__ == "__main__":
    main()

#python sender.py -f path/to/file.txt -a 10.0.7.141 -s 9000 -c 6696 -i ecd04286
