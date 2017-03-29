import pandas
import os.path

gmwTiles = pandas.read_csv('./GMW_10kGrid_AustMangOnlyRegions_csv.csv', delimiter = ',')
cmdBase = 'python /home/552/pjb552/agdc_mangrovemonitoring/CalcMangroveNDVIChange/Updated/Calc_AnnualNDVI_Tiles_Update.py '
outFileBase = '/g/data/r78/pjb552/MangNDVIChange/'
cmds = []
for tile in range(len(gmwTiles)):
    # Create lat / long file name.    
    midLat = gmwTiles['MinY'][tile] + ((gmwTiles['MaxY'][tile] - gmwTiles['MinY'][tile])/2)
    midLon = gmwTiles['MinX'][tile] + ((gmwTiles['MaxX'][tile] - gmwTiles['MinX'][tile])/2)
    
    midLatStr = str(midLat)
    midLonStr = str(midLon)
    midLatStr = midLatStr.replace('-','')
    midLonStr = midLonStr.replace('-','')
    midLatStr = midLatStr.replace('.','')
    midLonStr = midLonStr.replace('.','')
    
    posFileName = midLatStr+'_'+midLonStr
   
    outTileName = 'ndvi_'+posFileName+'_'+str(tile)

    cmd = cmdBase + ' --tileNCFile ' + os.path.join(outFileBase, outTileName+'_ndvi')
    cmd = cmd + ' --tileNCAMCFile ' + os.path.join(outFileBase, outTileName+'_mangmask')
    cmd = cmd + ' --tileNCCMCFile ' + os.path.join(outFileBase, outTileName+'_mangmask_closed')
    cmd = cmd + ' --tileAFile ' + os.path.join(outFileBase, outTileName+'_pxlcounts')
    cmd = cmd + ' --minlat ' + str(gmwTiles['MinY'][tile])
    cmd = cmd + ' --maxlat ' + str(gmwTiles['MaxY'][tile])
    cmd = cmd + ' --minlon ' + str(gmwTiles['MinX'][tile])
    cmd = cmd + ' --maxlon ' + str(gmwTiles['MaxX'][tile])
    #print(cmd)
    cmds.append(cmd)

outRunLstFile = 'RunCalcAnnualNDVIChange.sh'
f = open(outRunLstFile, 'w')
for item in cmds:
   f.write(str(item)+'\n')
f.flush()
f.close()

outQSubFile = 'QSubCalcAnnualNDVIChange.pbs'
outGenPBSFile = 'GenQSubCalcAnnualNDVIChangeCmds.sh'
f = open(outGenPBSFile, 'w')
f.write(str('python ../../PBS/CreateQSubScripts.py --input ' + outRunLstFile + ' --output ' + outQSubFile + ' --memory 128Gb --time 30:00:00 --cores 16 --project r78')+'\n')
f.flush()
f.close()
