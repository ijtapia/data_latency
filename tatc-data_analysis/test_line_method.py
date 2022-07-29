# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 00:31:38 2022

@author: Josue Tapia
"""
from shapely.geometry import Polygon
from tatc.schemas.satellite import Satellite, WalkerConstellation
from tatc.schemas.instrument import Instrument
from tatc.schemas.orbit import TwoLineElements
from tatc.analysis.coverage import collect_observations
import contextily as ctx
import geoplot as gplt
import datetime as dt
from Storm_analysis.geos_obs import test_line, get_observations
import time
import pandas as pd


tic=time.perf_counter()
target = Polygon([(-153.5,-0.4),(-152,-2), (-148.5,3), (-151,3)])

from tatc.generation.points import generate_fibonacci_lattice_points
points_df = generate_fibonacci_lattice_points(10e3, mask=target)
print("there are ", len(points_df), "points in the grid")

ins=Instrument(name= "Scon1",
     field_of_regard= 20,
     min_access_time= 0,
     duty_cycle= 1,
     duty_cycle_scheme= "fixed")

orb=TwoLineElements(type= "tle",
    tle= [
        #"1 25544U 98067A   22194.89145811  .00006208  00000+0  11693-3 0  9993",
        #"2 25544  51.6431 204.3260 0004839   8.8854  63.9523 15.49933573349324"
        "1 27424U 02022A   22201.61000978  .00000606  00000+0  14400-3 0  9996", #Retrograde test (Aqua's orbit)
        "2 27424  98.2481 143.1887 0001867  94.7341  85.4333 14.57334455 75015"
        ])

sat1=Satellite(type= "satellite", 
   name= "ISS-test",
   orbit= orb,
   instruments= [ins])
instrument={
    "name": ins.name,
    "field_of_regard": ins.field_of_regard,
    "min_access_time": ins.min_access_time,
    "req_self_sunlit": None,
    "req_target_sunlit": None
}
constellation= WalkerConstellation(
    name= "ISS_Constellation",
    type='walker',
    configuration= 'delta',
    instruments=[ins],
    orbit= sat1.orbit,
    number_satellites= 6,
    number_planes= 2,
    relative_spacing= 0.1
    ).generate_members() #assumes 0 drag coeff.
tt_sat={
    "type": "satellite",
    "name": constellation[0].name,
    "orbit": {
        "type":"tle",
        "tle":constellation[0].orbit.tle
    },
    "instrument": instrument
}
utc = dt.timezone.utc
start= dt.datetime(2022,6,1,2,30, tzinfo= utc)
end= dt.datetime(2022,6,1, 3,0, tzinfo=utc)
#%%
t_tim=start
while t_tim <end:
    sim_end=t_tim + dt.timedelta(minutes=30)
    cov,storms= get_observations(tt_sat,t_tim, sim_end, instrument)
    t_tim=sim_end
    display(cov.iloc[0].geometry)
    
"""
ax=gplt.polyplot(cov,
                   zorder=1,
                   extent=(-180,-90,180,90),
                   
                   projection= gplt.PlateCarree()
                   )
ax2=gplt.pointplot(storms,
                   ax=ax,
                   hue='observation',
                   extent=(-180,-90,180,90),
                  
                   projection= gplt.PlateCarree()
                   )


fig=ctx.add_basemap(ax2,
               source=ctx.providers.Stamen.TerrainBackground,
               crs="epsg:4326",
               attribution=False)
"""
    

"""
covt= test_line(tt_sat, start, end, instrument  )
from tatc.schemas.point import Point
points= points_df.apply(lambda r: Point(id=r.point_id, latitude=r.geometry.y, longitude=r.geometry.x), axis=1)
results_list=[
    collect_observations(point, constellation[1], ins, start, end, omit_solar=True)
    for point in points
    ]
results=pd.concat( results_list, ignore_index=True)

points_df['obs']=points_df.geometry.apply(lambda r: (r in list(results.geometry)))
covt.plot(ax=points_df.plot(points_df.obs),color='None',edgecolor='black')
toc=time.perf_counter()
print(f"The execution time is {toc-tic:0.4f} seconds")
"""