#!/usr/bin/python           # This is client.py file

import socket               # Import socket module
import time

s = socket.socket()         # Create a socket object
host = socket.gethostname() # Get local machine name
port = 1024                # Reserve a port for your service.

s.connect((host, port))
while 1:
	s.send('go|')
	print s.recv(1024)
	time.sleep(1)
