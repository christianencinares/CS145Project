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

#Retrieve the arguments from the command line. Using the argparse module allows easier retrival of values and can handle switched or missing arguments. 
def GetArgs():
    parser = argparse.ArgumentParser()  #Initialize an ArgumentParser object

    #Define the arguments: filepath, address, receiverport, senderport, and uniqueid. Help messages can be accessed by typing -h or --help.                    
    parser.add_argument("-f", "--filepath", help="File path of the payload to send", type=str, default= FILEPATH)           
    parser.add_argument("-a", "--address", help="IP address of receiver", type=str, default= ADDRESS)     
    parser.add_argument("-s", "--receiverport", help="Port that receiver will listen to", type=int, default= RECEIVERPORT)  
    parser.add_argument("-c", "--senderport", help="Port that sender will listen to", type=int, default= SENDERPORT)     
    parser.add_argument("-i", "--uniqueid", help="Unique Student ID", type=str, default = UID)         

    args = parser.parse_args()          #Parse the entered command line arguments according to the arguments defined above 
    return args                         #Return an object containing the argument values

#Sends the intent message to the receiver and returns the Transaction ID
def SendIntentMessage(socket,args):
    socket.settimeout(3)                                                #Set timeout for 3 seconds
    try:
        while True: 
            message = ("ID{}".format(args.uniqueid)).encode()           #Encode the intent message: ID<uniqueid>
            socket.sendto(message, (args.address, args.receiverport))   #Send the intent message using receiver's IP and port
            TID, server = socket.recvfrom(8)                            #Receive the response containing the TID from the receiver. Buffer size 8 bytes.
            TID = TID.decode()                                          #Decode the response
            if TID == 'Existing':                                       #If the TID is 'Existing', then someone else is using TID. Try again after some time.
                time.sleep(2)                                           #Wait for 2 seconds
                print("ERROR: Transaction ID currently in use. Reattempting...")
                continue                                                #Go back to beginning of loop
            print("TID:",TID)                                       
            return TID                                                  #Return the TID
    except:
        print("ERROR: Cannot establish connection with receiver")
        return -1                                                       #Return error code

