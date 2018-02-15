
import rsgislib
import rsgislib.imageutils

pvfDCImg = '/Users/pete/Dropbox (EOED)/PeteBunting/Projects/AustralianMangroves/MangroveCanopyCover/tmp/a03c36/PVFromCube_Adelade_2016_nodatazero.kea'
outCanopyMaskImg = './Adelade_2016_CanopyMask_1m.kea'

rsgislib.imageutils.createCopyImageDefExtent(pvfDCImg, outCanopyMaskImg, 1, 586925.0, 590300.0, 3780650.0, 3797700.0, 1.0, 1.0, 0, 'KEA', rsgislib.TYPE_8UINT)



#[-1844400.0, -1843725.0, -2474500.0, -2494075.0]
    