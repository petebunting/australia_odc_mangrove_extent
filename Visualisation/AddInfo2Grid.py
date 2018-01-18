import pandas
import numpy
import os.path
import osgeo.gdal as gdal
import osgeo.ogr as ogr


def calcStats(data, gridID):
    maxDiff = 0
    maxDiffYear = 0
    for i in range(data[gridID][['total']].index.shape[0]):
        if i == 1:
            maxDiff = abs(data[gridID][['total']].values[i][0] - data[gridID][['total']].values[i-1][0])
            maxDiffYear = int(data[gridID][['total']].index[i])
        elif i > 1:
            diff = abs(data[gridID][['total']].values[i][0] - data[gridID][['total']].values[i-1][0])
            if diff > maxDiff:
                maxDiff = diff
                maxDiffYear = int(data[gridID][['total']].index[i])
    
    StdTotalVal = data[gridID, 'total'].std()/data[gridID, 'total'].mean()
    MaxStdTotVal = numpy.max([data[gridID, 'low'].std(), data[gridID, 'mid'].std(), data[gridID, 'high'].std()])/data[gridID, 'total'].mean()
    MangAreaVal = data[gridID, 'total'].mean()
    diff8716AreaVal = data[gridID, 'total']['2016'] - data[gridID, 'total']['1987']
    diff1216AreaVal = data[gridID, 'total']['2016'] - data[gridID, 'total']['2012']
    return maxDiffYear, StdTotalVal, MaxStdTotVal, MangAreaVal, diff8716AreaVal, diff1216AreaVal



gridSHP = '/Users/pete/Temp/AustralianMangroves/AustraliaSqGrid_MangroveRegionsV1.shp'
outGridSHP = '/Users/pete/Temp/AustralianMangroves/AustraliaSqGrid_MangroveRegionsV1_ExtraV2Info.shp'

data = pandas.read_pickle("MangChangePVFC_V2_1987_to_2016.pkl.gz", compression="gzip")

inDataSet = gdal.OpenEx(gridSHP, gdal.OF_VECTOR )
if inDataSet is None:
    raise("Failed to open input shapefile\n") 
inLayer = inDataSet.GetLayer()

# Create shapefile driver
driver = gdal.GetDriverByName( "ESRI Shapefile" )

# create the output layer
if os.path.exists(outGridSHP):
    raise Exception('Output shapefile already exists - stopping.')
outDataSet = driver.Create(outGridSHP, 0, 0, 0, gdal.GDT_Unknown )

outLyrName = os.path.splitext(os.path.basename(outGridSHP))[0]
outLayer = outDataSet.CreateLayer(outLyrName, inLayer.GetSpatialRef(), inLayer.GetGeomType() )

inLayerDefn = inLayer.GetLayerDefn()
for i in range(0, inLayerDefn.GetFieldCount()):
    fieldDefn = inLayerDefn.GetFieldDefn(i)
    outLayer.CreateField(fieldDefn)

yearMaxField = ogr.FieldDefn("YearMax", ogr.OFTInteger)
outLayer.CreateField(yearMaxField)
stdTotalField = ogr.FieldDefn("StdTotal", ogr.OFTReal)
outLayer.CreateField(stdTotalField)
maxStdTotalField = ogr.FieldDefn("MaxStdTot", ogr.OFTReal)
outLayer.CreateField(maxStdTotalField)
meanAreaField = ogr.FieldDefn("MangArea", ogr.OFTInteger)
outLayer.CreateField(meanAreaField)
diff8716AreaField = ogr.FieldDefn("d8716Area", ogr.OFTInteger)
outLayer.CreateField(diff8716AreaField)
diff1216AreaField = ogr.FieldDefn("d1216Area", ogr.OFTInteger)
outLayer.CreateField(diff1216AreaField)

outLayerDefn = outLayer.GetLayerDefn()

# loop through the input features
inFeature = inLayer.GetNextFeature()
while inFeature:
    geom = inFeature.GetGeometryRef()
    if geom is not None:
        gridID = inFeature.GetField('GridID')
        print(gridID)
        outFeature = ogr.Feature(outLayerDefn)
        outFeature.SetGeometry(geom)
        for i in range(0, inLayerDefn.GetFieldCount()):
            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
        
        YearMaxVal, StdTotalVal, MaxStdTotVal, MangAreaVal, diff8716AreaVal, diff1216AreaVal = calcStats(data, gridID)
        
        outFeature.SetField("YearMax", YearMaxVal)
        outFeature.SetField("StdTotal", StdTotalVal)
        outFeature.SetField("MaxStdTot", MaxStdTotVal)
        outFeature.SetField("MangArea", MangAreaVal)
        outFeature.SetField("d8716Area", float(diff8716AreaVal))
        outFeature.SetField("d1216Area", float(diff1216AreaVal))
        
        outLayer.CreateFeature(outFeature)
        outFeature = None
    inFeature = inLayer.GetNextFeature()

# Save and close the shapefiles
inDataSet = None
outDataSet = None
