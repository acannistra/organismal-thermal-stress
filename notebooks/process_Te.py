import pandas as pd
import geopandas as gpd
from subprocess import call
from os.path import split, basename, join
from os import listdir, remove
from tempfile import NamedTemporaryFile
import matplotlib.pyplot as plt
import geojson
import numpy as np
from shapely.geometry import Point, Polygon, mapping
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from PIL import Image
from datetime import datetime
from multiprocessing import Pool
from functools import partial
import rasterio
import geojson
from rasterio.features import shapes

import tqdm


plt.rcParams['figure.figsize'] = (10, 10)
import click

def pointsToGrid(data, raster_outfile, xsize=100, ysize=100):
    """
        Convert xyz points into gridded raster, interpolated to (xsize, ysize).
    """
    _VRT = """
        <OGRVRTDataSource>
            <OGRVRTLayer name='{name}'>
                <SrcDataSource>{loc}</SrcDataSource>
                <GeometryType>wkbPoint</GeometryType>
                <GeometryField encoding='PointFromColumns' x='x' y='y' z='z'/>
            </OGRVRTLayer>
        </OGRVRTDataSource>
    """

    with NamedTemporaryFile('w', suffix = '.csv') as tmpf:
        # save csv
        print(tmpf.name)
        tmpdir, tmpfname = split(tmpf.name)
        data.to_csv(tmpf, index=False)
        tmpf.flush()
        

        
        # create vrt
        vrtTmp = NamedTemporaryFile('w', dir=tmpdir, delete=False)
        vrt = _VRT.format(loc = tmpf.name,
                          name=tmpfname.split(".")[0])
        vrtTmp.write(vrt)
        vrtTmp.flush()
    
        # grid data
        call(["gdal_grid", vrtTmp.name, raster_outfile, "-outsize", str(xsize), str(ysize), 
              "-a", "invdistnn:radius=30"])
        vrtTmp.close()
    
    return(raster_outfile)
        

def generateImageAndPolygonFromRaster(raster, outfile_suffix, threshold_high):
    with rasterio.open(raster, 'r') as src:
        print("reading " + raster)
        # read image into ndarray
        im = src.read()
        bounds = src.bounds
        stress_thresh_shapes= list(shapes(np.uint8(im > threshold_high)))#, transform=src.transform))

       

    
def process_grouped_xyz(xyzgroup, thresh_high, outdir, xsize, ysize):
    """
        Mapper work function for a group of xyz rows. Assumes (x, y, z). 
        
        Uses xyzgroup[0] as prefix for file names.
        
        Uses pointsToGrid to create (xsize, ysize) raster then thresholds + produces GeoJSON.
        
    """
    
    outfile_prefix = xyzgroup[0].strftime("%Y%m%d") # it's a date
    generatedRasterFilename = pointsToGrid(xyzgroup[1], join(outdir, outfile_prefix + ".tif"), xsize, ysize)
    generateImageAndPolygonFromRaster(generatedRasterFilename, outfile_prefix, thresh_high)
    
    try: 
        remove(generatedRasterFilename)
    except Exception as e:
        print(e)
        
    return(outfile_prefix)
    
    
    
    
    
    

@click.command()
@click.argument('file')
@click.option("-o", help="output directory", default=".")
@click.option("--date_col", help="date column in csv (int or str)", default=0)
@click.option("--cores", help="number of cores to parallelize into. default: all", type=click.INT)
@click.option("--thresh_high", help='upper temperature threshold (degrees kelvin)', type=click.INT)
def main(file, o, date_col, cores, thresh_high):
    """
    Process FILE into daily image/polygons for web visualization. 
    """
    data = pd.read_csv(file,
                       parse_dates=[0], header=None, 
                       date_parser = lambda x: datetime.strptime(x, "%Y%m%d%H")).set_index(0)
    
    data.columns = ["y", "x", "z"]

    
    data = data.iloc[:1000] #DELETE THIS

    
    daygroups = data.groupby(pd.Grouper(freq="d"))

    
    
    if(cores is None):
        processpool = Pool()
    else:
        processpool = Pool(processes = cores)
        
    _process_grouped_xyz = partial(process_grouped_xyz, thresh_high = thresh_high, outdir= o, xsize = 500, ysize = 500)
    ret = list(processpool.imap(_process_grouped_xyz, daygroups))
    print(ret)
    

    
if __name__ == "__main__":
    main()
    
    

    
