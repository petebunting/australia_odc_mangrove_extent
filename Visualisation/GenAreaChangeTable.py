import pandas
import numpy
import matplotlib.pyplot as plt


tilesOfInterest = numpy.arange(1, 2380, 1)

#outCSVFile = 'MangroveChangeStats_v3.csv'
outCSVFile = 'AustraliaMangroveChangeStats_v3.csv'

data = pandas.read_pickle("MangChangePVFC_V3.0_1987_to_2016.pkl.gz", compression="gzip")

outData = data[tilesOfInterest[0]][['total','low','mid','high']]
if len(tilesOfInterest) > 1:
    for tile in tilesOfInterest[1:]:
        outData = outData + data[tile][['total','low','mid','high']]

outData = (outData * 625) / 1000000

outData.to_csv(outCSVFile)
