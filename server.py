#!/usr/bin/python

import socket
import signal
import sys
import os
import inspect
from threading import Thread
import time
from time import strftime
import traceback
import string
import subprocess
import csv
import netifaces
import struct
import select

#global
BUFSIZE = 1024*8
THISFILENAME = inspect.getfile(inspect.currentframe())

#packet-related
PACKET_SIZE   = 1460
HEADER_FORMAT = struct.Struct('dii')
PADDING_SIZE  = PACKET_SIZE - HEADER_FORMAT.size
PADDING       = os.urandom(PADDING_SIZE)
 
 
#SIGINT
def signal_handler( *args ):
	print >> sys.stderr, 'SIGINT: Quit gracefully'
	sys.exit(0)
	

#wait, clock syn, minutes
def wait_for_min( mins ):
	print >> sys.stderr, '%s %s' % ( 'now:', time.strftime("%H:%M:%S", time.localtime(time.time())) )
	future_time = time.time() + ( mins * 60 )
	while True:
		cur_time = time.time()
		if( cur_time == future_time ):
			break
		delta = future_time - cur_time
		if( delta > 1 ):
			time.sleep(15)
			#print something to wait until...
			print >> sys.stderr, '%s %s , %s %s' % ( 'wait to sync at:', time.strftime("%H:%M:%S", time.localtime(future_time)), 'now:', time.strftime("%H:%M:%S", time.localtime(time.time())) )
		else:
			break


#TCP socket open
def set_tcp_socket( server_addr, server_port ):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		return s
	except socket.error as e:
		if s:
			s.close() 
		print >> sys.stderr, "could not open socket: ", server_addr,":",server_port, e
		raise


#UDP socket open
def set_udp_socket( iface, port ):
     try:
          #UDP
          s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
          #s.setblocking(0) ???
          
          server_addr = netifaces.ifaddresses(iface)[2][0]['addr']
          s.bind( ( server_addr, port ) )
          
          return s, server_addr
     except socket.error as e:
          print >> sys.stderr, "could not open socket: ", iface, e
          if s:
               s.close() 
          raise


#TCP/UDP socket close
def unset_socket( socket ):
	try:
		socket.close()
	except socket.error as e:
		print >> sys.stderr, "could not close socket: ", socket, e
		raise


#send
def send_socket( s, client_addr, client_port, nr_packets, epoch ):
	next_send_time = 0
	for i in range(nr_packets):
		# wait for next send time
		while True:
			curr_time = time.time()
			delta = next_send_time - curr_time
			if delta <= 0:
				break
			if delta > 0.05:
				time.sleep(delta - 0.025)
		# send packet
		pkt_timestamp = time.time()
		header = HEADER_FORMAT.pack(pkt_timestamp, epoch, i)
		payload = header + PADDING
		try:
			s.sendto(payload, (client_addr, client_port))
		except Exception as e:
			print >> sys.stderr, 'sendto error:', e
			break
		# define next send time
		next_send_time = time.time() + 1


#receive
def recv_socket( s, epoch ):
     rcv_packets = []
     timeout = 300
     client_addr = None
     while True:
	if client_addr == None:
	     recvready = select.select([s], [], [])
	else:
	     recvready = select.select([s], [], [], timeout)
	     if not recvready[0]:
		  break
	# receive
	payload, client_addr = s.recvfrom(BUFSIZE)
	recv_timestamp = time.time()
	# reply
	try:
		s.sendto(payload, client_addr)
	except Exception as e:
		print >> sys.stderr, 'sendto error:', e
		break
	(send_timestamp, epoch, packet_nr) = HEADER_FORMAT.unpack(payload[:HEADER_FORMAT.size])
	rcv_packets.append([recv_timestamp, epoch, packet_nr, recv_timestamp-send_timestamp])

     return rcv_packets, client_addr


