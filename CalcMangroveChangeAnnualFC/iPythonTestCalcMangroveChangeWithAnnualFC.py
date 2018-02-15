import datacube
import numpy
from osgeo import ogr
from osgeo import gdal
from osgeo import osr


dc = datacube.Datacube(app='CalcAnnualMangroveExtent')

start_of_epoch = '2010-01-01'
end_of_epoch = '2015-12-31'

maxLat = -17.5
minLat = -17.6
maxLon = 140.8
minLon = 140.6

query = {'time': (start_of_epoch, end_of_epoch),}
query['x'] = (minLon, maxLon)
query['y'] = (maxLat, minLat)
query['crs'] = 'EPSG:4326'

annualFC = dc.load(product='fc_percentile_albers_annual', group_by='solar_day', measurements=['PV_PC_10'], **query)


crswkt = annualFC.crs.wkt
affine = annualFC.affine

annualPV10th = annualFC.PV_PC_10

time_sorted = annualPV10th.time.argsort()
annualPV10th = annualPV10th.isel(time=time_sorted)
annualPV10th.attrs['affine'] = affine
annualPV10th.attrs['crs'] = crswkt


# Define pixel size and NoData value of new raster
xres = affine[0]
yres = affine[4]
noDataVal = 0

# Set the geotransform properties
xcoord = annualFC.coords['x'].min()
ycoord = annualFC.coords['y'].max()
geotransform = (xcoord - (xres*0.5), xres, 0, ycoord + (yres*0.5), 0, yres)

mangShpMask = '/g/data/r78/pjb552/GMW_Mang_Union/GMW_UnionMangroveExtent_v1.2_Australia_epsg3577.shp'
# Open the data source and read in the extent
source_ds = ogr.Open(mangShpMask)
source_layer = source_ds.GetLayer()
source_srs = source_layer.GetSpatialRef()

# Create the destination extent
yt,xt = annualFC.PV_PC_10[0].shape

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

mangAnnualFC = annualPV10th.where(gmwMaskArr == 1)
mangAnnualFC.data[numpy.isnan(mangAnnualFC.data)] = 0
mangAnnualFC.attrs['affine'] = affine
mangAnnualFC.attrs['crs'] = crswkt

fcThreshold = 40

mangroveAreaPxlC = mangAnnualFC > fcThreshold
mangroveAreaPxlC.attrs['affine'] = affine
mangroveAreaPxlC.attrs['crs'] = crswkt

numMangPxls = numpy.sum(mangroveAreaPxlC.data[0])
print(numMangPxls)