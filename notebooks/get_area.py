import geopandas as gpd
from pandas import DataFrame
import pandas as pd
from glob import glob
from datetime import datetime
import os
import click
from multiprocessing import Pool

def get_area(file):
    try:
        _f = gpd.read_file(file)
        area = _f.geometry.area.sum()
    except Exception as e:
        area = 0
    date = os.path.basename(file).split('.')[0]
    date = datetime.strptime(date, "%Y%m%d")
    return((date, area))
    


@click.command()
@click.argument("dir")
@click.argument("outfile")
def main(dir, outfile):
    
    _p = Pool()
    gj_files = glob(os.path.join(dir, "*.geojson"))
    data = DataFrame(data = list(zip(*_p.map(get_area, gj_files)))).T
    data.columns = ["date", "area"]
    data['area'] = pd.to_numeric(data['area'])
    data = data.set_index(pd.to_datetime(data["date"]))
    data = data.sort_index()
    print(data)
    monthly = data.groupby(pd.Grouper(freq="W")).mean()
    monthlyDateStr = monthly.index.map(lambda x: pd.to_datetime(x).strftime("%b-%d-%y"))
    monthly['date'] = monthlyDateStr
    print(monthly)
    monthly[['date', 'area']].to_csv(outfile, index=None, header=True)
    


    
if __name__ == "__main__":
    main()