#Initializes the UDP socket
def InitSocket(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Create a UDP socket
    sock.bind(('',args.senderport))                         #Bind the socket to the sender's port
    return sock                                             #Return the socket

#Retrieves payload from specified file path
def GetFileContents(args):
    if os.path.isfile(args.filepath):                 #Check if the file exists
        file = open(args.filepath, 'rt')              #Open the file in read-text mode
        file_size = os.path.getsize(args.filepath)    #Get the size of the file
        file_contents = file.read(file_size)          #Read the file contents using the size of the file
        file.close()                                  #Close the file
        return file_contents                          #Return the payload
    else:
        print("ERROR: File does not exist")           #Print an error message if file does not exist
        return -1                                     #Return error code   

#Download new payload file
def FetchNewPayload(args):
    url = "http://3.0.248.41:5000/get_data?student_id={}".format(args.uniqueid) #Use unique ID in URL to fetch payload file
    response = requests.get(url)                                                #Send GET request to server
    open(args.filepath, 'wb').write(response.content)                           #Automatically creates file if DNE

#Sends the payload to the receiver through over packets  
def SendPayload(args,socket,TID,payload):
    #/=====================Variable Initializations=====================/
    payload_start = 0               #Starting index for current payload segment 
    payload_end = 1                 #Ending index for current payload segment
    payload_size = 1                #Size of payload segment to be transmitted
    transmitted_payload = 0         #Counter for number of characters transmitted
    sequence_number = 0             #Initialize the sequence number to 0
    adaptive_size_mode = 0          #Current mode for adaptive payload size (0 = initial guess, 1 = exponential increase , 2 = incremental increase)
    RTT = 0                         #Initialize the RTT per packet to 0
    Ave_RTT = 10                    #Initialize the average RTT to 10s to be used in first and suceeding timeouts
    Z = 0                           #Initialize the last packet identifier to 0
    incrementer = 1                 #Initialize the incrementer for the exponential increase mode to 1
    overestimated = 0               #Initialize a flag to determine if initial guess was overestimated

    payload_length = len(payload)   #Get the length of the payload
    start_elapsed_time = time.time()#Start timer for elapsed time
    
    #/=====================Sending and Parameter Estimation=====================/
    #While loop continuously sends packets to receiver until overtime or when all the payload has been transmitted
    print("------------------------------------------------------")
    while (transmitted_payload != payload_length) and (time.time() - start_elapsed_time < 125): 
        #Try sending packet
        try:
            #Compose packet to be sent to receiver
            data_packet = ("ID{}SN{:07d}TXN{:07d}LAST{}{}".format(args.uniqueid,int(sequence_number),int(TID),Z,payload[payload_start:payload_end])).encode()
            print("Attempting to send: ",data_packet)
            print("SIZE: ",payload_size,"| SN:",sequence_number,"| Adapative Size Mode:",adaptive_size_mode,'| Timeout Value:',Ave_RTT+1)
            socket.settimeout(Ave_RTT+1)     #Set the socket timeout (1 is added to avoid timing out on the actual RTT)
            start = time.time()              #Start timer for RTT
            socket.sendto(data_packet, (args.address, args.receiverport))   #Send packet to receiver
            receiver_ack, server = socket.recvfrom(100)                     #Receive ACK from receiver
            receiver_ack = receiver_ack.decode()                            #Decode the ACK
            end = time.time()                                               #End timer for RTT

            if end-start > 1:                                               #Do not count RTT if it is less than 1 second
                RTT = end - start                                           #Calculate RTT for this segment(Successful transmission)
                if sequence_number == 0:       #If this is the first packet, then set the average RTT to the RTT of this segment for the next segment's timeout
                    Ave_RTT = RTT 
                else:                          #If this is not the first packet, then calculate the average RTT
                    Ave_RTT = (Ave_RTT*sequence_number + RTT)/(sequence_number+1)
                print("Average RTT: ",Ave_RTT)
                
            transmitted_payload = transmitted_payload + payload_size #Update number of characters transmitted
            elapsed_time = time.time() - start_elapsed_time          #Check elapsed time for this segment
            print("[SUCCESS] ACK:",receiver_ack,"| RTT:",RTT,"| Transmitted:",transmitted_payload,"/",payload_length,"| Elapsed Time:",elapsed_time)
            print("------------------------------------------------------")
            
            #Prepare Variables for next segment
            if payload_size >  payload_length - payload_end:    #Check if current payload size exceeds the remaining payload to send
                payload_size = payload_length - payload_end     #Set payload size to the remaining payload's length
                payload_start = payload_end                     #Set the payload start index to the end of the last segment
                payload_end = payload_length                    #Set the end index to the end of the payload
                Z = 1                                           #Denotes next segment to be sent is the last segment

            else:
                if adaptive_size_mode == 0:                                        #Initial guessing mode
                    if sequence_number == 0 and overestimated == 0:                #Compute initial guess payload size 
                        numofpackets = math.ceil(80/RTT)                           #Calculate the number of packets that can fit under target time using a sample RTT
                        payload_size = int(math.ceil(payload_length/numofpackets)) #Calculate the baseline payload size
                    else:                                                          #Initial guess size didn't time out. Try increasing payload size
                        incrementer = incrementer * 3             
                        payload_size = payload_size + incrementer #Increment current payload size
                        adaptive_size_mode = 1                    #Change to exponential increase mode
                elif adaptive_size_mode == 1:                     #Exponential payload size increase mode
                    incrementer = incrementer * 3                 #Increase the payload size by a factor of 3
                    payload_size = payload_size + incrementer     #Increment current payload size 
                elif adaptive_size_mode == 2:                     #Incremental payload size increase mode
                    payload_size = payload_size + 1               #Increment current payload size by 1
                #else Optimal payload size attained, no payload size change

                #Adjust indices to next payload segment
                payload_start = payload_end 
                payload_end = payload_end + payload_size

            sequence_number = sequence_number+1 #Increment sequence number for next segment
        except:
            elapsed_time = time.time() - start_elapsed_time       #Check elapsed time for this segment
            payload_start = payload_end - payload_size            #Revert to previous successful segment start index
            #Timeout RTTs are not counted in Ave_RTT since they will increase the timeout value

            #Adapative payload size error handlers
            #Bad initial guess for payload size  or bad intial timeout RTT
            if adaptive_size_mode == 0: 
                Ave_RTT = Ave_RTT + 0.5                           #Increase the average RTT by 0.5s
                payload_size = math.ceil(payload_size * 1/2)      #Halve the initial guess payload size
                overestimated = 1                                 #Set the initial guess overestimated flag to 1
            elif adaptive_size_mode == 1:                         #Exponential increase mode reached timeout
                payload_size = payload_size - incrementer         #Revert increase
                adaptive_size_mode = 2                            #Switch to incremental increase mode     
            elif adaptive_size_mode == 2:                         #Incremental increase mode reached timeout
                payload_size = payload_size - 1                   #Revert increase
                adaptive_size_mode = 3                            #Switch to optimal payload size mode
            else:                                                 #Incremental increase mode reached timeout
                Ave_RTT = Ave_RTT + 1 #Increase timeout 

            payload_end = payload_start + payload_size            #Change end index according to new payload size
            print("[TIMEOUT] Transmitted:",transmitted_payload,"/",payload_length,"| Elapsed Time:",elapsed_time)
            print("------------------------------------------------------")
        
        
    if transmitted_payload == payload_length:   #Check if all payload has been transmitted
        print("TRANSMISSION SUCCESSFUL")
    else:                                       #If not all packets sent, then transmission failed
        print("TRANSMISSION FAILED with ",transmitted_payload,"/",payload_length,"transmitted")

        
#Main function. Calls other helper functions.
def main():
    cmd_args = GetArgs()                        #Get command line arguments 

    print("Fetching payload file...") 
    FetchNewPayload(cmd_args)                   #Fetch new payload file

    print("Reading payload file...")
    payload = GetFileContents(cmd_args)         #Read payload file
    if payload == -1:  #File path didn't exist
        return -1

    print("Initializing socket...") 
    udp_socket = InitSocket(cmd_args)            #Initialize UDP socket

    print("Sending intent message...")                            
    TID = SendIntentMessage(udp_socket,cmd_args) #Send intent message to receiver
    if TID == -1:      #Couldn't connect with receiver                
        return -1

    print("Sending payload...")
    SendPayload(cmd_args,udp_socket,TID,payload) #Send payload to receiver

    return 0

if __name__ == "__main__":
    main()

