import argparse
import os.path
import os
import shutil
import math

import rsgislib
import rsgislib.imageutils
import rsgislib.imagecalc
import rsgislib.vectorutils
import rsgislib.rastergis

import osgeo.ogr as ogr
import osgeo.osr as osr
import osgeo.gdal as gdal


def createCanopyCoverLyrs(pvfDCImg, canopyMaskSHP, outCanopyMaskImg, outCanopyCoverImg, outExtData, aggImageLyrsOutImg, aggOutExtData, aggOutRes, baseTmpDIR):

    rsgisUtils = rsgislib.RSGISPyUtils()
    uidStr = rsgisUtils.uidGenerator()
    tmpDIR = os.path.join(baseTmpDIR, uidStr)
    
    tmpPresent = True
    if not os.path.exists(tmpDIR):
        os.makedirs(tmpDIR)
        tmpPresent = False 

    ############ DO STUFF ###############
    
    # 0. Make PV no data value to be zero...
    tmpPVImgZeroNoData = os.path.join(tmpDIR, os.path.splitext(os.path.basename(pvfDCImg))[0]+'_nodatazero.kea')
    rsgislib.imagecalc.imageMath(pvfDCImg, tmpPVImgZeroNoData, '(b1>0)&&(b1<=100)?b1:0', 'KEA', rsgislib.TYPE_8UINT)
    rsgislib.imageutils.popImageStats(tmpPVImgZeroNoData, usenodataval=True, nodataval=0, calcpyramids=True)
    pvfDCImg = tmpPVImgZeroNoData # Use this version throughout rest of the processing.
    
    # 1. Reproject the shapefile to epsg 3577
    shpInWKT = rsgisUtils.getProjWKTFromVec(canopyMaskSHP)
    inEPSGCode = rsgisUtils.getEPSGCodeFromWKT(shpInWKT)
    
    if inEPSGCode is not 3577:
        print('Reprojecting canopy mask shapefile')
        outWKT3577 = rsgisUtils.getWKTFromEPSGCode(3577)
        
        shpBasename = os.path.splitext(os.path.basename(canopyMaskSHP))[0]
        tmpReprojSHP = os.path.join(tmpDIR, shpBasename+'_3577proj.shp')
        rsgislib.vectorutils.reProjVectorLayer(canopyMaskSHP, tmpReprojSHP, outWKT3577)
        
        origCanopyMaskSHP = canopyMaskSHP
        canopyMaskSHP = tmpReprojSHP
    
    # 2. Find shapefile extent.
    shpExtent = rsgisUtils.getVecLayerExtent(canopyMaskSHP)
        
    # 3. Create image aligned with pvfDCImg and extent of canopyMaskSHP
    imgBBOX = rsgisUtils.getImageBBOX(pvfDCImg)
    imgResX, imgResY = rsgisUtils.getImageRes(pvfDCImg)
    if imgResX != imgResY:
        raise Exception('The input pixels are not square.')
        
    commonExtent = rsgisUtils.findCommonExtentOnGrid(imgBBOX, imgResX, shpExtent, fullContain=True)    
    rsgislib.imageutils.createCopyImageDefExtent(pvfDCImg, outCanopyMaskImg, 1, commonExtent[0], commonExtent[1], commonExtent[2], commonExtent[3], 1.0, 1.0, 0, 'KEA', rsgislib.TYPE_8UINT)
    
    # 4. Rasterise canopyMaskSHP
    rsgislib.vectorutils.rasterise2Image(canopyMaskSHP, None, outCanopyMaskImg, "", burnVal=1)
    rsgislib.rastergis.populateStats(outCanopyMaskImg, True, True, True)
    
    # 5. Create Canopy Cover on pvfDCImg grid.
    tmpCanopyCountImg = os.path.join(tmpDIR, 'TmpCountImg.kea')
    rsgislib.imagecalc.getImgSumStatsInPxl(pvfDCImg, outCanopyMaskImg, tmpCanopyCountImg, 'KEA', rsgislib.TYPE_32UINT, [rsgislib.SUMTYPE_SUM], 1, False, 16, 16)
    
    nPxlsInGrid = abs(imgResX * imgResY)
    
    rsgislib.imagecalc.imageMath(tmpCanopyCountImg, outCanopyCoverImg, '(b1/'+str(nPxlsInGrid)+')*100', 'KEA', rsgislib.TYPE_32FLOAT)
    rsgislib.imageutils.popImageStats(outCanopyCoverImg, usenodataval=True, nodataval=0, calcpyramids=True)
    
    # 6. Create Mangrove Mask on pvfDCImg grid
    tmpCanopyMaskImg = os.path.join(tmpDIR, 'TmpMaskImg.kea')
    rsgislib.imagecalc.imageMath(outCanopyCoverImg, tmpCanopyMaskImg, 'b1>0?1:0', 'KEA', rsgislib.TYPE_8UINT)
    
    # 7. Stack pvfDCImg and Canopy Cover into a multi band image
    tmpPVCCStackImg = os.path.join(tmpDIR, 'TmpPCCCStackImg.kea')
    rsgislib.imageutils.stackImageBands([pvfDCImg, outCanopyCoverImg], ['PV','CC'], tmpPVCCStackImg, 0.0, 0.0, 'KEA', rsgislib.TYPE_32FLOAT)
    
    # 8. Export PVF and Canopy Cover to HDF5 file.    
    rsgislib.imageutils.extractZoneImageValues2HDF(tmpPVCCStackImg, tmpCanopyMaskImg, outExtData, 1)
    
    # 9. Aggregate image layers to 1 km grids
    imgBBOX = rsgisUtils.getImageBBOX(tmpPVCCStackImg)
    lowResExtent = rsgisUtils.findExtentOnGrid(imgBBOX, aggOutRes, fullContain=False)
    tmpLowResImg4Agg = os.path.join(tmpDIR, 'TmpLowResAggImg.kea')
    rsgislib.imageutils.createCopyImageDefExtent(pvfDCImg, tmpLowResImg4Agg, 1, lowResExtent[0], lowResExtent[1], lowResExtent[2], lowResExtent[3], aggOutRes, aggOutRes, 0, 'KEA', rsgislib.TYPE_8UINT)
    
    tmpAggCanopyCover = os.path.join(tmpDIR, 'TmpAggCanopyCover.kea')
    rsgislib.imagecalc.getImgSumStatsInPxl(tmpLowResImg4Agg, outCanopyCoverImg, tmpAggCanopyCover, 'KEA', rsgislib.TYPE_32FLOAT, [rsgislib.SUMTYPE_MEAN], 1, True, 16, 16)
    
    tmpAggPV = os.path.join(tmpDIR, 'TmpAggPV.kea')
    rsgislib.imagecalc.getImgSumStatsInPxl(tmpLowResImg4Agg, pvfDCImg, tmpAggPV, 'KEA', rsgislib.TYPE_32FLOAT, [rsgislib.SUMTYPE_MEAN], 1, False, 16, 16)
    
    rsgislib.imageutils.stackImageBands([tmpAggPV, tmpAggCanopyCover], ['PV','CC'], aggImageLyrsOutImg, 0.0, 0.0, 'KEA', rsgislib.TYPE_32FLOAT)
    rsgislib.imageutils.popImageStats(aggImageLyrsOutImg, usenodataval=True, nodataval=0, calcpyramids=True)
    
    # 10. Extract Aggregated data to HDF5.
    tmpAggCanopyMaskImg = os.path.join(tmpDIR, 'TmpMaskImg.kea')
    rsgislib.imagecalc.imageMath(tmpAggCanopyCover, tmpAggCanopyMaskImg, 'b1>0?1:0', 'KEA', rsgislib.TYPE_8UINT)
    
    rsgislib.imageutils.extractZoneImageValues2HDF(aggImageLyrsOutImg, tmpAggCanopyMaskImg, aggOutExtData, 1)
    
    ####################################
    
    if not tmpPresent:
        shutil.rmtree(tmpDIR, ignore_errors=True)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='CreateDataCubeCanopyCover.py', description='''Produce canopy cover estimates which are on the same grid as the data cube..''')

    parser.add_argument("--dcpvf", type=str, required=True, help='Photosyntheic vegetation cover fraction on the data cube grid.')
    parser.add_argument("--canopymask", type=str, required=True, help='Shapefile of the canopy mask.')
    parser.add_argument("--canopymaskdc", type=str, required=True, help='Output canopy mask image file which with a grid which corresponds to the DataCube.')
    parser.add_argument("--canopycover", type=str, required=True, help='Output canopy cover image.')
    parser.add_argument("--extractpvcc", type=str, required=True, help='Output HDF5 file with data extracted for mangrove regions.')
    parser.add_argument("--aggimagelyrs", type=str, required=True, help='Output image layer aggregated to a lower resolution.')
    parser.add_argument("--aggextractpvcc", type=str, required=True, help='Output HDF5 file with aggregated data extracted for mangrove regions.')
    parser.add_argument("--aggres", type=int, required=False, default=1000, help='Aggregated output image resolution; note value must be a multiple of 25 m; Default is 1000.')
    parser.add_argument("--tmp", type=str, required=True, help='tmp DIR path.')
    
    # Call the parser to parse the arguments.
    args = parser.parse_args()
        
    createCanopyCoverLyrs(args.dcpvf, args.canopymask, args.canopymaskdc, args.canopycover, args.extractpvcc, args.aggimagelyrs, args.aggextractpvcc, args.aggres, args.tmp)  
    
    
    
    
    