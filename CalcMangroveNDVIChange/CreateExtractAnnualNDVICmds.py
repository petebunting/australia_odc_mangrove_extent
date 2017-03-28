import pandas
import os.path

gmwTiles = pandas.read_csv('./GMW_10kGrid_AustMangOnlyRegions_csv.csv', delimiter = ',')
cmdBase = 'python /home/552/pjb552/agdc_mangrovemonitoring/CalcMangroveNDVIChange/Calc_AnnualNDVI_Tiles.py '

years = ['1987', '1988', '1989', '1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016']

genQSubCmds = []

for year in years:
    print(year)
    cmds = []
    outFileBase = os.path.join('/g/data/r78/pjb552/MangNDVIChange/', year)
    cmds.append('mkdir -p ' + outFileBase )
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
       
        outTileName = 'ndvi'+year+'_'+posFileName+'_'+str(tile)
    
        cmd = cmdBase + ' --tileNCFile ' + os.path.join(outFileBase, outTileName+'_ndvi.nc') + ' --year ' + year
        cmd = cmd + ' --tileNCAMCFile ' + os.path.join(outFileBase, outTileName+'_mangmask.nc')
        cmd = cmd + ' --tileNCCMCFile ' + os.path.join(outFileBase, outTileName+'_mangmask_closed.nc')
        cmd = cmd + ' --tileAFile ' + os.path.join(outFileBase, outTileName+'_pxlcounts.csv')
        cmd = cmd + ' --minlat ' + str(gmwTiles['MinY'][tile])
        cmd = cmd + ' --maxlat ' + str(gmwTiles['MaxY'][tile])
        cmd = cmd + ' --minlon ' + str(gmwTiles['MinX'][tile])
        cmd = cmd + ' --maxlon ' + str(gmwTiles['MaxX'][tile])
        #print(cmd)
        cmds.append(cmd)
    
    outFile = 'RunCalcAnnualNDVIChange_'+year+'.sh'
    f = open(outFile, 'w')
    for item in cmds:
       f.write(str(item)+'\n')
    f.flush()
    f.close()
    
    outQSubFile = 'QSubCalcAnnualNDVIChange_'+year+'.pbs'
    genQSubCmds.append('python ../PBS/CreateQSubScripts.py --input ' + outFile + ' --output ' + outQSubFile + ' --memory 32Gb --time 08:00:00 --cores 16 --project r78')


outFile = 'GenQSubCalcAnnualNDVIChangeCmds.sh'
f = open(outFile, 'w')
for item in genQSubCmds:
   f.write(str(item)+'\n')
f.flush()
f.close()
   