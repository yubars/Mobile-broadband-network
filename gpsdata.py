#! /usr/bin/python
# Written by Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0
 
import os
from gps import *
from time import *
import time
import threading
 
gpsd = None #seting the global variable
 
os.system('clear') #clear the terminal (optional)
 
class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true
 
  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
h = 1
 
if __name__ == '__main__':
  gpsp = GpsPoller() # create the thread
  try:
    gpsp.start() # start it up
    filename = "gps" + time.strftime("%m%d%H:%M") + ".csv"
    while True:
	fh = open(filename,"a")
	if h <= 5:	
      #It may take a second or two to get good data
		print 'writing data to file......'
		fh.write('timestamp,')
		fh.writelines('latitude,')
		fh.write('longitude,')
		fh.write('speed\n')
		h += 1
		print '\ttimestamp:' , int(round(time.time()))  
		print '\tlatitude:' , gpsd.fix.latitude
        	print '\tlongitude:' , gpsd.fix.longitude
        	print '\tspeed' , gpsd.fix.speed  #,' + ', gpsd.fix.time
      #print 'altitude (m)\n' , gpsd.fix.altitude
	fh.write(str(int(round(time.time()))) + ',')
	fh.writelines(str(gpsd.fix.latitude) + ',')
	fh.write(str(gpsd.fix.longitude)+ ',')
	fh.write(str(gpsd.fix.speed)+ '\n')
#	fh.write(str(gpsd.fix.altitude)+'\n')
	
	fh.close()
#        print 'eps         ' , gpsd.fix.eps
 #       print 'epx         ' , gpsd.fix.epx
  #      print 'epv         ' , gpsd.fix.epv
   #     print 'ept         ' , gpsd.fix.ept
    #    print 'speed (m/s) ' , gpsd.fix.speed
     #   print 'climb       ' , gpsd.fix.climb
      #  print 'track       ' , gpsd.fix.track
       # print 'mode        ' , gpsd.fix.mode
        #print
        #print 'sats        ' , gpsd.satellites
 
        time.sleep(1) #set to whatever
 
  except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print "\nKilling Thread..."
    gpsp.running = False
    gpsp.join() # wait for the thread to finish what it's doing
  print "Done.\nExiting."      
  exit(0)
