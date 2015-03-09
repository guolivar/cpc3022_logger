#!/usr/bin/env python
# Load the libraries
import serial # Serial communications
import time # Timing utilities
import subprocess # Shell utilities ... compressing data files

# Set the time constants
rec_time=time.gmtime()
timestamp = time.strftime("%Y/%m/%d %H:%M:%S GMT",rec_time)
prev_minute=rec_time[4]
# Set the minute averaging variable
min_concentration=0
n_concentration = 0
# Set the pre/post SQL statement values
insert_statement = """INSERT INTO data.fixedmeasurements (parameterid,value,siteid,recordtime) VALUES (%s,%s,%s,timestamptz %s);"""
insert_statement_file = """INSERT INTO data.fixedmeasurements (parameterid,value,siteid,recordtime) VALUES (%s,'%s',%s,timestamptz '%s');\n"""
# Read the settings from the settings file
settings_file = open("./settings.txt")
# e.g. "/dev/ttyUSB0"
port = settings_file.readline().rstrip('\n')
# path for data files
# e.g. "/home/logger/datacpc3775/"
datapath = settings_file.readline().rstrip('\n')
prev_file_name = datapath+time.strftime("%Y%m%d.txt",rec_time)
# psql connection string
# e.g "user=datauser password=l3tme1n host=penap-data.dyndns.org dbname=didactic port=5432"
db_conn = settings_file.readline().rstrip('\n')
# ID values for the parameters and site (DATA, ERROR, SITE)
# e.g. "408,409,2" == CPCdata,CPCerror,QueenStreet
params = settings_file.readline().rstrip('\n').split(",")
# Close the settings file
settings_file.close()
# Hacks to work with custom end of line
eol = b'\r'
leneol = len(eol)
bline = bytearray()
# Open the serial port and clean the I/O buffer
ser = serial.Serial(port,115200)
ser.flushInput()
ser.flushOutput()
# Start the logging
while True:
	# Set the time for the record
	rec_time_s = int(time.time())
	rec_time=time.gmtime()
	timestamp = time.strftime("%Y/%m/%d %H:%M:%S GMT",rec_time)
	# Change the counters' display to show the time
	ser.write('WLogging\r')
	dump_me = ser.read(3)
	
	# Request display concentration from the instrument
	ser.write('RD\r')
	# Get data from the instrument
	while True:
		c = ser.read(1)
		bline += c
		if bline[-leneol:] == eol:
			break
	# Parse the data line
	file_line = bline.decode("utf-8")[:-leneol]
	concentration = eval(bline.decode("utf-8")[:-leneol])
	
	# Request Liquid Level from the instrument
	ser.write('R0\r')
	# Get data from the instrument
	while True:
		c = ser.read(1)
		bline += c
		if bline[-leneol:] == eol:
			break
	# Parse the response
	file_line = file_line + ',' + bline.decode("utf-8")[:-leneol]
	liq_OK = bline.decode("utf-8")[:-leneol]=='FULL'
	
	# Request CondT from the instrument
	ser.write('R1\r')
	# Get data from the instrument
	while True:
		c = ser.read(1)
		bline += c
		if bline[-leneol:] == eol:
			break
	# Parse the response
	file_line = file_line + ',' + bline.decode("utf-8")[:-leneol]
	CondT = eval(bline.decode("utf-8")[:-leneol])
	
	# Request SatT from the instrument
	ser.write('R2\r')
	# Get data from the instrument
	while True:
		c = ser.read(1)
		bline += c
		if bline[-leneol:] == eol:
			break
	# Parse the response
	file_line = file_line + ',' + bline.decode("utf-8")[:-leneol]
	SatT = eval(bline.decode("utf-8")[:-leneol])
	
	# Request OptT from the instrument
	ser.write('R3\r')
	# Get data from the instrument
	while True:
		c = ser.read(1)
		bline += c
		if bline[-leneol:] == eol:
			break
	# Parse the response
	file_line = file_line + ',' + bline.decode("utf-8")[:-leneol]
	OptT = eval(bline.decode("utf-8")[:-leneol])
	
	# Request flow from the instrument
	ser.write('R4\r')
	# Get data from the instrument
	while True:
		c = ser.read(1)
		bline += c
		if bline[-leneol:] == eol:
			break
	# Parse the response
	file_line = file_line + ',' + bline.decode("utf-8")[:-leneol]
	flow = eval(bline.decode("utf-8")[:-leneol])
	
	# Restore instrument display
	ser.write('W\r')
	dump_me = ser.read(3)
		
	split_indx = line.find(',')
	error_message = line[split_indx+1:]
	# Make the line pretty for the file
	file_line = timestamp+','+line
	# Save it to the appropriate file
	current_file_name = datapath+time.strftime("%Y%m%d.txt",rec_time)
	current_file = open(current_file_name,"a")
	current_file.write(file_line+"\n")
	current_file.flush()
	current_file.close()
	line = ""
	bline = bytearray()
	## Is it the top of the minute?
	#if rec_time[4] != prev_minute:
		#prev_minute = rec_time[4]
		## YES! --> generate the psql statement
		## Average for the minute with what we have
		#min_concentration = min_concentration / n_concentration
		## Print the missing insert statements to a file
		## to be processed by another programme
		#sql_buffer = open(datapath + "SQL/inserts.sql","a")
		## Insert the DATA record
		#sql_buffer.write(insert_statement_file%
		#(params[0],min_concentration,params[2],timestamp))
		## Insert the ERROR record
		#sql_buffer.write(insert_statement_file%
		#(params[0],line[split_indx+1:],params[2],timestamp))
		#sql_buffer.flush()
		#sql_buffer.close()
	#min_concentration = 0
	#n_concentration = 0
	# Is it the last minute of the day?
	if current_file_name != prev_file_name:
		subprocess.call(["gzip",prev_file_name])
		prev_file_name = current_file_name
	# Wait until the next second
	while int(time.time())<=rec_time_s:
		#wait a few miliseconds
		time.sleep(0.05)	
print('I\'m done')