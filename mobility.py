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
			datas = []
			datam = []
			datafile1 = open(file, 'r')
			readerg = csv.reader(datafile1)
			for row in readerg:
    				data.append(row)

			for d3 in data:
				#d3[3] = int(round(float(d3[3]) * 1.0))
				#print d3[3]
				speed = int(d3[3])
				if(speed < 3):
                                	datas.append(d3)
                                else:
                                        datam.append(d3)

			with open(file1 + "s.csv", "a") as f:
				w = csv.writer(f)
    				w.writerows(datas)

			with open(file1 + "m.csv", "a") as f10:
				w10 = csv.writer(f10)
    				w10.writerows(datam)
        else:
                usage()
