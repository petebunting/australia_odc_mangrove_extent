import pandas
import numpy
import glob
import os.path

def readVals(statsFile, nLinesVals):
    outTotalVals = numpy.zeros((nLinesVals), dtype=int)
    outLowVals = numpy.zeros((nLinesVals), dtype=int)
    outMidVals = numpy.zeros((nLinesVals), dtype=int)
    outHighVals = numpy.zeros((nLinesVals), dtype=int)
    
    lineN = 0
    dataFile = open(statsFile, 'r')
    for line in dataFile:
        line = line.strip()
        if (lineN > 0) and (line is not ""):
            splitVals = line.split(',')
            if len(splitVals)-1 != 4:
                raise Exception("The number of values on the line is too few.")
            
            outTotalVals[lineN-1] = int(splitVals[1])
            outLowVals[lineN-1] = int(splitVals[2])
            outMidVals[lineN-1] = int(splitVals[3])
            outHighVals[lineN-1] = int(splitVals[4])

        lineN = lineN + 1
    
    return outTotalVals, outLowVals, outMidVals, outHighVals

years = ['1987', '1988', '1989', '1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016']

nBoxs = 2379
nYears = len(years)

dataVals = numpy.zeros((nYears, nBoxs*4), dtype=int)

statsFiles = glob.glob('./stats/*.csv')

for statFile in statsFiles:
    print(statFile)
    baseName = os.path.splitext(os.path.basename(statFile))[0]
    print(baseName)
    gridID = int(baseName.split('_')[-1])
    print(gridID)
    sIdx = (gridID-1)*4
    print(sIdx)
    outTotalVals, outLowVals, outMidVals, outHighVals = readVals(statFile, nYears)
    dataVals[..., sIdx] = outTotalVals
    dataVals[..., sIdx+1] = outLowVals
    dataVals[..., sIdx+2] = outMidVals
    dataVals[..., sIdx+3] = outHighVals
    

    
dfIdx = pandas.MultiIndex.from_product([numpy.arange(1,nBoxs+1, 1), ['total', 'low', 'mid', 'high']], names=['GridID', 'PxlCount'])

dataValsFrame = pandas.DataFrame(dataVals, index=years, columns=dfIdx)
print(dataValsFrame)


dataValsFrame.to_csv('MangChangePVFC_V2.1_1987_to_2016.csv')
dataValsFrame.to_pickle("MangChangePVFC_V2.1_1987_to_2016.pkl.gz", compression="gzip")

