import argparse
import os.path
import shutil

import rsgislib
import rsgislib.vectorutils

import osgeo.gdal as gdal

import pandas
import numpy
import matplotlib.pyplot as plt

def createPlots(dataFile, tilesOfInterest, outTypePlotFile, baseTitle):
    
    data = pandas.read_pickle(dataFile, compression="gzip")
    
    outData = data[tilesOfInterest[0]][['total','low','mid','high']]
    if len(tilesOfInterest) > 1:
        for tile in tilesOfInterest[1:]:
            outData = outData + data[tile][['total','low','mid','high']]
            
    outData = (outData * 625) / 1000000
    
    ax=outData[['low','mid','high']].plot.bar(stacked=True, figsize=(10,7), color=['#9FFF4C', '#5ECC00', '#3B7F00'], legend=False, width=1.0)
    ax.set_xlabel('Time (Years)')
    ax.set_ylabel('Area (km$^{2}$)')
    ax.set_title(baseTitle)
    plt.savefig(outTypePlotFile)


def GenZoneMangroveChangePlots(zonesSHP, zoneNameCol, plotPathDIR, dataFile, gridSHP, gridIDCol, tmpPath):
    rsgisUtils = rsgislib.RSGISPyUtils()
    uidStr = rsgisUtils.uidGenerator()
    tmpDIR = os.path.join(tmpPath, uidStr)
    
    tmpPresent = True
    if not os.path.exists(tmpDIR):
        os.makedirs(tmpDIR)
        tmpPresent = False 

    ############ DO STUFF ###############
        
    zonesDataSet = gdal.OpenEx(zonesSHP, gdal.OF_VECTOR )
    if zonesDataSet is None:
        raise("Failed to open input zones shapefile\n") 
    zonesLyr = zonesDataSet.GetLayer()
    zonesSpatRef = zonesLyr.GetSpatialRef()
    zonesSpatRef.AutoIdentifyEPSG()
    epsgCodeZones = zonesSpatRef.GetAuthorityCode(None)
    print(zonesSpatRef.ExportToWkt())
    
    gridDataSet = gdal.OpenEx(gridSHP, gdal.OF_VECTOR )
    if gridDataSet is None:
        raise("Failed to open input grid shapefile\n") 
    gridLyr = gridDataSet.GetLayer()
    gridSpatRef = gridLyr.GetSpatialRef()
    gridSpatRef.AutoIdentifyEPSG()
    epsgCodeGrid = gridSpatRef.GetAuthorityCode(None)
    print(gridSpatRef.ExportToWkt())
    
    if epsgCodeZones is not epsgCodeGrid:
        print('Reprojecting zones shapefile')
        zonesDataSet = None
        shpBasename = os.path.splitext(os.path.basename(zonesSHP))[0]
        tmpReprojSHP = os.path.join(tmpDIR, shpBasename+'_reproj.shp')
        rsgislib.vectorutils.reProjVectorLayer(zonesSHP, tmpReprojSHP, gridSpatRef.ExportToWkt())
        
        origZonesSHP = zonesSHP
        zonesSHP = tmpReprojSHP
        
        zonesDataSet = gdal.OpenEx(zonesSHP, gdal.OF_VECTOR )
        if zonesDataSet is None:
            raise("Failed to open input zones shapefile\n") 
        zonesLyr = zonesDataSet.GetLayer()
        zonesSpatRef = zonesLyr.GetSpatialRef()
        zonesSpatRef.AutoIdentifyEPSG()
        epsgCodeZones = zonesSpatRef.GetAuthorityCode(None)
    
    print('epsgCodeZones ', epsgCodeZones)
    print('epsgCodeGrid ', epsgCodeGrid)
    
    zonesFeat = zonesLyr.GetNextFeature()
    while zonesFeat:
        zoneGeom = zonesFeat.GetGeometryRef()
        if zoneGeom is not None:
            gridLyr.SetSpatialFilter(zoneGeom)
            gridIDs = []
            for gridFeat in gridLyr:
                gridIDs.append(int(gridFeat.GetField(gridIDCol)))
            print(gridIDs)
            
            zoneName = zonesFeat.GetField(zoneNameCol)
            print(zoneName)
            zoneNameNoSpace = zoneName.replace(' ', '_')
            outTypePlotFile = os.path.join(plotPathDIR, zoneNameNoSpace+'_totalAreaType.pdf')
            createPlots(dataFile, gridIDs, outTypePlotFile, zoneName)
            
        zonesFeat = zonesLyr.GetNextFeature()
        
    zonesDataSet = None
    gridDataSet = None
    
    ####################################
    
    if not tmpPresent:
        shutil.rmtree(tmpDIR, ignore_errors=True)
    
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='CalcMangroveChangeWithAnnualFC.py', description='''Produce an annual mangrove map using the Annual Fractional Cover Product.''')

    parser.add_argument("--zones", type=str, required=True, help='Shapefile defining zones of interest')
    parser.add_argument("--zonename", type=str, required=True, help='The column in the zones shapefile specifying the base name for the output plots.')
    parser.add_argument("--plotpath", type=str, required=True, help='Output directory where plots will be saved.')
    parser.add_argument("--data", type=str, required=True, help='File name and path picked pandas data.')
    parser.add_argument("--grid", type=str, required=True, help='File name and path for shapefile grid.')
    parser.add_argument("--gridid", type=str, required=True, help='The column in the grid shapefile specifying the Grid ID.')
    parser.add_argument("--tmp", type=str, required=True, help='Temp path where files can be written.')
    
    
    # Call the parser to parse the arguments.
    args = parser.parse_args()
        
    GenZoneMangroveChangePlots(args.zones, args.zonename, args.plotpath, args.data, args.grid, args.gridid, args.tmp)  
