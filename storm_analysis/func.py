# -*- coding: utf-8 -*-
"""
Created on Tue Apr  5 13:10:49 2022
This script contains all functions

@author: Josue
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import geoplot as gplt
from datetime import timezone, timedelta, datetime
from skyfield.api import load, wgs84, EarthSatellite
from shapely.geometry import Point, Polygon
from pyproj.database import query_utm_crs_info
from pyproj.aoi import AreaOfInterest
import matplotlib.pyplot as plt
from netCDF4 import Dataset as netcdf
import time





##### subpoint prop
def collect_ground_track(satellite, instrument, start, end, delta, mask=None):
    # load the timescale and define starting and ending points
    ts = load.timescale()
    # construct a satellite for propagation
    sat = EarthSatellite(satellite["orbit"]["tle"][0], satellite["orbit"]["tle"][1], satellite["name"])
    # load the ephemerides
    eph = load('de421.bsp')
    # enumerate the time steps
    times = pd.date_range(
        start = start,
        end = end,
        freq = delta
    ).tz_convert(timezone.utc)
   
    def is_target_sunlit(time, sat, eph):
        t = ts.utc(time)
        solar_obs = (eph["earth"] + wgs84.subpoint(sat.at(t))).at(t).observe(eph["sun"]).apparent()
        solar_alt, solar_az, solar_dist = solar_obs.altaz()
        return solar_alt.degrees > 0
    
    def is_satellite_sunlit(time, sat, eph):
        return sat.at(time).is_sunlit(eph)
        
    def get_sub_satellite_point(time, sat):
        ssp = wgs84.subpoint(sat.at(ts.utc(time)))
        return Point(ssp.longitude.degrees, ssp.latitude.degrees)
    
    df = pd.DataFrame(
        [{
            'time': time,
            'satellite': satellite['name'],
            'instrument': satellite['instrument']['name'],
            'geometry': get_sub_satellite_point(time, sat)
        } 
            for time in times
            if (satellite["instrument"]["req_target_sunlit"] is None or is_target_sunlit(time, sat, eph) == satellite["instrument"]["req_target_sunlit"])
            and (satellite["instrument"]["req_self_sunlit"] is None or is_satellite_sunlit(time, sat, eph) == satellite["instrument"]["req_self_sunlit"])
        ],
        columns=['time', 'satellite', 'instrument', 'geometry']
    )
   
    gdf = gpd.GeoDataFrame(df, geometry=df.geometry, crs="EPSG:4326")
    if mask is None:
        return gdf
    return gpd.clip(gdf, mask).reset_index(drop=True)
###########################
def field_of_regard_to_swath_width(height, field_of_regard):
    """
    Fast conversion from field of regard to swath width.

    Args:
        height (float): Height (meters) above surface of the observation.
        field_of_regard (float): Angular width (degrees) of observation.

    Returns:
        float: The observation diameter (meters).
    """
    # mean radius for spherical calculations (based on wgs84, (2*a+b)/3)
    mean_radius = 6371008.771415059
    # rho is the angular radius of the earth viewed by the satellite
    sin_rho = mean_radius / (mean_radius + height)
    # eta is the angular radius of the region viewable by the satellite
    sin_eta = np.sin(np.radians(field_of_regard)/2)
    # epsilon is the min satellite elevation for obs (grazing angle) 
    cos_epsilon = sin_eta/sin_rho
    # lambda is the Earth central angle
    _lambda = np.pi/2 - np.arcsin(sin_eta) - np.arccos(cos_epsilon)
  
    return 2*mean_radius*_lambda

def get_utm_epsg_code(p):
            results = query_utm_crs_info(
                datum_name='WGS 84', 
                area_of_interest=AreaOfInterest(
                    p.x, p.y, p.x, p.y
                )
            )
            if len(results) > 0:
                return results[0].code
            else:
                return '32663'
def hack_coords(coords):
        lon = np.array([c[0] for c in coords])
        lat = np.array([c[1] for c in coords])
        # wrap negative coords crossing antimeridian to positive values
        if np.any(lon < 0) and np.any(lon > 0) and not np.all(np.abs(lon)<90):
            lon[lon<0] += 360
        return list(zip(lon, lat))

def confusion_matrix(dt, gt):
    dt['cat']="Null"
    
    for i in range(len(dt)):
        if dt.observation[i]==True and gt.observation[i]==True:
            dt.cat[i]='TP'
        elif dt.observation[i]==False and gt.observation[i]==True:
            dt.cat[i]='FP'
           
        elif dt.observation[i]==True and gt.observation[i]==False:
            dt.cat[i]='FN'
            
        elif dt.observation[i]==False and gt.observation[i]==False:
            dt.cat[i]='TN'
    values= dt.cat.value_counts()
    pot=["TP","FP", "FN","TN"]
    a={values.index[i]: values[i] for i in range(len(values))}
    noin=[key for key in a]
    for tr in pot:
        if tr not in noin:
            a[tr]=0
    return a 