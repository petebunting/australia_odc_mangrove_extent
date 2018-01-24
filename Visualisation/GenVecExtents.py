
import rsgislib
import rsgislib.vectorutils

import os
import os.path
import glob
import numpy

inFiles = glob.glob('/Users/pete/Temp/AustralianMangroves/MangChangePVFC_V3/totalimgs/*.tif')

outDIRBase = '/Users/pete/Temp/AustralianMangroves/MangChangePVFC_V3/vectortiles'

years = numpy.arange(1987, 2017, 1)
for year in years:
    yearDIR = os.path.join(outDIRBase, str(year))
    if not os.path.exists(yearDIR):
        os.makedirs(yearDIR)

for inImg in inFiles:
    print(inImg)
    baseName = os.path.splitext(os.path.basename(inImg))[0]
    imgBand = 1
    for year in years:
        yearDIR = os.path.join(outDIRBase, str(year))
        outSHP = os.path.join(yearDIR, baseName+'_'+str(year)+'.shp')
        rsgislib.vectorutils.polygoniseRaster(inImg, outSHP, imgBandNo=imgBand, maskImg=inImg, imgMaskBandNo=imgBand)
        imgBand = imgBand + 1        


outDBFile = '/Users/pete/Temp/AustralianMangroves/MangChangePVFC_V3/AustraliaMangroveChange_v3.0.sqlite'
fileExists = False
for year in years:
    yearDIR = os.path.join(outDIRBase, str(year))
    lyrName = 'Mangroves_'+str(year)
    inFileList = glob.glob(os.path.join(yearDIR, '*.shp'))
    rsgislib.vectorutils.mergeVectors2SQLiteDB(inFileList, outDBFile, lyrName, fileExists)
    fileExists = True
    
