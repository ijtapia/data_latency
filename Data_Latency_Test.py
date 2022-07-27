# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 11:45:26 2022
This script is a test for ground stations and storm simulations
@author: Josue Tapia
"""
from tatc.analysis.latency import collect_downlinks, aggregate_downlinks, compute_latency
from tatc.analysis.coverage import collect_observations
from tatc.schemas.point import GroundStation
from tatc.schemas.satellite import Satellite, WalkerConstellation
from tatc.schemas.instrument import Instrument
from tatc.schemas.orbit import TwoLineElements
from tatc.schemas.point import Point
#from tatc.analysis.track import collect_ground_track


from storm_analysis.geos_obs import get_observations
from storm_analysis.func import collect_ground_track

from datetime import timezone
import time
import itertools
from datetime import datetime, timedelta

import geopandas as gpd
import numpy as np
import datetime as dt
import pandas as pd
import contextily as ctx
import geoplot as gplt
"""
gr1=GroundStation(name= "Alaska",
   latitude = 64.859,
   longitude = -147.854,
   min_elevation_angle = 25,
   min_access_time= 10)
gr2=GroundStation(name= "Svalbard",
   latitude = 78.22,
   longitude = 15.40,
   min_elevation_angle = 25,
   min_access_time= 10
    
    )
gr3=GroundStation(name= "McMurdo",
   latitude = -77.846,
   longitude = 166.668,
   min_elevation_angle = 25,
   min_access_time= 10
    )
gr4=GroundStation(name= "Wallops",
   latitude = 37.94,
   longitude = -75.46,
   min_elevation_angle = 25,
   min_access_time= 10
    )
gr_network=[gr1, gr2, gr3, gr4]
"""
gr1=GroundStation(name= "Oregon",
   latitude = 43.804,
   longitude = -120.55,
   min_elevation_angle = 25,
   min_access_time= 10)
gr2=GroundStation(name= "Ohio",
   latitude = 40.41,
   longitude = -82.90,
   min_elevation_angle = 25,
   min_access_time= 10
    
    )
gr3=GroundStation(name= "Ireland",
   latitude = 53.1424,
   longitude = -7.6921,
   min_elevation_angle = 25,
   min_access_time= 10
    )
gr4=GroundStation(name= "Stockholm",
   latitude = 59.3293,
   longitude = 18.0686,
   min_elevation_angle = 25,
   min_access_time= 10
    )
gr5=GroundStation(name= "Bahrain",
   latitude = 26.0667,
   longitude = 50.5577,
   min_elevation_angle = 25,
   min_access_time= 10
    )
gr6=GroundStation(name= "Seoul",
   latitude = 37.5665,
   longitude = 126.97,
   min_elevation_angle = 25,
   min_access_time= 10
    )
gr7=GroundStation(name= "Sydney",
   latitude = -33.8688,
   longitude = 151.2093,
   min_elevation_angle = 25,
   min_access_time= 10
    )
gr8=GroundStation(name= "Cape Town",
   latitude = -33.91,
   longitude = 18.42,
   min_elevation_angle = 25,
   min_access_time= 10
    )
gr9=GroundStation(name= "Punta Arenas",
   latitude = -53.163,
   longitude = -70.91,
   min_elevation_angle = 25,
   min_access_time= 10
    )
gr10=GroundStation(name= "Hawaii",
   latitude = 19.89,
   longitude = -155.5828,
   min_elevation_angle = 25,
   min_access_time= 10
    )
gr11=GroundStation(name= "Wallops",
   latitude = 37.94,
   longitude = -75.46,
   min_elevation_angle = 25,
   min_access_time= 10
    )
"""
gr11=GroundStation( name= "New Delhi",
                    latitude= 28.6139,
                    longitude= 77.209,
                    min_elevation_angle=25,
                    min_access_time=10
    )

"""
"""
gr11=GroundStation( name= "Manila",
                    latitude= 14.599,
                    longitude= 120.98,
                    min_elevation_angle=25,
                    min_access_time=10
    )
"""
"""
gr11=GroundStation( name= "Fortaleza",
                    latitude= -3.73,
                    longitude= -38.52,
                    min_elevation_angle=25,
                    min_access_time=10
    )