def evaluate_packet_delay( packets, epoch, nr_packets, filename ):
	with open(filename + ".csv", "a") as csvfile:
		w = csv.writer(csvfile, delimiter=',')

		packet_dict={}
		for packet in packets:
			packet_dict[packet[2]] = packet

		w.writerow(['timestamp', 'epoch', 'nr_packet', 'delta', 'jitter', 'owd'])
		for curr in range(nr_packets):
			try:
				prev = curr - 1
				curr_packet = packet_dict[curr]
				prev_packet = packet_dict[prev]
			except:
				# there is no pair of packets
				continue

			delta = curr_packet[0] - prev_packet[0]
			jitter = delta - 1.0
			timestamp = int(round(curr_packet[0]))
			owd = curr_packet[3]
			w.writerow([timestamp, epoch, curr, delta, jitter, owd])


#client
def server( *args ):  
	finish = 0
	server_addr = args[0]
	server_port = args[1]
	iface = args[2]
	nr_packets = args[3]
	nr_probe = args[4]
	filename = args[5]
	
	try:
		epoch = 1
		while( epoch <= nr_probe ):
			try:
				#ntp
				#subprocess.call("/etc/init.d/ntp stop", shell=True)
				#subprocess.call("pkill ntpd", shell=True)
				#subprocess.call("ntpdate 129.240.2.6", shell=True) #ntp1.uio.no
				#subprocess.call("/etc/init.d/ntp start", shell=True)
				
				#UDP socket
				while True:
					try:
						socket, addr = set_udp_socket( iface, server_port )
						print 'UDP: %s:%d' % (addr, server_port) + '\n'
						break
					except:
						time.sleep(0.1)
						print >> sys.stderr, '\n', 'wait for socket'

				#recv: ON
				print >> sys.stderr, '\n', 'SERVER - RECV'
				rcv_packets, client_addr = recv_socket( socket, epoch )
				#print 'packets received in server %d' % len(rcv_packets) + '\n'
				#print 'packet loss is %d' % (nr_packets - len(rcv_packets)) + '\n'

				#send: ON
				#print >> sys.stderr, '\n', 'SERVER - SEND'
				#send_socket( socket, client_addr[0], client_addr[1], nr_packets, epoch )
				
				evaluate_packet_delay( rcv_packets, epoch, nr_packets, ('SERVER-DELAY-'+iface+'-'+filename+time.strftime("%m%d%H:%M")) )
				
				unset_socket( socket )
				print >> sys.stderr, '\n', 'SERVER - DONE'
					 
			except:
				e = sys.exc_info()
				for file, linenr, function, text in traceback.extract_tb(e[2]):
					error = '%s %s %s %s %s %s %s' % (file, 'line', linenr, 'in', function, '->', e[:2])
					print >> sys.stderr, error;
					
			wait_for_min( 0.1 ) 
			epoch+=1
	
	except( KeyboardInterrupt, SystemExit ):
		print >> sys.stderr, 'close tcp socket: Exit! -> ',str(THISFILENAME);
	finally:
		error = '%s %s' % ('close tcp socket -> ',str(THISFILENAME))
		print >> sys.stderr, error
		try:
		     interfaceinfo.stop()
		     socket.close()
		except:
		     pass		


#usage:
def usage():
	print >> sys.stderr, '\n' + str(THISFILENAME)+" [server IP] [server port] [interface] [nr. of packets (int)] [number of epoches (int)] [filename]" + '\n'
	sys.exit(0)


#SERVER:
if __name__ == '__main__':

	#SIGINT 
	signal.signal(signal.SIGINT, signal_handler)

	if( len(sys.argv) < 7 ):
		usage()
	elif( len(sys.argv) == 7 ):
			server_addr = sys.argv[1]
			server_port = int(sys.argv[2])
			iface = sys.argv[3]
			nr_packets = int(sys.argv[4])
			nr_probe = int(sys.argv[5])
			filename = sys.argv[6]
			#server
			server(server_addr, server_port, iface, nr_packets, nr_probe, filename)
	else:
		usage()
		
