import rasterio
import rasterio.features
import datacube
import numpy
from datacube.storage import masking
import xarray
import argparse
import os.path
from osgeo import ogr
from osgeo import gdal
from osgeo import osr
import pandas

def pq_fuser(dest, src):
    valid_bit = 8
    valid_val = (1 << valid_bit)

    no_data_dest_mask = ~(dest & valid_val).astype(bool)
    numpy.copyto(dest, src, where=no_data_dest_mask)

    both_data_mask = (valid_val & dest & src).astype(bool)
    numpy.copyto(dest, src & dest, where=both_data_mask)


minLon = 144.3
maxLon = 144.4
maxLat = -38.0
minLat = -38.1

mangShpExt = '/g/data/r78/pjb552/gmwExtent/GMW_Australia_MangroveExtent2010_AlbersEA_shp.shp'
ndviThresLow = 0.4
ndviThresHigh = 0.6

dc = datacube.Datacube(app='CalcAnnualMangroveExtent')
    
#Define wavelengths/bands of interest, remove this kwarg to retrieve all bands
bands_of_interest = ['red', 'nir']

#Define sensors of interest
sensors = ['ls8', 'ls7', 'ls5']

#define temporal range
start_of_epoch = '1987-01-01'
# latest observation
end_of_epoch = '2016-12-31'

query = {'time': (start_of_epoch, end_of_epoch),}
query['x'] = (minLon, maxLon)
query['y'] = (maxLat, minLat)
query['crs'] = 'EPSG:4326'

#Define which pixel quality artefacts you want removed from the results
mask_components = {'cloud_acca':          'no_cloud',
                   'cloud_shadow_acca' :  'no_cloud_shadow',
                   'cloud_shadow_fmask' : 'no_cloud_shadow',
                   'cloud_fmask' :        'no_cloud',
                   'blue_saturated' :     False,
                   'green_saturated' :    False,
                   'red_saturated' :      False,
                   'nir_saturated' :      False,
                   'swir1_saturated' :    False,
                   'swir2_saturated' :    False,
                   'contiguous' :         True }

print("Read pixel image data into memory.")
sensor_clean = {}
for sensor in sensors:
    print(sensor)
    #Load the NBAR and corresponding PQ
    sensor_nbar = dc.load(product= sensor+'_nbar_albers', group_by='solar_day', measurements = bands_of_interest, **query)
    if bool(sensor_nbar):
        sensor_pq = dc.load(product=sensor+'_pq_albers', group_by='solar_day', fuse_func=pq_fuser, **query)
        #grab the projection info before masking/sorting
        crs = sensor_nbar.crs
        crswkt = sensor_nbar.crs.wkt
        affine = sensor_nbar.affine
        #this line is to make sure there's PQ to go with the NBAR
        sensor_nbar = sensor_nbar.sel(time = sensor_pq.time)
        #Apply the PQ masks to the NBAR
        cloud_free = masking.make_mask(sensor_pq, **mask_components)
        good_data = cloud_free.pixelquality.loc[start_of_epoch:end_of_epoch]
        sensor_nbar = sensor_nbar.where(good_data)
        sensor_clean[sensor] = sensor_nbar

if bool(sensor_clean):
    #Concatenate data from different sensors together and sort so that observations are sorted by time rather than sensor
    print("Merge data from different sensors.")
    nbar_clean = xarray.concat(sensor_clean.values(), dim='time')
    time_sorted = nbar_clean.time.argsort()
    nbar_clean = nbar_clean.isel(time=time_sorted)
    nbar_clean.attrs['affine'] = affine
    nbar_clean.attrs['crs'] = crswkt
    
    print("\'Clean\' up the Red and NIR bands to remove any values less than zero.")
    nbar_clean['red'] = nbar_clean.red.where(nbar_clean.red>0)
    nbar_clean['nir'] = nbar_clean.nir.where(nbar_clean.nir>0)
    
    print("Calculate NDVI.")
    ndvi = ((nbar_clean.nir-nbar_clean.red)/(nbar_clean.nir+nbar_clean.red))
    ndvi.attrs['affine'] = affine
    ndvi.attrs['crs'] = crswkt
    
    print("Create Composite")
    ndviAnnual = ndvi.groupby('time.year')
    ndviMean = ndviAnnual.mean(dim = 'time')
    ndviMean.attrs['affine'] = affine
    ndviMean.attrs['crs'] = crswkt
    
    print("Rasterise the GMW extent map for the area of interest.")
    # Define pixel size and NoData value of new raster
    xres = nbar_clean.attrs['affine'][0]
    yres = nbar_clean.attrs['affine'][4]
    noDataVal = -9999
    
    # set the geotransform properties
    xcoord = ndviMean.coords['x'].min()
    ycoord = ndviMean.coords['y'].max()
    geotransform = (xcoord - (xres*0.5), xres, 0, ycoord + (yres*0.5), 0, yres)
    
    # Open the data source and read in the extent
    source_ds = ogr.Open(mangShpExt)
    source_layer = source_ds.GetLayer()
    source_srs = source_layer.GetSpatialRef()
    vx_min, vx_max, vy_min, vy_max = source_layer.GetExtent() # this is extent of Australia
    
    # Create the destination extent
    yt,xt = ndviMean.sel(year=2010).shape
        
    # set up mask image including projection
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
    
    print("Apply the GMW Mask to the NDVI values")
    mangroveNDVIMean = ndviMean.where(gmwMaskArr == 1)
    
    print("Apply thresholds to NDVI to find total mangrove area (in pixels) and closed canopy mangrove area.")
    mangroveAreaPxlC = mangroveNDVIMean>ndviThresLow
    clMangroveAreaPxlC = mangroveNDVIMean>ndviThresHigh
    
    mangroveAreaPxlC.attrs['affine'] = affine
    mangroveAreaPxlC.attrs['crs'] = crswkt
    clMangroveAreaPxlC.attrs['affine'] = affine
    clMangroveAreaPxlC.attrs['crs'] = crswkt
    mangroveNDVIMean.attrs['affine'] = affine
    mangroveNDVIMean.attrs['crs'] = crswkt
    
    years = [1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016]
    for yearVal in years:    
        tileAFile = 'MangAreas_'+str(yearVal)+'.csv'
        
        numMangPxls = numpy.sum(mangroveAreaPxlC.sel(year=yearVal).data)
        numClMangPxls = numpy.sum(clMangroveAreaPxlC.sel(year=yearVal).data) 
        pxlCountSeries = pandas.Series([numMangPxls, numClMangPxls], index=['MangPxls', 'MangPxlsCl'])
        pxlCountSeries.to_csv(tileAFile)   
        
        tileNCAMCFile = 'MangAreaLowThres_'+str(yearVal)+'.nc'
        tileNCCMCFile = 'MangAreaHighThres_'+str(yearVal)+'.nc'
        tileNCFile = 'ndvi_'+str(yearVal)+'.nc'
        
        mangroveAreaPxlC.sel(year=yearVal).to_netcdf(path = tileNCAMCFile, mode = 'w')
        clMangroveAreaPxlC.sel(year=yearVal).to_netcdf(path = tileNCCMCFile, mode = 'w')                        
        mangroveNDVIMean.sel(year=yearVal).to_netcdf(path = tileNCFile, mode = 'w')




