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
#import numpy as np
import netifaces
import struct
import select

#common
import interfaceinfo
import pathinfo

#global
BUFSIZE = 1024*8
THISFILENAME = inspect.getfile(inspect.currentframe())
global f
f = 0
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
          
          #check pppX or ICE and bind
          if ( str(iface) == 'eth1' ):
               client_addr = '10.110.111.2'
          if ( str(iface).find('ppp') >= 0 ):			
               client_addr = netifaces.ifaddresses(str(iface))[2][0]['addr']
          s.bind( ( client_addr, port ) )
          
          return s, client_addr
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
def send_socket( s, server_addr, server_port, iface, nr_packets, epoch, filename ):
	next_send_time = 0
	global f
	#rcv_packets = []
	file = 'CLIENT-'+iface+'-'+filename+time.strftime("%m%d%H:%M")
	#with open(file + ".csv", "a") as csvfile:
        #	w = csv.writer(csvfile, delimiter=',')
	#        w.writerow(['sent_time', 'received_time', 'rtt', 'epoch', 'pkt-Nr', 'Delta', 'Jitter', 'cur_rrc', 'cur_mode', 'cur_submode', 'cur_cellid', 'cur_lac', 'cur_rssi'])

	for i in range(nr_packets):
		# wait for next send time
		while True:
			curr_time = time.time()
			delta = next_send_time - curr_time
			if delta <= 0:
				break
			# wait to receive packet
			if delta > 0.05:
				recvready = select.select([s], [], [], (delta - 0.025))
				if recvready[0]:
					payload = s.recv(BUFSIZE)
					recv_timestamp = time.time()
					#modem
					try:
						modem = pathinfo.getinfo()
						cur_rrc_state = modem[iface]['rrc']
					except:
						cur_rrc_state = 'N'
					try:
						cur_mode = modem[iface]['mode']
					except:
						cur_mode = 'N'
					try:
						cur_submode = modem[iface]['submode']
					except:
						cur_submode = 'N'
					try:
						cur_lac = modem[iface]['lac']	
					except:
						cur_lac = 'N'					
					try:
						cur_cellid = modem[iface]['cellid']
					except:
						cur_cellid = 'N'
					try:
						cur_rssi = modem[iface]['rssi']
					except:
						cur_rssi = 'N'
					(send_timestamp, epoch, packet_nr) = HEADER_FORMAT.unpack(payload[:HEADER_FORMAT.size])
					with open(file + ".csv", "a") as cf:
                               			w1 = csv.writer(cf, delimiter=',')
						w1.writerow([int(round(send_timestamp)), int(round(recv_timestamp)), round(float(recv_timestamp-send_timestamp),3), epoch, packet_nr, cur_rrc_state, cur_mode, cur_submode, cur_cellid, cur_lac, cur_rssi])
						#rcv_packets.append([send_timestamp, epoch, packet_nr, recv_timestamp-send_timestamp, cur_rrc_state, cur_mode, cur_submode, cur_cellid, cur_lac, cur_rssi])
		# send packet
		send_timestamp = time.time()
		header = HEADER_FORMAT.pack(send_timestamp, epoch, i)
		payload = header + PADDING
		try:
			#print s 
			#print 'before\n'
			s.sendto(payload, (server_addr, server_port))
		except Exception as e:
			print >> sys.stderr, 'sendto error:', e
			#break
			print 'INTERFACE Problem...getting new socket.... \n'
			#s, client_addr = regen(s, iface, server_port)
			f = 1
	        	#evaluate_packet( rcv_packets, epoch, nr_packets, ('CLIENT-'+iface+'-'+filename+time.strftime("%m%d%H:%M")) )
                	break
		# next send time
		next_send_time = time.time() + 1
	print i
	return i

#regenrate socket after interface down
def regen(s1, iface, server_port):
	try:
		unset_socket(s1)
	except:
		pass

	try:
                pathinfo.stop()
        except:
                pass

	try:
                interfaceinfo.stop()
        except:
                pass

	while True:
		try:
			# MULTI
			interfaceinfo.start()
			break
        	except:
			sleep(0.1)
                	pass

	try:
		# pathinfo
		pathinfo.start()
	except:
		pass

	while True:
		try:
			socket, client_addr = set_udp_socket( iface, server_port )
			print 'UDP: %s:%d' % (client_addr, server_port) + '\n'
			break
		except:
			time.sleep(0.1)
			print >> sys.stderr, '\n', 'wait for socket'
	return socket, client_addr


#packet loss
def packet_loss(nr_packets, rcv_packets):
	nr_packets_received = len(rcv_packets)
	print 'packet sent packet received %d %d' % (nr_packets, nr_packets_received) + '\n' 
	nr_loss = nr_packets - nr_packets_received
	print 'loss no %d' % nr_loss + '\n'
	percent_loss = (float(nr_loss)/float(nr_packets)) * 100
	print 'packet loss %.2f' % percent_loss + ' percent\n'
	return percent_loss


#receive
def recv_socket( s, epoch ):
	packets = []
	timeout = 30
	while True:
		recvready = select.select([s], [], [], timeout)
		if not recvready[0]:
		     break
		payload, server_addr = s.recvfrom(BUFSIZE)
		recv_timestamp = time.time()
		(timestamp, epoch, packet_nr) = HEADER_FORMAT.unpack(payload[:HEADER_FORMAT.size])
		packets.append([recv_timestamp, epoch, packet_nr, recv_timestamp-timestamp])
	return packets


