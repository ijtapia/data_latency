# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 11:45:26 2022
This script is a test for ground stations and storm simulations
@author: Josue Tapia
"""
from tatc_o.analysis.latency import collect_downlinks, aggregate_downlinks, compute_latency
from tatc_o.analysis.coverage import collect_observations

from tatc_o.schemas.point import Point
#from tatc.analysis.track import collect_ground_track

from generate_architectures import get_aws_network, add_gr_network,generate_constellation

from storm_analysis.geos_obs import get_observations


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



aws_network= get_aws_network() #list of aws ground stations

add_network= add_gr_network()  #list of additional ground stations

## define constellation base design variables
instrument_for=20
n_satellites=6
n_planes=2
######
#start= datetime.fromisoformat("2022-05-22T00:00:00+00:00")
#end= datetime.fromisoformat("2022-05-22T04:00:00+00:00")
utc = dt.timezone.utc
start= dt.datetime(2022,5,22,0,0, tzinfo= utc)
end= dt.datetime(2022,5,22, 2,30, tzinfo=utc)
obs_delta= timedelta(minutes=30)

mission_arch=[{
    'type': "ground",
    'name': "AWS network",
    'satellites': generate_constellation(instrument_for, n_satellites, n_planes),
    'ground_network': aws_network,
    'start':start,
    'end': end,
    'delta': obs_delta
    }]
for gr in add_network:
    mission_arch.append({'type': "ground",
    'name': gr.name,
    'satellites': generate_constellation(instrument_for, n_satellites, n_planes),
    'ground_network': aws_network +[gr],
    'start':start,
    'end': end,
    'delta': obs_delta})
    
for _for in range(30, 90, 10):
    mission_arch.append({'type': "instrument_FOR",
    'name': 'Instruments_FOR '+str(_for),
    'satellites': generate_constellation(_for, n_satellites, n_planes),
    'ground_network': aws_network,
    'start':start,
    'end': end,
    'delta': obs_delta})

for n_satellites in range(9,30, 3): 
    mission_arch.append({'type': "number_satellites",
    'name': 'Constellation_with '+str(n_satellites)+' sats',
    'satellites': generate_constellation(_for, n_satellites, n_satellites/3),
    'ground_network': aws_network,
    'start':start,
    'end': end,
    'delta': obs_delta})
    

#%%
def constellation_latency(sat1, instrument, ins,start, end,gr_network,obs_delta):
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

def architecture_analysis(arch):
    constellation= arch['satellites']

    start= arch['start']
    end= arch['end']
    gr_network= arch['ground_network']
    obs_delta= arch['delta']
    
    re_sat=[]
    err_sat=[]
    dw=[]
    tic=time.perf_counter()
    for sat in constellation:
        ins= sat.instruments[0]
        instrument={
            "name": ins.name,
            "field_of_regard": ins.field_of_regard,
            "min_access_time": ins.min_access_time,
            "req_self_sunlit": None,
            "req_target_sunlit": None
        }
        
        results,err_st, downlinks = constellation_latency(sat, instrument, ins, start, end, gr_network, obs_delta)
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
    bg=np.array(list(latency_data.latency))
    vl=np.percentile(bg, 90)

    return latency_data, downlinks_data, err_sat, vl

#paper discussion: a storm observation is treated as an individual observations by every satellite
values=[]
latency_add=[]
add_downlink=[]
for arch in mission_arch:
    latency_data, downlinks_data, err_sat, val=architecture_analysis(arch)
    values.append({'type': arch['type'],
                   "latency_90th_hrs": val})
    latency_add.append(latency_data)
    add_downlink.append(downlinks_data)



#%%
###### Visualize architectures
import matplotlib.pyplot as plt
import seaborn as sns
for i in range(len(latency_add)):
    latency_add[i]['arch_name']= 'arch_'+ str(i+1)
    latency_add[i]['type']= mission_arch[i]['name']
csv_fl=pd.concat(latency_add, ignore_index=True)
csv_fl.to_csv('simulation_results.csv')

data_to_plot={'architecture':[ "arch"+str(i+1) for i in range(len(values))],
              '90th_latency':[lct['latency_90th_hrs'] for lct in values],
              'type':[lct['type'] for lct in values]}
df_plt=pd.DataFrame(data_to_plot)
sns.scatterplot(data=df_plt, x='architecture', y='90th_latency', hue='type' )
plt.xticks(rotation=90)
plt.show()

gr_na=[gro.name for gro in add_network +aws_network ]
gr_obs_arc=[]
for i in range(len(latency_add)):
    st_df=latency_add[i].station_name.value_counts().reset_index(name='observations')
    
    st_df['arch']= "arch"+str(i+1)
    st_df['type']= values[i]["type"]
    gr_obs_arc.append(st_df)
gr_obs_arc=pd.concat(gr_obs_arc, ignore_index=True)
#gr_obs_arc.rename(columns={'index':'gr_name'}) does not work
sns.scatterplot(data=gr_obs_arc, x='index', y='observations', hue='type') #style='arch'
plt.xticks(rotation=90)
plt.xtitle('ground_stations')
plt.show
#%%
raw_data=latency_add
for i in range(len(raw_data)):
    raw_data[i].observed= raw_data[i].observed.apply(lambda r: r.isoformat())
    raw_data[i].downlinked= raw_data[i].downlinked.apply(lambda r: r.isoformat())

import json
feature=json.dumps(raw_data)
with open('latency_data.txt', 'w') as f:
     f.write(latency_add)
"""
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
"""
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