import datacube
import numpy
import argparse
import os.path
from osgeo import ogr
from osgeo import gdal
from osgeo import osr
import pandas


startYear = 2010
endYear = 2016
minLat = -17.6
maxLat = -17.5
minLon = 140.6
maxLon = 140.8 
mangShpMask = '/g/data/r78/pjb552/GMW_Mang_Union/GMW_UnionMangroveExtent_v1.2_Australia_epsg3577.shp'
ccThresholds = [12, 35, 70]
outStatsFile = '/home/552/pjb552/MangroveExtentStats.csv'
outImgMask = '/home/552/pjb552/MangroveTotalExtentImg.tif'
outImgTypeMask = '/home/552/pjb552/MangroveTypeExtentImg.tif'



dc = datacube.Datacube(app='CalcAnnualMangroveExtent')

start_of_epoch = str(startYear)+'-01-01'
end_of_epoch = str(endYear)+'-12-31'

query = {'time': (start_of_epoch, end_of_epoch),}
query['x'] = (minLon, maxLon)
query['y'] = (maxLat, minLat)
query['crs'] = 'EPSG:4326'

annualFC = dc.load(product='fc_percentile_albers_annual', group_by='solar_day', measurements=['PV_PC_10'], **query)

annualWOFS = dc.load(product='wofs_annual_summary_temp', measurements=['frequency'], group_by='solar_day', **query)

crswkt = annualFC.crs.wkt
affine = annualFC.affine

annualPV10th = annualFC.PV_PC_10
annualWetFreq = annualWOFS.frequency

time_sorted = annualPV10th.time.argsort()
annualPV10th = annualPV10th.isel(time=time_sorted)
annualPV10th.attrs['affine'] = affine
annualPV10th.attrs['crs'] = crswkt

time_sorted = annualWetFreq.time.argsort()
annualWetFreq = annualWetFreq.isel(time=time_sorted)
annualWetFreq.attrs['affine'] = affine
annualWetFreq.attrs['crs'] = crswkt

# Define pixel size and NoData value of new raster
xres = affine[0]
yres = affine[4]
noDataVal = 0

# Set the geotransform properties
xcoord = annualFC.coords['x'].min()
ycoord = annualFC.coords['y'].max()
geotransform = (xcoord - (xres*0.5), xres, 0, ycoord + (yres*0.5), 0, yres)

# Open the data source and read in the extent
source_ds = ogr.Open(mangShpMask)
source_layer = source_ds.GetLayer()
source_srs = source_layer.GetSpatialRef()

# Create the destination extent
yt,xt = annualPV10th[0].shape

# Set up 'in-memory' gdal image to rasterise the shapefile too
target_ds = gdal.GetDriverByName('MEM').Create('', xt, yt, gdal.GDT_Byte)
target_ds.SetGeoTransform(geotransform)
albers = osr.SpatialReference()
albers.ImportFromEPSG(3577)
target_ds.SetProjection(albers.ExportToWkt())
band = target_ds.GetRasterBand(1)
band.SetNoDataValue(noDataVal)

# Rasterise
gdal.RasterizeLayer(target_ds, [1], source_layer, burn_values=[1])

# Read as array the GMW mask
gmwMaskArr = band.ReadAsArray()

annualPV10th = annualPV10th.where(annualWetFreq<0.7)
annualPV10th.data[numpy.isnan(annualPV10th.data)] = 0

mangAnnualFC = annualPV10th.where(gmwMaskArr == 1)
mangAnnualFC.data[numpy.isnan(mangAnnualFC.data)] = 0
mangAnnualFC.attrs['affine'] = affine
mangAnnualFC.attrs['crs'] = crswkt


years = numpy.arange(startYear, endYear+1, 1)
if len(years) != annualPV10th.shape[0]:
    raise Exception("The list of years specified is not equal to the number of annual layers within the datacube dataset read.")


mangroveAreaPxlT = mangAnnualFC > ccThresholds[0]
mangroveAreaPxlC = mangAnnualFC.copy(True)
numThresVals = len(ccThresholds)
for i in range(len(years)):
    mangroveAreaPxlC.data[i] = 0
    for j in range(numThresVals):
        mangroveAreaPxlC.data[i][mangAnnualFC.data[i] > ccThresholds[j]] = j+1


albers = osr.SpatialReference()
albers.ImportFromEPSG(3577)

targetImgDS = gdal.GetDriverByName('GTIFF').Create(outImgMask, xt, yt, len(years), gdal.GDT_Byte, options=["TILED=YES", "COMPRESS=DEFLATE"])
targetImgDS.SetGeoTransform(geotransform)
targetImgDS.SetProjection(albers.ExportToWkt())

targetTypeImgDS = gdal.GetDriverByName('GTIFF').Create(outImgTypeMask, xt, yt, len(years), gdal.GDT_Byte, options=["TILED=YES", "COMPRESS=DEFLATE"])
targetTypeImgDS.SetGeoTransform(geotransform)
targetTypeImgDS.SetProjection(albers.ExportToWkt())

f = open(outStatsFile, 'w')
f.write('Year, TotalPxlCount')
for i in range(numThresVals):
    f.write(', PxlCountThres'+str(i+1))
f.write('\n')

idx = 0
for yearVal in years:
    pxlCount = numpy.sum(mangroveAreaPxlT.data[idx])
    f.write(str(yearVal)+', '+str(pxlCount))
    for i in range(numThresVals):
        pxlCount = numpy.sum((mangroveAreaPxlC.data[idx] == i+1))
        f.write(', ' + str(pxlCount))
    f.write('\n')
    
    # Export the Total Mangrove Area image
    band = targetImgDS.GetRasterBand(idx+1)
    band.SetNoDataValue(noDataVal)
    band.WriteArray(mangroveAreaPxlT.data[idx])
    band.SetDescription(str(yearVal))
    
    # Export Mangrove Cover Type Area Image
    band = targetTypeImgDS.GetRasterBand(idx+1)
    band.SetNoDataValue(noDataVal)
    band.WriteArray(mangroveAreaPxlC.data[idx])
    band.SetDescription(str(yearVal))
    
    idx = idx + 1
f.write('\n')
f.flush()
f.close()

targetImgDS = None
targetTypeImgDS = None


