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

        #SIGINT 
        #signal.signal(signal.SIGINT, signal_handler)
        if( len(sys.argv) < 2 ):
                usage()
        elif( len(sys.argv) == 2 ):
                        file = sys.argv[1]
			data = []
			datafile1 = open(file, 'r')
			readerg = csv.reader(datafile1)
			for row in readerg:
    				data.append(row)
			heading1 = data.pop(0)
			mode_c = 0
			mode_cn = 0
			mode = 0
			submode_c = 0
			submode_cn = 0
			submode = 0
			lac_c = 0
			lac_cn = 0
			lac = 0
			cell_c = 0
			cell_cn = 0
			cell = 0
			other_c = 0
			other = 0

			for d1 in data:
				i1 = data.index(d1)
				last = len(data)
				if (i1 < last-1):
					if((int(data[i1+1][4]) - int(data[i1][4])) > 1):
						if(data[i1][6] != data[i1+1][6]):
							mode_c += 1
							mode += (int(data[i1+1][4]) - int(data[i1][4]) -1)
						elif(data[i1][7] != data[i1+1][7]):
							submode_c += 1
							submode += (int(data[i1+1][4]) - int(data[i1][4])-1)
						elif(data[i1][9] != data[i1+1][9]):
                                                        lac_c += 1
                                                        lac += (int(data[i1+1][4]) - int(data[i1][4])-1)
						elif(data[i1][8] != data[i1+1][8]):
                                                        cell_c += 1
                                                        cell += (int(data[i1+1][4]) - int(data[i1][4])-1)
						else:
							other_c += 1
							other += (int(data[i1+1][4]) - int(data[i1][4])-1)			
					if(data[i1][6] != data[i1+1][6]):
                                        	mode_cn += 1
                                        if(data[i1][7] != data[i1+1][7]):
                                                submode_cn += 1
                                        if(data[i1][9] != data[i1+1][9]):
                                                lac_cn += 1
                                        if(data[i1][8] != data[i1+1][8]):
                                                cell_cn += 1
			total = mode+submode+lac+cell+other
			sent = int(data[last-1][4]) - int(data[0][4]) +1
			print mode_c
			print mode_cn
			print submode_c
			print submode_cn
			print lac_c
			print lac_cn
			print cell_c
			print cell_cn
			print other_c
			print mode
			print submode
			print lac
			print cell
			print other
			print total
			print sent
			print last



        else:
                usage()