"""
"""
gr11=GroundStation( name= "New Zealand",
                    latitude= -40.9,
                    longitude= 174.88,
                    min_elevation_angle=25,
                    min_access_time=10
    )
"""
gr_network=[gr1, gr2, gr3, gr4,gr5, gr6, gr7, gr8, gr9, gr10]

ins=Instrument(name= "Scon1",
     field_of_regard= 20,
     min_access_time= 0,
     duty_cycle= 1,
     duty_cycle_scheme= "fixed")

orb=TwoLineElements(type= "tle",
    tle= [
        "1 25544U 98067A   22194.89145811  .00006208  00000+0  11693-3 0  9993",
        "2 25544  51.6431 204.3260 0004839   8.8854  63.9523 15.49933573349324"
        
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


#start= datetime.fromisoformat("2022-05-22T00:00:00+00:00")
#end= datetime.fromisoformat("2022-05-22T04:00:00+00:00")
utc = dt.timezone.utc
start= dt.datetime(2022,5,22,0,0, tzinfo= utc)
end= dt.datetime(2022,6,23, 0,30, tzinfo=utc)
obs_delta= timedelta(minutes=30)


#%%
def constellation_latency(sat1, instrument ,start, end,gr_network,obs_delta):
    test_sat={
        "type": "satellite",
        "name": sat1.name,
        "orbit": {
            "type":"tle",
            "tle":sat1.orbit.tle
        },
        "instrument": instrument
    }
    t_tim=start
    ico=10
    obs_df=[]
    err_st=[]
    while t_tim<end:
        sim_end= t_tim + obs_delta
        gdf,storms= get_observations(test_sat,t_tim, sim_end, instrument)
        storms=storms[storms['observation']==True] #only observed storms
        storms=storms.reset_index()
        if not storms.empty:
            data=[]
            for i in range(len(storms.geometry)):
                obs=collect_observations(Point(id= ico*i, latitude= storms.lat[i], longitude= storms.lon[i]), 
                                         sat1, ins, t_tim, sim_end)
                if not obs.empty:
                    data.append({'point_id': obs.point_id[0],
                                 'satellite': sat1.name,
                                 'label': storms.id[i],
                                 'instrument': instrument["name"],
                                 'geometry': obs.geometry[0],
                                 'start': obs.start[0],
                                 'end': obs.end[0],
                                 "access": obs.access[0],
                                 'epoch': obs.epoch[0]})
                else: #observations that are not visible to the coverage model?
                    err_st.append({
                        "satellite": sat1.name,
                        "latitude": storms.lat[i],
                        'longitude': storms.lon[i],
                        "label": storms.id[i],
                        "start": t_tim,
                        "end": sim_end
                        })
            if data:
                observation=pd.DataFrame(data)
                observations=gpd.GeoDataFrame(observation, geometry=observation.geometry )
                obs_df.append(observations)
            t_tim= sim_end
            
        else:
            t_tim= sim_end
    
    observations=gpd.GeoDataFrame(pd.concat(obs_df, ignore_index=True))
    
    results = gpd.GeoDataFrame()
    
    downlinks = [ 
        collect_downlinks(gr, sat1,start, end+timedelta(days=1))
        for gr in gr_network
        ]
    downlinks= aggregate_downlinks(downlinks)
    for _, observation in observations.iterrows():
        results = results.append(compute_latency(
                                    observation,
                                        downlinks
                                        )
                                    )
    results.latency= results.latency.apply(lambda r:r/timedelta(hours=1) ) #latency in hours 
    return results,err_st, downlinks
#results,err_st = constellation_latency(constellation[3], instrument,start, end, gr_network, obs_delta)



re_sat=[]
err_sat=[]
dw=[]
tic=time.perf_counter()
for sat in constellation:
    results,err_st, downlinks = constellation_latency(sat, instrument,start, end, gr_network, obs_delta)
    re_sat.append(results)
    err_sat.append(err_st)
    dw.append(downlinks)
latency_data=pd.concat(re_sat, ignore_index=True)
downlinks_data=pd.concat(dw, ignore_index=True)
err_sat=list(itertools.chain(*err_sat))
err=pd.DataFrame(err_sat)
err=gpd.GeoDataFrame(err,  geometry= gpd.points_from_xy(err.longitude, err.latitude))
toc=time.perf_counter()
print(f"the simulation took{toc-tic:0.4f} seconds")
#paper discussion: a storm observation is treated as individual observations by every satellite

#%%
######################################################
                ##########################
                ##### Visualization  #####
                ##########################
######################################################
from matplotlib import pyplot as plt
station_df=latency_data.station_name.value_counts().reset_index(name='observations')
plt.subplot(1, 2, 1)
plt.bar(station_df['index'], station_df.observations)
plt.xticks(rotation=90)
plt.xlabel('Ground Stations')
plt.ylabel('Storm Observations')
plt.title('Observations')

df1=downlinks_data.drop(columns=['start', 'epoch', 'end'], axis=1)
df1=df1.groupby('station_name').agg(
    {
     #"geometry":"first",
     "access": "sum"
     }
    )
aver=np.mean(latency_data.latency)
print("Average latency", aver," hours")
plt.subplot(1, 2, 2)
plt.hist(latency_data.latency, bins=40)
plt.title("Constellation Latency")
plt.xlabel('Latency [hr]')
plt.ylabel("Frequency")
plt.plot()
latency_data=latency_data.drop(columns=["point_id"], axis=1)
df_re=latency_data.groupby("station_name").agg(
    {
     #"geometry": "first",
     "station_name": "first",
     "latency": "mean"
     }
    
    ).reset_index(drop=True)

new=(df_re.merge(df1, left_on='station_name', right_on='station_name').reindex(
    columns=["station_name", "latency","access"]))


#g_track=collect_ground_track(test_sat, instrument, start, end+timedelta(hours=4), 
#                             dt.timedelta(seconds = 300), mask=None) #older version
gr_df=pd.DataFrame({'gr_name': [gr.name for gr in gr_network],
                    'lat':[gr.latitude for gr in gr_network],
                    'lon':[gr.longitude for gr in gr_network]})
gr_df=gpd.GeoDataFrame(gr_df, geometry=gpd.points_from_xy(gr_df.lon, gr_df.lat))

gr_df=(gr_df.merge(new, left_on='gr_name', right_on='station_name').reindex(columns=["station_name","lat","lon", "geometry","latency", "access"]))
gr_df.access=gr_df.access.apply(lambda r: r/timedelta(hours=1))

ax=gplt.pointplot(err,
                   color='red',
                   extent=(-180,-90,180,90),
                   
                   projection= gplt.PlateCarree()
                   )
ax2=gplt.pointplot(gr_df,
                   ax=ax,
                   hue='latency',
                   extent=(-180,-90,180,90),
                   legend= True,
                   projection= gplt.PlateCarree()
                   )


ctx.add_basemap(ax2,
               source=ctx.providers.Stamen.TerrainBackground,
               crs="epsg:4326",
               attribution=False)
plt.plot()
#%%

ax=gplt.pointplot(latency_data,
                  hue='latency',
                  legend=True,
                 extent=(-180,-90,180,90),
                 projection= gplt.PlateCarree())
ctx.add_basemap(ax,
               source=ctx.providers.Stamen.TerrainBackground,
               crs="epsg:4326",
               attribution=False)
plt.plot()
bg=np.array(list(latency_data.latency))
vl=np.percentile(bg, 90)
print(f"the 90th data_latency percentile is {vl} hours")
#%%
"""
tt_sat={
    "type": "satellite",
    "name": constellation[1].name,
    "orbit": {
        "type":"tle",
        "tle":constellation[1].orbit.tle
    },
    "instrument": instrument
}


cov, cluster_gpd= get_observations(tt_sat, err.start[0], err.end[0], instrument)
cluster_gpd=cluster_gpd[cluster_gpd['observation']==True]
ax1=gplt.pointplot(cluster_gpd,
                   
                   color='brown',
                   extent=(-180,-90,180,90),
                   projection= gplt.PlateCarree())

ax=gplt.polyplot(cov,
                 ax=ax1,
                 edgecolor="black",
                 zorder=1,
                 extent=(-180,-90,180,90),
                 projection= gplt.PlateCarree())
ctx.add_basemap(ax,
               source=ctx.providers.Stamen.TerrainBackground,
               crs="epsg:4326",
               attribution=False)
plt.plot()
"""