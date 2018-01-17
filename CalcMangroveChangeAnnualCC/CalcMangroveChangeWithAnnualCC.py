
import datacube
import numpy
import argparse
import os.path
from osgeo import ogr
from osgeo import gdal
from osgeo import osr
import pandas


def calcMangNDVIMangPxlFromCube(startYear, endYear, minLat, maxLat, minLon, maxLon, mangShpMask, ccThresholds, outStatsFile, outImgMask, outImgTypeMask):

    dc = datacube.Datacube(app='CalcAnnualMangroveExtent')

    start_of_epoch = str(startYear)+'-01-01'
    end_of_epoch = str(endYear)+'-12-31'
    
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
    mangroveAreaPxlC.attrs['affine'] = affine
    mangroveAreaPxlC.attrs['crs'] = crswkt
    mangroveAreaPxlT.attrs['affine'] = affine
    mangroveAreaPxlT.attrs['crs'] = crswkt
    
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


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='CalcMangroveChangeWithAnnualFC.py', description='''Produce an annual mangrove map using the Annual Fractional Cover Product.''')

    parser.add_argument("--minlat", type=float, required=True, help='min. lat for tile region.')
    parser.add_argument("--maxlat", type=float, required=True, help='max. lat for tile region.')
    parser.add_argument("--minlon", type=float, required=True, help='min. lon for tile region.')
    parser.add_argument("--maxlon", type=float, required=True, help='max. lon for tile region.')
    parser.add_argument("--startyear", type=int, default=1987, required=False, help='Start year for the analysis.')
    parser.add_argument("--endyear", type=int, default=2016, required=False, help='End year for the analysis.')
    parser.add_argument("--ccthres1", type=int, default=12, required=False, help='First Threshold for Canopy Cover.')
    parser.add_argument("--ccthres2", type=int, default=35, required=False, help='Second Threshold for Canopy Cover.')
    parser.add_argument("--ccthres3", type=int, default=70, required=False, help='Third Threshold for Canopy Cover.')
    parser.add_argument("--outtypeimg", type=str, required=True, help='Output image file is mangrove extent in cover classes with a band for each year.')
    parser.add_argument("--outimg", type=str, required=True, help='Output image file is mangrove extent with a band for each year.')
    parser.add_argument("--outstats", type=str, required=True, help='Output stats file with pixel count for mangrove extent.')
    
    # Call the parser to parse the arguments.
    args = parser.parse_args()
    
    mangShpMask = '/g/data/r78/pjb552/GMW_Mang_Union/GMW_UnionMangroveExtent_v1.2_Australia_epsg3577.shp'
    
    calcMangNDVIMangPxlFromCube(args.startyear, args.endyear, args.minlat, args.maxlat, args.minlon, args.maxlon, mangShpMask, [args.ccthres1, args.ccthres2, args.ccthres3], args.outstats, args.outimg, args.outtypeimg)  
    