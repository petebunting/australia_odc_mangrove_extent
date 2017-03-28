import rasterio
import rasterio.features
import datacube
import numpy
from datacube.storage import masking
import xarray
import argparse

def pq_fuser(dest, src):
    valid_bit = 8
    valid_val = (1 << valid_bit)

    no_data_dest_mask = ~(dest & valid_val).astype(bool)
    numpy.copyto(dest, src, where=no_data_dest_mask)

    both_data_mask = (valid_val & dest & src).astype(bool)
    numpy.copyto(dest, src & dest, where=both_data_mask)

dc = datacube.Datacube(app='ExtractAnnualNDVI')

#Define wavelengths/bands of interest, remove this kwarg to retrieve all bands
bands_of_interest = ['red', 'nir']

minLon = 144.3
maxLon = 144.4
maxLat = -38.0
minLat = -38.1

#Define sensors of interest
sensors = ['ls8', 'ls7', 'ls5']
year = '2010'
#define temporal range
start_of_epoch = year+'-01-01'
# latest observation
end_of_epoch = year+'-12-31'

query = {'time': (start_of_epoch, end_of_epoch),}
query['x'] = (minLon, maxLon)
query['y'] = (maxLat, minLat)
query['crs'] = 'EPSG:4326'

#Define which pixel quality artefacts you want removed from the results
mask_components = {'cloud_acca':          'no_cloud',
                   'cloud_shadow_acca' :  'no_cloud_shadow',
                   'cloud_shadow_fmask' : 'no_cloud_shadow',
                   'cloud_fmask' :        'no_cloud',
                   'blue_saturated' :     False,
                   'green_saturated' :    False,
                   'red_saturated' :      False,
                   'nir_saturated' :      False,
                   'swir1_saturated' :    False,
                   'swir2_saturated' :    False,
                   'contiguous' :         True }
                   
                   
print("Read pixel image data into memory.")
sensor_clean = {}
for sensor in sensors:
    print(sensor)
    #Load the NBAR and corresponding PQ
    sensor_nbar = dc.load(product= sensor+'_nbar_albers', group_by='solar_day', measurements = bands_of_interest, **query)
    if bool(sensor_nbar):
        sensor_pq = dc.load(product=sensor+'_pq_albers', group_by='solar_day', fuse_func=pq_fuser, **query)
        #grab the projection info before masking/sorting
        crs = sensor_nbar.crs
        crswkt = sensor_nbar.crs.wkt
        affine = sensor_nbar.affine
        #this line is to make sure there's PQ to go with the NBAR
        sensor_nbar = sensor_nbar.sel(time = sensor_pq.time)
        #Apply the PQ masks to the NBAR
        cloud_free = masking.make_mask(sensor_pq, **mask_components)
        good_data = cloud_free.pixelquality.loc[start_of_epoch:end_of_epoch]
        sensor_nbar = sensor_nbar.where(good_data)
        sensor_clean[sensor] = sensor_nbar
    
#Concatenate data from different sensors together and sort so that observations are sorted by time rather than sensor
print("Merge data from different sensors.")
nbar_clean = xarray.concat(sensor_clean.values(), dim='time')
time_sorted = nbar_clean.time.argsort()
nbar_clean = nbar_clean.isel(time=time_sorted)
nbar_clean.attrs['crs'] = crswkt
nbar_clean.attrs['affine'] = affine

print("Calculate NDVI.")
ndvi = ((nbar_clean.nir-nbar_clean.red)/(nbar_clean.nir+nbar_clean.red))
ndvi.attrs['affine'] = affine
ndvi.attrs['crs'] = crswkt

print("Create Composite")
ndviMean = ndvi.mean(dim = 'time')
ndviMean.attrs['affine'] = affine
ndviMean.attrs['crs'] = crswkt
