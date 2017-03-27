import pandas
import os.path
import rsgislib

gmwTiles = pandas.read_csv('./GMW_10kGrid_AustMangRegions_csv.csv', delimiter = ',')

year = '2010'
cmds = []
cmdBase = 'python Extract_AnnualNDVI_Tiles.py '
outFileBase = os.path.join('/g/data/r78/pjb552/ndvitiles/', year)

for tile in range(len(gmwTiles)):
    outTileFilename = 'ndvi'+year+'_'+str(tile)+'.nc'
    outTileFile = os.path.join(outFileBase, outTileFilename)
    print(outTileFile)
    
    cmd = cmdBase + ' --tileFile ' + outTileFile + ' --year ' + year
    cmd = cmd + ' --minlat ' + str(gmwTiles['MinY'][tile])
    cmd = cmd + ' --maxlat ' + str(gmwTiles['MaxY'][tile])
    cmd = cmd + ' --minlon ' + str(gmwTiles['MinX'][tile])
    cmd = cmd + ' --maxlon ' + str(gmwTiles['MaxX'][tile])
    print(cmd)
    cmds.append(cmd)

rsgisUtils = rsgislib.RSGISPyUtils()
rsgisUtils.writeList2File(cmds, 'Calc2010AnnualNDVI.sh')
