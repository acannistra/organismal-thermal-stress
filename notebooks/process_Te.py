import pandas as pd
import geopandas as gpd
from subprocess import call
from os.path import split, basename, join
from os import listdir, remove
from tempfile import NamedTemporaryFile
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import geojson
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon, mapping
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from PIL import Image
from datetime import datetime
from multiprocessing import Pool
from functools import partial
import rasterio
import pyproj
import geojson
from shapely.geometry import Polygon, mapping
import shapely.ops as ops
from rasterio.features import shapes
from rasterio.plot import show

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
        

def generateImageAndPolygonFromRaster(raster, outfile_suffix, threshold_high, compute_area = False):
    with rasterio.open(raster, 'r') as src:
        print("reading " + raster)
        # read image into ndarray
        im = src.read()
        bounds = src.bounds
        im = np.transpose(im, [1,2,0])
        im = im.squeeze()  
        
        stress_thresh_shapes= list(shapes(np.uint8(im > threshold_high)))#, transform=src.transform))
        stress_thresh_polys = []
        for poly, value in stress_thresh_shapes:
            if(value == 1.0):
                print(len(poly['coordinates']))
                poly['coordinates'] = [src.affine * xy for xy in poly['coordinates'][0]]
                stress_thresh_polys.append(Polygon(shell=poly['coordinates']))
            
        area = 0
        if (compute_area):
            print("computing area...\r")
            # compute polygon area

            def get_geom_area(geom):
                _geom_area = ops.transform(
                    partial(
                        pyproj.transform,
                        pyproj.Proj(init='EPSG:4326'),
                        pyproj.Proj(
                            proj='aea',
                            lat1=geom.bounds[1],
                            lat2=geom.bounds[3])),
                    geom)
                
                return(_geom_area.area)

            area = sum([get_geom_area(g) for g in stress_thresh_polys])
            print(area)
            print("area: {}".format(area))
    
            print('done.')
            
        
        with open(outfile_suffix + ".geojson", 'w') as gjf:
            geojson.dump(geojson.GeometryCollection(stress_thresh_polys), gjf)
        
        
        
        
        im = np.flip(im, 0)

        norm = Normalize(vmin=200, vmax=320, clip=False) # ARBITRARY VALUES

        im = Image.fromarray(np.uint8(plt.cm.viridis(norm(im)) * 255))
        im.save(outfile_suffix + ".gif")
        with open(outfile_suffix + '.ref', 'w') as f:
            f.write("{}.gif,{},{},{},{},{}.geojson".format(basename(outfile_suffix),
                                                           bounds.left, bounds.right, bounds.bottom, bounds.top,
                                                           basename(outfile_suffix)))
        
        
        

    
def process_grouped_xyz(xyzgroup, thresh_high, outdir, xsize, ysize, compute_area = False):
    """
        Mapper work function for a group of xyz rows, index is datetime. Assumes (x, y, z). 
        
        Uses xyzgroup[0] as prefix for file names.
        
        Uses pointsToGrid to create (xsize, ysize) raster then thresholds + produces GeoJSON.
        
    """
    
    outfile_prefix = xyzgroup[0].strftime("%Y%m%d") # it's a date
    generatedRasterFilename = pointsToGrid(xyzgroup[1], join(outdir, outfile_prefix + ".tif"), xsize, ysize)
    area = generateImageAndPolygonFromRaster(generatedRasterFilename, 
                                             join(outdir, outfile_prefix),
                                             thresh_high, 
                                             compute_area)
    
    try: 
        remove(generatedRasterFilename)
    except Exception as e:
        print(e)
        
    return((outfile_prefix, area))
    
    
    
    
    
    

@click.command()
@click.argument('file')
@click.option("-o", help="output directory", default=".")
@click.option("--date_col", help="date column in csv (int or str)", default=0)
@click.option("--cores", help="number of cores to parallelize into. default: all", type=click.INT)
@click.option("--thresh_high", help='upper temperature threshold (degrees kelvin)', type=click.INT)
@click.option("--area_file", help="file to write stressed area into", default=None)
def main(file, o, date_col, cores, thresh_high, area_file):
    """
    Process FILE into daily image/polygons for web visualization. 
    """
    data = pd.read_csv(file,
                       parse_dates=[0], header=None, 
                       date_parser = lambda x: datetime.strptime(x, "%Y%m%d%H")).set_index(0)
    
    data.columns = ["y", "x", "z"]

    
    daygroups = data.groupby(pd.Grouper(freq="d"))

    compute_area = False
    if(area_file is not None):
        compute_area = True
    
    if(cores is None):
        processpool = Pool()
    else:
        processpool = Pool(processes = cores)
        
    _process_grouped_xyz = partial(process_grouped_xyz, 
                                   thresh_high = thresh_high, 
                                   outdir= o,
                                   xsize = 500, ysize = 500, 
                                   compute_area=compute_area)
    ret = list(processpool.imap(_process_grouped_xyz, daygroups))
    
    if(area_file is not None):
        _a = pd.DataFrame(np.array(ret).T)
        _a.to_csv(area_file, index=False)
    
    

    
if __name__ == "__main__":
    main()
    
    

    
