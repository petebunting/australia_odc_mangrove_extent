import datacube
import numpy
import xarray as xr
from datacube.storage import masking
from datacube.storage.masking import mask_to_dict

import matplotlib as mpl
mpl.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.dates
#from IPython.display import display
#import ipywidgets as widgets
import rasterio
from datacube.storage.storage import write_dataset_to_netcdf

dc = datacube.Datacube(app='dc-show changes in mean NDVI values')


## define spatiotemporal range and bands

#define temporal range
start_of_epoch = '2010-01-01'
# latest observation
end_of_epoch = '2015-12-31'

# define wavelenghts
bands_of_interest = [#'blue', 
                     #'green',
                     'red',
                     'nir',
                     'swir1',
                     #'swir2'
                      ]

#Define sensors of interest, # out sensors that aren't relevant for the time period
sensors = [
    'ls8', #May 2013 to present
    'ls7', #1999 to present
    'ls5'  #1986 to present, full continual coverage from 1987 to May 2012
]

query = {'time': (start_of_epoch, end_of_epoch),}

#area of interest
lat_max = -12.14
lat_min = -12.45
lon_max = 132.4
lon_min = 132.2
query['x'] = (lon_min, lon_max)
query['y'] = (lat_max, lat_min)
query['crs'] = 'EPSG:4326'


print("Read pixel quality information.")
#Group PQ by solar day to avoid idosyncracies of N/S overlap differences in PQ algorithm performance
pq_albers_product = dc.index.products.get_by_name(sensors[0]+'_pq_albers')
valid_bit = pq_albers_product.measurements['pixelquality']['flags_definition']['contiguous']['bits']

def pq_fuser(dest, src):
    valid_val = (1 << valid_bit)
    
    no_data_dest_mask = ~(dest & valid_val).astype(bool)
    numpy.copyto(dest, src, where=no_data_dest_mask)
    
    both_data_mask = (valid_val & dest & src).astype(bool)
    numpy.copyto(dest, src & dest, where=both_data_mask)

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


#Retrieve the NBAR and PQ data for sensor n
print("Read pixel image data into memory.")
sensor_clean = {}
for sensor in sensors:
    print(sensor)
    #Load the NBAR and corresponding PQ
    sensor_nbar = dc.load(product= sensor+'_nbar_albers', group_by='solar_day', measurements = bands_of_interest, **query)
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
nbar_clean = xr.concat(sensor_clean.values(), dim='time')
time_sorted = nbar_clean.time.argsort()
nbar_clean = nbar_clean.isel(time=time_sorted)
nbar_clean.attrs['crs'] = crs
nbar_clean.attrs['affine'] = affine
#nbar_clean


#calculate NDVI
print("Calculate NDVI.")
ndvi = ((nbar_clean.nir-nbar_clean.red)/(nbar_clean.nir+nbar_clean.red))
print(ndvi.shape)

print("Setup plotting colours etc.")
#This controls the colour maps used for plotting NDVI
ndvi_cmap = mpl.colors.ListedColormap(['blue','#ffcc66','#ffffcc','#ccff66','#2eb82e','#009933','#006600'])
ndvi_bounds = [-1, 0, 0.1, 0.25, 0.35, 0.5, 0.8, 1]
ndvi_norm = mpl.colors.BoundaryNorm(ndvi_bounds, ndvi_cmap.N)
ndvi.attrs['crs'] = crs
ndvi.attrs['affine'] = affine

print("Calculate annual mean NDVI")
#Calculate annual average NDVI values
annual_ndvi = ndvi.groupby('time.year')
annual_mean = annual_ndvi.mean(dim = 'time') # .mean can be replaced by max, min, median, 
annual_mean_landonly = annual_mean.where(annual_mean>0)
print(annual_mean_landonly.shape)

print("Plot annual mean NDVI")
annual_mean_landonly.plot(col='time', col_wrap=2)
plt.savefig('~/Kakadu_AnnualMeanNDVI.png')
plt.close()
















