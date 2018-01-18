import pandas
import numpy
import matplotlib.pyplot as plt


tilesOfInterest = [970, 971, 972, 1211, 1212, 1213]#[1657]#[664, 665, 666, 668, 670, 901, 902]#[2044, 2045, 2046, 2047, 2048, 1795, 1796, 1797, 1798, 1550, 1551, 1552]

outTotalPlotFile = 'MangTotalAreaPlot.pdf'
outTypePlotFile = 'MangTypeAreaPlot.pdf'

data = pandas.read_pickle("MangChangePVFC_V2_1987_to_2016.pkl.gz", compression="gzip")

outData = data[tilesOfInterest[0]][['total','low','mid','high']]
if len(tilesOfInterest) > 1:
    for tile in tilesOfInterest[1:]:
        outData = outData + data[tile][['total','low','mid','high']]

ax=outData['total'].plot(x=outData.index, y=outData['total'], legend=False)
ax.set_ylim(0, outData['total'].values.max()*1.1)
plt.savefig(outTotalPlotFile)

outData[['low','mid','high']].plot.bar(stacked=True, figsize=(10,7), color=['#9FFF4C', '#5ECC00', '#3B7F00'], legend=False, width=1.0)
plt.savefig(outTypePlotFile)