#wait until iface returned by MULTI is UP
def wait_for_interface( iface ):
     while True:
          ifaces = interfaceinfo.getinfo()
          if ( iface in ifaces ) and ( ifaces[iface] == 'UP' ):
               return
          time.sleep(0.1)


def evaluate_packet( packets, epoch, nr_packets, filename ):
	with open(filename + ".csv", "a") as csvfile:
		w = csv.writer(csvfile, delimiter=',')

		packet_dict={}
		for packet in packets:
			packet_dict[packet[2]] = packet

		w.writerow(['timestamp', 'epoch', 'pkt-Nr', 'Delta', 'Jitter', 'rtt', 'cur_rrc', 'cur_mode', 'cur_submode', 'cur_cellid', 'cur_lac', 'cur_rssi'])

		for curr in range(nr_packets):
			try:
				prev = curr - 1
				curr_packet = packet_dict[curr]
				prev_packet = packet_dict[prev]
			except:
				# there is no pair of packets
				continue

			delta = round(float(curr_packet[0] - prev_packet[0]),3)
			jitter = round(float(delta - 1.0),3)
			timestamp = int(round(curr_packet[0]))
			rtt = round(float(curr_packet[3]),3)
			cur_rrc = curr_packet[4]
			cur_mode = curr_packet[5]
			cur_submode = curr_packet[6]
			cur_cellid = curr_packet[7]
			cur_lac = curr_packet[8]
			cur_rssi = curr_packet[9]
			
			w.writerow([timestamp, epoch, curr, delta, jitter, rtt, cur_rrc, cur_mode, cur_submode, cur_cellid, cur_lac, cur_rssi])


#client
def client( *args ):  
	finish = 0
	server_addr = args[0]
	server_port = args[1]
	iface = args[2]
	nr_packets = args[3]
	nr_probe = args[4]
	filename = args[5]

	try:
		#1. MULTI
		interfaceinfo.start()
		
		#2. pathinfo
		pathinfo.start()
		
		epoch = 1
		while( epoch <= nr_probe ):
			
			#2. Wait until iface returned by MULTI is UP
			if iface != 'eth1':
				wait_for_interface(iface)
			try: 				
				#ntp
				#subprocess.call("/etc/init.d/ntp stop", shell=True)
				#subprocess.call("pkill ntpd", shell=True)
				#subprocess.call("ntpdate ntp1.uio.no", shell=True)
				#subprocess.call("/etc/init.d/ntp start", shell=True)
				
				#UDP socket
				while True:
					try:
						socket, client_addr = set_udp_socket( iface, server_port )
						print 'UDP: %s:%d' % (client_addr, server_port) + '\n'
						break
					except:
						time.sleep(0.1)
						print >> sys.stderr, '\n', 'wait for socket'
				
				#send: ON
				print >> sys.stderr, '\n', 'CLIENT - SEND'
				sent = 0
				file = 'CLIENT-'+iface+'-'+filename+time.strftime("%m%d%H:%M")
				with open(file + ".csv", "a") as csvfile:
			        	w = csv.writer(csvfile, delimiter=',')
	        			w.writerow(['sent_time', 'received_time', 'rtt', 'epoch', 'pkt-Nr', 'cur_rrc', 'cur_mode', 'cur_submode', 'cur_cellid', 'cur_lac', 'cur_rssi'])

				sent = send_socket( socket, server_addr, server_port, iface, nr_packets, epoch, filename )
				
				#recv: ON
				#print >> sys.stderr, '\n', 'CLIENT - RECV'
				#packets = recv_socket( socket, epoch )
				
				#packet loss
				#percent_loss = packet_loss(nr_packets, rcv_packets)
				#if (f == 0):
                                #        print 'evaluation without interface issue\n'
                                #        evaluate_packet( rcv_packets, epoch, nr_packets, ('CLIENT-'+iface+'-'+filename+time.strftime("%m%d%H:%M")) )

				#socket
				unset_socket( socket )
				print >> sys.stderr, '\n', 'CLIENT - DONE'   
			except:
				e = sys.exc_info()
				for file, linenr, function, text in traceback.extract_tb(e[2]):
					error = '%s %s %s %s %s %s %s' % (file, 'line', linenr, 'in', function, '->', e[:2])
					print >> sys.stderr, error;
				
			#Poisson distribution sample: lambda
			#intv = np.random.poisson(5, 1)
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
	
	return sent 
#usage:
def usage():
	print >> sys.stderr, '\n' + str(THISFILENAME)+" [server IP] [server port] [interface] [nr. of packets (int)] [number of epoches (int)] [filename]" + '\n'
	sys.exit(0)


#CLIENT:
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
			#client
			sent_packets = client(server_addr, server_port, iface, nr_packets, nr_probe, filename)
			time.sleep(30)  # wait for inteface up after problem
			if (f == 1):
				missed_packets = nr_packets - sent_packets
                                print 'second socket\n'
				cmd  = './client-para.py %s' % server_addr + ' %s' % server_port + ' %s' % iface + ' %s' % missed_packets + ' %s' % nr_probe + ' %s' % filename
				print '%s' % cmd + '\n'
				os.system(cmd)
	else:
		usage()
		