"""










# calculate two-monthly average NDVI for start of trend
two_monthly_ndvi = ndvi.loc['2015-1':'2015-2']
two_monthly_ndvi.shape


two_monthly_ndvi.plot(col='time', col_wrap=2)

two_monthly_ndvi_mean = two_monthly_ndvi.mean(dim = 'time')
#two_monthly_ndvi_mean.shape
fig=plt.figure()
plt.title('two-monthly-mean ndvi')
plt.imshow(two_monthly_ndvi_mean.squeeze(), interpolation = 'nearest')


# calculate two-monthly average NDVI for middle-start of trend
two_monthly_ndvi2 = ndvi.loc['2015-3':'2015-4']
#two_monthly_ndvi2.shape
#two_monthly_ndvi2.plot(col='time', col_wrap=2)

two_monthly_ndvi_mean2 = two_monthly_ndvi2.mean(dim = 'time')
two_monthly_ndvi_mean2.shape

## plot the two-monthly-mean ndvi
#fig=plt.figure()
#plt.title('two-monthly-mean ndvi2')
#plt.imshow(two_monthly_ndvi_mean2.squeeze(), interpolation = 'nearest')






# calculate two-monthly average NDVI for middle-middle of trend
two_monthly_ndvi3 = ndvi.loc['2015-5':'2015-6']
#two_monthly_ndvi3.shape
#two_monthly_ndvi3.plot(col='time', col_wrap=2)

two_monthly_ndvi_mean3 = two_monthly_ndvi3.mean(dim = 'time')
two_monthly_ndvi_mean3.shape

## plot the two-monthly-mean ndvi
#fig=plt.figure()
#plt.title('two-monthly-mean ndvi3')
#plt.imshow(two_monthly_ndvi_mean3.squeeze(), interpolation = 'nearest')





# calculate two-monthly average NDVI for middle-end of trend
two_monthly_ndvi4 = ndvi.loc['2015-7':'2015-8']
#two_monthly_ndvi4.shape
#two_monthly_ndvi4.plot(col='time', col_wrap=2)

two_monthly_ndvi_mean4 = two_monthly_ndvi4.mean(dim = 'time')
two_monthly_ndvi_mean4.shape

## plot the two-monthly-mean ndvi
#fig=plt.figure()
#plt.title('two-monthly-mean ndvi4')
#plt.imshow(two_monthly_ndvi_mean4.squeeze(), interpolation = 'nearest')







# calculate two-monthly average NDVI for nearly-end of trend
two_monthly_ndvi5 = ndvi.loc['2015-9':'2015-10']
#two_monthly_ndvi5.shape
#two_monthly_ndvi5.plot(col='time', col_wrap=2)

two_monthly_ndvi_mean5 = two_monthly_ndvi5.mean(dim = 'time')
two_monthly_ndvi_mean5.shape

## plot the two-monthly-mean ndvi
#fig=plt.figure()
#plt.title('two-monthly-mean ndvi5')
#plt.imshow(two_monthly_ndvi_mean5.squeeze(), interpolation = 'nearest')






# calculate two-monthly average NDVI for end of trend
two_monthly_ndvi6 = ndvi.loc['2015-11':'2015-12']
#two_monthly_ndvi6.shape
#two_monthly_ndvi6.plot(col='time', col_wrap=2)

two_monthly_ndvi_mean6 = two_monthly_ndvi6.mean(dim = 'time')
two_monthly_ndvi_mean6.shape

## plot the two-monthly-mean ndvi
fig=plt.figure()
plt.title('two-monthly-mean ndvi6')
plt.imshow(two_monthly_ndvi_mean6.squeeze(), interpolation = 'nearest')





# Calculate two-monthly NDVI difference over trend period

two_monthly_ndvi_change1 = two_monthly_ndvi_mean2 - two_monthly_ndvi_mean
two_monthly_ndvi_change2 = two_monthly_ndvi_mean3 - two_monthly_ndvi_mean2
two_monthly_ndvi_change3 = two_monthly_ndvi_mean4 - two_monthly_ndvi_mean3
two_monthly_ndvi_change4 = two_monthly_ndvi_mean5 - two_monthly_ndvi_mean4
two_monthly_ndvi_change5 = two_monthly_ndvi_mean6 - two_monthly_ndvi_mean5

two_monthly_ndvi_change1_landonly = two_monthly_ndvi_change1.where(two_monthly_ndvi_mean>0)
two_monthly_ndvi_change2_landonly = two_monthly_ndvi_change2.where(two_monthly_ndvi_mean>0)
two_monthly_ndvi_change3_landonly = two_monthly_ndvi_change3.where(two_monthly_ndvi_mean>0)
two_monthly_ndvi_change4_landonly = two_monthly_ndvi_change4.where(two_monthly_ndvi_mean>0)
two_monthly_ndvi_change5_landonly = two_monthly_ndvi_change5.where(two_monthly_ndvi_mean>0)

fig = plt.figure()
#plt.title=('two-monthly-mean difference')
plt.imshow(two_monthly_ndvi_change5_landonly.squeeze(), interpolation = 'nearest')




two_monthly_ndvi_change_comb = xr.concat([two_monthly_ndvi_change1_landonly,two_monthly_ndvi_change2_landonly,
                                          two_monthly_ndvi_change3_landonly,two_monthly_ndvi_change4_landonly,
                                         two_monthly_ndvi_change5_landonly])
two_monthly_ndvi_change_comb.shape
#two_monthly_ndvi_change_comb
two_monthly_ndvi_change_comb.plot(col = 'concat_dims', col_wrap=3)







# this converts the map x coordinates into image x coordinates
image_coords = ~affine * (x, y)
imagex = int(image_coords[0])
imagey = int(image_coords[1])

#retrieve the time series for the pixel location clicked above
ts_ndvi = ndvi.isel(x=[imagex],y=[imagey]).dropna('time', how = 'any')

# output time-series plot

fig = plt.figure(figsize=(8,5))
plt.show()

firstyear = start_of_epoch
lastyear = end_of_epoch
ts_ndvi.plot(linestyle= '--', c= 'b', marker = '8', mec = 'b', mfc ='r')
plt.grid()   
plt.axis([firstyear, lastyear, 0, 1])





#Plotting image, view transect and select a location to retrieve a time series
fig = plt.figure()
#Plot the mean NDVI values for a year of interest (yoi)
#Dark green = high amounts of green veg with yellow and oranges lower amounts
#Blue indicates NDVI < 0 typically associated with water
yoi = 2014
#plt.title('Average annual NDVI for '+str(yoi))
arr_yoi = annual_mean_landonly.sel(year =yoi)
plt.imshow(arr_yoi.squeeze(), interpolation = 'nearest', cmap = ndvi_cmap, norm = ndvi_norm,
           extent=[arr_yoi.coords['x'].min(), arr_yoi.coords['x'].max(),
                   arr_yoi.coords['y'].min(), arr_yoi.coords['y'].max()])


"""


