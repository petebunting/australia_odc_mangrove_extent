
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


def calcMangNDVIMangPxlFromCube(minLat, maxLat, minLon, maxLon, mangShpMask, fcThreshold=30):

    dc = datacube.Datacube(app='CalcAnnualMangroveExtent')
    
    start_of_epoch = '2010-01-01'
    end_of_epoch = '2015-12-31'
    
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
    xres = annualFC.attrs['affine'][0]
    yres = annualFC.attrs['affine'][4]
    noDataVal = 0
    
    # Set the geotransform properties
    xcoord = annualFC.coords['x'].min()
    ycoord = annualFC.coords['y'].max()
    geotransform = (xcoord - (xres*0.5), xres, 0, ycoord + (yres*0.5), 0, yres)
    
    
    # Open the data source and read in the extent
    source_ds = ogr.Open(mangShpMask)
    source_layer = source_ds.GetLayer()
    source_srs = source_layer.GetSpatialRef()
    vx_min, vx_max, vy_min, vy_max = source_layer.GetExtent() # This is extent of Australia
    
    # Create the destination extent
    yt,xt = annualFC.sel(year=2010).shape
    
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
    
    mangAnnualFC = annualFC.where(gmwMaskArr == 1)
    mangAnnualFC.attrs['affine'] = affine
    mangAnnualFC.attrs['crs'] = crswkt
    
    mangroveAreaPxlC = mangAnnualFC>fcThreshold
    mangroveAreaPxlC.attrs['affine'] = affine
    mangroveAreaPxlC.attrs['crs'] = crswkt
    
    numMangPxls = numpy.sum(mangroveAreaPxlC.data)
    print(numMangPxls)
    
    
    """        
        years = [1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016]
        for yearVal in years:                
            numMangPxls = numpy.sum(mangroveAreaPxlC.sel(year=yearVal).data)
            numClMangPxls = numpy.sum(clMangroveAreaPxlC.sel(year=yearVal).data) 
            pxlCountSeries = pandas.Series([numMangPxls, numClMangPxls], index=['MangPxls', 'MangPxlsCl'])
            tileAFileOut = tileAFile+'_'+str(yearVal)+'.csv'
            pxlCountSeries.to_csv(tileAFileOut)   
            
            tileNCAMCFileOut = tileNCAMCFile+'_'+str(yearVal)+'.nc'
            tileNCCMCFileOut = tileNCCMCFile+'_'+str(yearVal)+'.nc'
            tileNCFileOut = tileNCFile+'_'+str(yearVal)+'.nc'
            
            mangroveAreaPxlC.sel(year=yearVal).to_netcdf(path=tileNCAMCFileOut, mode = 'w')
            clMangroveAreaPxlC.sel(year=yearVal).to_netcdf(path=tileNCCMCFileOut, mode = 'w')                        
            mangroveNDVIMean.sel(year=yearVal).to_netcdf(path=tileNCFileOut, mode = 'w')
    """


if __name__ == '__main__':
    """
    parser = argparse.ArgumentParser(prog='CalcMangroveChangeWithAnnualFC.py', description='''Produce an annual mangrove map using the Annual Fractional Cover Product.''')

    parser.add_argument("--minlat", type=float, required=True, help='min. lat for tile region.')
    parser.add_argument("--maxlat", type=float, required=True, help='max. lat for tile region.')
    parser.add_argument("--minlon", type=float, required=True, help='min. lon for tile region.')
    parser.add_argument("--maxlon", type=float, required=True, help='max. lon for tile region.')
    
    # Call the parser to parse the arguments.
    args = parser.parse_args()
    """
    lat_max = -17.5
    lat_min = -17.6
    lon_max = 140.8
    lon_min = 140.6
    
    mangShpMask = '/g/data/r78/pjb552/GMW_Mang_Union/GMW_UnionMangroveExtent_v1.2_Australia_epsg3577.shp'
    
    #calcMangNDVIMangPxlFromCube(args.minlat, args.maxlat, args.minlon, args.maxlon, mangShpMask)
    calcMangNDVIMangPxlFromCube(lat_min, lat_max, lon_min, lon_max, mangShpMask)


