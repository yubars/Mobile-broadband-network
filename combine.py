#!/usr/bin/python

import sys
import os
import csv
from math import radians, cos, sin, asin, sqrt
def usage():
        print >> sys.stderr, '\n' + str(THISFILENAME)+" [gps file] [ppp file] [new file]" + '\n'
        sys.exit(0)



def haversine(lon1, lat1, lon2, lat2, t1, t2):
    # convert decimal degrees to radians 
    lon1,lat1,lon2,lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 

    # 6371 km is the radius of the Earth
    kmh = (6367.0 * c * 3600.0) / (float(t2) - float(t1))
    return kmh 

#CLIENT:
if __name__ == '__main__':

        #SIGINT 
        #signal.signal(signal.SIGINT, signal_handler)
        if( len(sys.argv) < 4 ):
                usage()
        elif( len(sys.argv) == 4 ):
                        fileg = sys.argv[1]
                        filep = sys.argv[2]
			newfile = sys.argv[3]
			datag = []
			datap = []
			data = []
			data1 = []
			data10 = []
			data25 = []
			data40 = []
			datarest = []
			datafile1 = open(fileg, 'r')
			readerg = csv.reader(datafile1)
			for row in readerg:
    				datag.append(row)
			heading1 = datag.pop(0)

			datafile2 = open(filep, 'r')
			readerp = csv.reader(datafile2)
			for row1 in readerp:
    				datap.append(row1)
			heading2 = datap.pop(0)
			for d in datag:
				if(d[1] != 'nan'):
					data.append(d)
		
			for d1 in data:
				i1 = data.index(d1)
				#if(i < c):
				for d2 in datap:
					i2 = datap.index(d2)
					#print i2
					if(data[i1][0] == datap[i2][0]):
						#print 'kera'
						data1.append(data[i1]+datap[i2])
						print data[i1]+datap[i2]
						break
						
			for d3 in data1:
				del d3[4]
				d3[3] = int(round(float(d3[3]) * 3.6))
				speed = d3[3]
				if(speed < 10):
                                	data10.append(d3)
                                elif(speed >= 10 and speed < 25):
                                        data25.append(d3)
                                elif(speed >= 25 and speed < 40):
                                        data40.append(d3)
                                else:
                                        datarest.append(d3)

			#print data1
			with open(newfile + ".csv", "a") as f:
				w = csv.writer(f)
    				w.writerows(data1)

			
			with open(newfile + "speed10.csv", "a") as f10:
				w10 = csv.writer(f10)
    				w10.writerows(data10)
			with open(newfile + "speed25.csv", "a") as f25:
				w25 = csv.writer(f25)
    				w25.writerows(data25)
			with open(newfile + "speed40.csv", "a") as f40:
				w40 = csv.writer(f40)
    				w40.writerows(data40)
			with open(newfile + "speedg40.csv", "a") as frest:
				wrest = csv.writer(frest)
    				wrest.writerows(datarest)
		
        else:
                usage()
