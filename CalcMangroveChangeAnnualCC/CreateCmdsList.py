import pandas
import os.path

gmwTiles = pandas.read_csv('./AustraliaSqGrid_MangroveRegionsV1.csv', delimiter = ',')
cmdBase = 'python /home/552/pjb552/agdc_mangrovemonitoring/CalcMangroveChangeAnnualCC/CalcMangroveChangeWithAnnualCC.py '
outFileTotalImgBase = '/g/data/r78/pjb552/MangChangePVFC_V2/totalimgs'
outFileTypeImgBase = '/g/data/r78/pjb552/MangChangePVFC_V2/typeimgs'
outFileStatsBase = '/g/data/r78/pjb552/MangChangePVFC_V2/stats'
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
        
    posFileName = midLatStr+'_'+midLonStr+'_'+str(gmwTiles['GridID'][tile])
   
    outTotalImgTileName = 'MangTotalExtent_'+posFileName+'.tif'
    outTypeImgTileName = 'MangTypeExtent_'+posFileName+'.tif'
    outStatsTileName = 'MangExtentStats_'+posFileName+'.csv'

    cmd = cmdBase + '--startyear 1987 --endyear 2016 --ccthres1 12 --ccthres2 35 --ccthres3 70 '
    cmd = cmd + ' --minlat ' + str(gmwTiles['MinY'][tile])
    cmd = cmd + ' --maxlat ' + str(gmwTiles['MaxY'][tile])
    cmd = cmd + ' --minlon ' + str(gmwTiles['MinX'][tile])
    cmd = cmd + ' --maxlon ' + str(gmwTiles['MaxX'][tile])
    cmd = cmd + ' --outimg ' + os.path.join(outFileTotalImgBase, outTotalImgTileName)
    cmd = cmd + ' --outtypeimg ' + os.path.join(outFileTypeImgBase, outTypeImgTileName)
    cmd = cmd + ' --outstats ' + os.path.join(outFileStatsBase, outStatsTileName)
    #print(cmd)
    cmds.append(cmd)

outRunLstFile = 'RunCalcAnnualMangChange.sh'
f = open(outRunLstFile, 'w')
for item in cmds:
   f.write(str(item)+'\n')
f.flush()
f.close()


outQSubFile = 'QSubCalcAnnualMangChange.pbs'
outGenPBSFile = 'GenQSubCalcAnnualMangChangeCmds.sh'
f = open(outGenPBSFile, 'w')
f.write(str('python ../PBS/CreateQSubScripts.py --input ' + outRunLstFile + ' --output ' + outQSubFile + ' --memory 32Gb --time 30:00:00 --cores 16 --project r78')+'\n')
f.flush()
f.close()

