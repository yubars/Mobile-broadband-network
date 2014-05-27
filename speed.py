#!/usr/bin/python

import sys
import os
import csv
from math import radians, cos, sin, asin, sqrt
def usage():
        print >> sys.stderr, '\n' + str(THISFILENAME)+" [csv file]" + '\n'
        sys.exit(0)



#CLIENT:
if __name__ == '__main__':

        #SIGINT 
        #signal.signal(signal.SIGINT, signal_handler)
        if( len(sys.argv) < 3 ):
                usage()
        elif( len(sys.argv) == 3 ):
                        file = sys.argv[1]
                        file1 = sys.argv[2]
			data = []
			#data1 = []
			#data2 = []
			data5 = []
			data20 = []
			data30 = []
			datag30 = []
			datafile1 = open(file, 'r')
			readerg = csv.reader(datafile1)
			for row in readerg:
    				data.append(row)
			#rtt1 = 0.0
			#rtt2 = 0.0
			
			for d3 in data:
				
				speed = int(d3[3])
				if(speed < 6):
                                	data5.append(d3)
				elif(speed < 21):
                                	data20.append(d3)
				elif(speed < 31):
                                	data30.append(d3)
        else:
                                  datag30.append(d3)

				
			with open(file1 + "5.csv", "a") as f5:
				w5 = csv.writer(f5)
    				w5.writerows(data5)
			with open(file1 + "20.csv", "a") as f20:
				w20 = csv.writer(f20)
    				w20.writerows(data20)
			with open(file1 + "30.csv", "a") as f30:
				w30 = csv.writer(f30)
    				w30.writerows(data30)
			with open(file1 + ">30.csv", "a") as fg30:
				wg30 = csv.writer(fg30)
    				wg30.writerows(datag30)
			

        else:
                usage()
