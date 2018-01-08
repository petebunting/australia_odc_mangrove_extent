import osgeo.ogr as ogr 
import osgeo.osr as osr
import os.path

def createPolySHP4LstBBOXs(csvFile, outSHP, espgCode, minXCol=0, maxXCol=1, minYCol=2, maxYCol=3, ignoreRows=0, force=False):
    """
This function takes a CSV file of bounding boxes (1 per line) and creates a polygon shapefile.
    
* csvFile - input CSV file.
* outSHP - output ESRI shapefile
* espgCode - ESPG code specifying the projection of the data (4326 is WSG84 Lat/Long).
* minXCol - The index (starting at 0) for the column within the CSV file for the minimum X coordinate.
* maxXCol - The index (starting at 0) for the column within the CSV file for the maximum X coordinate.
* minYCol - The index (starting at 0) for the column within the CSV file for the minimum Y coordinate.
* maxYCol - The index (starting at 0) for the column within the CSV file for the maximum Y coordinate.
* ignoreRows - The number of rows to ignore from the start of the CSV file (i.e., column headings)
* force - If the output file already exists delete it before proceeding.
"""
    try:
        if os.path.exists(outSHP):
            if force:
                driver = ogr.GetDriverByName('ESRI Shapefile')
                driver.DeleteDataSource(outSHP)
            else:
                raise Exception("Output file already exists")
        # Create the output Driver
        outDriver = ogr.GetDriverByName('ESRI Shapefile')
        # create the spatial reference, WGS84
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(int(espgCode))
        # Create the output Shapefile
        outDataSource = outDriver.CreateDataSource(outSHP)
        outLayer = outDataSource.CreateLayer(os.path.splitext(os.path.basename(outSHP))[0], srs, geom_type=ogr.wkbPolygon )
        # Get the output Layer's Feature Definition
        featureDefn = outLayer.GetLayerDefn()
    
        dataFile = open(csvFile, 'r')
        rowCount = 0
        for line in dataFile:
            if rowCount >= ignoreRows:
                line = line.strip()
                if line != "":
                    comps = line.split(',')
                    # Get values from CSV file.
                    minX = float(comps[minXCol])
                    maxX = float(comps[maxXCol])
                    minY = float(comps[minYCol])
                    maxY = float(comps[maxYCol])
                    # Create Linear Ring
                    ring = ogr.Geometry(ogr.wkbLinearRing)
                    ring.AddPoint(minX, maxY)
                    ring.AddPoint(maxX, maxY)
                    ring.AddPoint(maxX, minY)
                    ring.AddPoint(minX, minY)
                    ring.AddPoint(minX, maxY)
                    # Create polygon.
                    poly = ogr.Geometry(ogr.wkbPolygon)
                    poly.AddGeometry(ring)
                    # Add to output shapefile.
                    outFeature = ogr.Feature(featureDefn)
                    outFeature.SetGeometry(poly)
                    outLayer.CreateFeature(outFeature)
                    outFeature = None
            rowCount = rowCount + 1
        dataFile.close()
        outDataSource = None
    except Exception as e:
        raise e
        

        



#createPolySHP4LstBBOXs('/Users/pete/Development/agdc_mangrovemonitoring/AustraliaMangroveTileGrid/GMW_10kGrid_AustMangOnlyRegions_csv.csv', '/Users/pete/Development/agdc_mangrovemonitoring/AustraliaMangroveTileGrid/GMW_10kGrid_AustMangOnlyRegions.shp', 4326, minXCol=0, maxXCol=1, minYCol=2, maxYCol=3, ignoreRows=1, force=True)


createPolySHP4LstBBOXs('/Users/pete/Development/agdc_mangrovemonitoring/AustraliaMangroveTileGrid/CapeSubset10kGrid_csv.csv', '/Users/pete/Development/agdc_mangrovemonitoring/AustraliaMangroveTileGrid/CapeSubset10kGrid.shp', 4326, minXCol=0, maxXCol=1, minYCol=2, maxYCol=3, ignoreRows=1, force=True)




