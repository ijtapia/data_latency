# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 20:14:35 2022
This script provides GEOS-5 observations for a predetermined period
@author: Josue Tapia
"""


import datetime as dt
from .func import collect_ground_track, field_of_regard_to_swath_width
from netCDF4 import Dataset as netcdf
import numpy as np
import pandas as pd
import geopandas as gpd
from .line_method import line_string
from skyfield.api import load, wgs84, EarthSatellite


def get_observations(sat1, start,end,instrument):
    ti=start

    while ti< end:
        step = dt.timedelta(minutes = 1)
        tout=ti+dt.timedelta(minutes=30)

        datestr = str(ti.year-16)+str(ti.month).zfill(2)+str(ti.day).zfill(2)
        datestr = datestr + "_"+str(ti.hour).zfill(2)+str(ti.minute).zfill(2)
        file='Storm_analysis/output/cluster_stats_c1440_NR_tb220K_' +datestr+'.nc4'

        f=netcdf(file)
        lat = f.variables['lat'][:][0].tolist()
        lon = f.variables['lon'][:][0].tolist()
        lat_lon=np.column_stack((lat,lon))
        cnprcp= f.variables['cnprcp'][:][0].tolist()

        df = pd.DataFrame(lat_lon, columns=[ 'lat', 'lon'])
        cluster_gpd= gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat))
        cluster_gpd['cnprcp']=cnprcp
        cluster_gpd['id']=[str(i)+'_'+datestr for i in range(len(cluster_gpd))] #generates storm ids


        gdf = collect_ground_track(sat1, instrument, ti, tout, step, mask=None)

        ts = load.timescale()
        iss = EarthSatellite(sat1["orbit"]["tle"][0], sat1["orbit"]["tle"][1], sat1["name"])
        startDate= ti
        satellite_height = wgs84.subpoint(iss.at(ts.utc(startDate))).elevation.m
        sw=field_of_regard_to_swath_width(satellite_height,sat1['instrument']["field_of_regard"])
        ar_cov=line_string(gdf,"4087",sw/2)


        st_cov=ar_cov.geometry[0]
        cluster_gpd["observation"]=cluster_gpd["geometry"].apply(lambda r: r.within(st_cov))

        ob_pos=cluster_gpd[cluster_gpd["observation"]==True]

        ti+= dt.timedelta(minutes=30)
    return ar_cov, cluster_gpd #observed storms

def test_line(sat1, start,end,instrument):
    ti=start


    step = dt.timedelta(seconds=20)





    gdf = collect_ground_track(sat1, instrument, start, end, step, mask=None)

    ts = load.timescale()
    iss = EarthSatellite(sat1["orbit"]["tle"][0], sat1["orbit"]["tle"][1], sat1["name"])
    startDate= ti
    satellite_height = wgs84.subpoint(iss.at(ts.utc(startDate))).elevation.m
    sw=field_of_regard_to_swath_width(satellite_height,sat1['instrument']["field_of_regard"])
    ar_cov=line_string(gdf,"4087",sw/2)


    st_cov=ar_cov.geometry[0]

    return ar_cov
