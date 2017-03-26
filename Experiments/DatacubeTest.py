import datacube
from datacube.storage import masking
import pandas
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

dc = datacube.Datacube(app='KakaduMangroves')

nbar = dc.load(product='ls5_nbar_albers', x=(132.2, 132.4), y=(-12.45, -12.14), time=('2003-01', '2003-12'), measurements=['red', 'nir'], group_by='solar_day')

nbar.data_vars


autumn = nbar.green.loc['2003-3':'2003-8']



autumn.plot(col='time', col_wrap=3)
plt.savefig('plot.png')


autumn_valid = autumn.where(autumn != autumn.attrs['nodata'])
autumn_valid.plot(col='time', col_wrap=3)
plt.savefig('plot-nodata.png')


pq = dc.load(product='ls5_pq_albers', x=(132.2, 132.4), y=(-12.45, -12.14), time=('2003-01', '2003-12'))
pq_autumn = pq.pixelquality.loc['2003-3':'2003-8']
pq_autumn.plot(col='time', col_wrap=3)
plt.savefig('plot-pxlqual.png')



pandas.DataFrame.from_dict(masking.get_flags_def(pq), orient='index')

good_data = masking.make_mask(pq, cloud_acca='no_cloud', cloud_fmask='no_cloud', contiguous=True)
autumn_good_data = good_data.pixelquality.loc['2003-3':'2003-8']
autumn_good_data.plot(col='time', col_wrap=3)
plt.savefig('plot-clouds.png')


autumn_cloud_free = autumn_valid.where(autumn_good_data)
autumn_cloud_free.plot(col='time', col_wrap=3)
plt.savefig('plot-cloudfree.png')



red = nbar.red.where(nbar.red != nbar.red.attrs['nodata'])
nir = nbar.nir.where(nbar.nir != nbar.nir.attrs['nodata'])
cloud_free = masking.make_mask(pq, cloud_acca='no_cloud', cloud_fmask='no_cloud', contiguous=True).pixelquality
ndvi = ((nir - red) / (nir + red)).where(cloud_free)
ndvi.shape
ndvi.plot(col='time', col_wrap=5)
plt.savefig('plot-ndvi.png')
plt.close()

ndvi.median(dim='time').plot()
plt.savefig('plot-medndvi.png')

