# CS 145 Project:  Parameter-Adaptive Reliable UDP-based Protocol

An implementation of the sender side of a protocol, as well as its parameter estimation module or component.
This project is part of the course requirements for CS 145 for A.Y. 2021-2022, 2nd Semester.

## Prerequisites
This program is written in **Python 3**. As such, ensure that you have the correct version installed. 
The project also makes use of the following modules:
- socket
- time
- os
- argparse
- requests
- math

If your IDE reports that you're missing one of these modules, you may have to install it by running the following command in your terminal:\
`pip install <module_name>`
## Command Syntax 
```
python3 sender.py -f <FILEPATH> -a <ADDRESS> -s <RECEIVERPORT> -c <SENDERPORT> -i <UNIQUEID>
```
or alternatively,
```
python3 sender.py --filepath <FILEPATH> --address <ADDRESS> --receiverport <RECEIVERPORT> --senderport <SENDERPORT> --uniqueid <UNIQUEID>
```

Where FILEPATH is the directory for the payload you want to send, ADDRESS is the IP address of the server/receiver, RECEIVERPORT is the port the receiver will listen to, SENDERPORT is the port the sender will listen to, and UNIQUEID is the unique student ID assigned to you.

Note that a flag can be omitted and the program will instead use its default value. The arguments can also be reordered/switched as long as the appropriate flag-value pair are still together.

The default values are:
- “ecd04286.txt” for the file path
- “10.0.7.141” for the receiver’s IP address 
- “9000” for the receiver’s port
- “6696” for the sender’s port 
- "ecd04286" for the Unique ID.

You may view a summarized syntax guide in your terminal by entering `python3 sender.py -h` or `python3 sender.py --h`
## Usage
>This guide assumes that there is already an appropriate receiver/server instance setup to respond to the sender and that you have the necessary information to connect to the server such as its IP address and port. Additionally, this also assumes that you have an assigned dedicated sender port and unique ID.
1. In your terminal, navigate to the directory where you downloaded this project's files. (e.g. using `cd <directory>`)
2. Run the following command in your terminal: 
  ```
  python3 sender.py -f <FILEPATH> -a <ADDRESS> -s <RECEIVERPORT> -c <SENDERPORT> -i <UNIQUEID>
  ```
3. Wait for the process/program to finish transmitting the payload.
4. Verify the status or results of your transaction in the Transaction Generation/Results Server (TGRS).

If you want to prevent the program from fetching new payload files, simply comment out the line 
```
FetchNewPayload(cmd_args)
``` 
under the main function.

