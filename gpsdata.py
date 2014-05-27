#! /usr/bin/python
import os
from gps import *
from time import *
import time
import threading
 
gpsd = None 
 
os.system('clear') 
 
class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd 
    gpsd = gps(mode=WATCH_ENABLE) 
    self.current_value = None
    self.running = True 
 
  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() 
h = 1
 
if __name__ == '__main__':
  gpsp = GpsPoller() 
  try:
    gpsp.start() 
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
        	print '\tspeed' , gpsd.fix.speed  
      	fh.write(str(int(round(time.time()))) + ',')
	fh.writelines(str(gpsd.fix.latitude) + ',')
	fh.write(str(gpsd.fix.longitude)+ ',')
	fh.write(str(gpsd.fix.speed)+ '\n')

	fh.close()
	time.sleep(1) 
 
  except (KeyboardInterrupt, SystemExit): 
    print "\nKilling Thread..."
    gpsp.running = False
    gpsp.join() 
  print "Done.\nExiting."      
  exit(0)
