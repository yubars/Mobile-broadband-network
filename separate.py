#!/usr/bin/python

import sys
import os
import csv
from math import radians, cos, sin, asin, sqrt
def usage():
        print >> sys.stderr, '\n' + str(THISFILENAME)+" [gps file] [ppp file] [new file]" + '\n'
        sys.exit(0)



#CLIENT:
if __name__ == '__main__':

        if( len(sys.argv) < 3 ):
                usage()
        elif( len(sys.argv) == 3 ):
                        file = sys.argv[1]
			newfile = sys.argv[2]
			data2 = []
			data3 = []
			datag = []
			dataplus = []
			datadu = []
			datad = []
			datau = []
			dataw = []

			datafile1 = open(file, 'r')
			readerg = csv.reader(datafile1)
			for row in readerg:
    				datag.append(row)

			for d in datag:
				if(d[6] == 'DCH' || d[6] == 'FACH'):
					data3.append(d)
				else:
					data2.append(d)

			for d1 in data3:
				if(d[7] == 'HSPA+'):
                                        dataplus.append(d1)
                                elif(d[7] == 'HSDPA+HSUPA'):
                                        datadu.append(d1)
				elif(d[7] == 'HSDPA'):
                                        datad.append(d1)
				elif(d[7] == 'HSUPA'):
                                        datau.append(d1)
				else:
					dataw.append(d1)


			with open(newfile + ".csv", "a") as f2:
				w2 = csv.writer(f2)
    				w2.writerows(data2)
			with open(newfile + ".csv", "a") as f3:
				w3 = csv.writer(f3)
    				w3.writerows(data3)
			with open(newfile + ".csv", "a") as fplus:
				wplus = csv.writer(fplus)
    				wplus.writerows(dataplus)
			with open(newfile + ".csv", "a") as fdu:
				wdu = csv.writer(fdu)
    				wdu.writerows(datadu)
			with open(newfile + ".csv", "a") as fd:
				wd = csv.writer(fd)
    				wd.writerows(datad)
			with open(newfile + ".csv", "a") as fu:
				wu = csv.writer(fu)
    				wu.writerows(datau)
			with open(newfile + ".csv", "a") as fw:
				ww = csv.writer(fw)
    				ww.writerows(dataw)



        else:
                usage()
