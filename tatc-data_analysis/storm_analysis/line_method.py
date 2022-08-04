# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 21:33:10 2022

@author: josue
"""
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString, MultiLineString,MultiPolygon
from shapely.ops import unary_union
import matplotlib.pyplot as plt
import pandas as pd


#%%
def orbit_type(gdf):
    '''
    orbit_type: detect if an orbit is retrograde or prograde.
    Args:
    :param gdf: Geodetic Geodataframe with Ground track points.
    Return:
    :param ty: string either "Re" or "Pro"
    '''
    st=gdf.geometry[0].x
    nt=gdf.geometry[1].x
    if (st*nt>0): #both with same sign
        pass
    else:
        st=gdf.geometry[1].x
        nt=gdf.geometry[2].x
    if st> nt:
        ty="Re"
    elif st<nt:
        ty="Pro"
    return ty
def cutter(pr,gdf,ty,qsr,cpe):

    if ty=='Re':
        if qsr==True and cpe=='nd': # antimeridian crossing due to swath projection can occur at the ground track start or end
            s=-1*(gdf.geometry[len(gdf)-1].x)-20
            nx=[ko.x for ko in pr.geometry]
            if all (lon<s for lon in nx):
                pass
            else:
                pr['geometry']=pr['geometry'].apply(lambda r: Point(r.x+360,r.y) if(r.x<s) else Point(r.x,r.y))
        elif qsr==True and cpe=="st":
            s= gdf.geometry[len(gdf)-1].x-20
            nx=[ko.x for ko in pr.geometry]
            if all (lon>s for lon in nx):
                pass
            else:
                pr['geometry']=pr['geometry'].apply(lambda r: Point(r.x+360,r.y) if(r.x<s) else Point(r.x,r.y))
        elif qsr==False:
            s=gdf.geometry[len(gdf)-1].x-20
            pr['geometry']=pr['geometry'].apply(lambda r: Point(r.x+360,r.y) if(r.x<s) else Point(r.x,r.y))


        total=Polygon(pr.geometry)
        ref=Polygon([Point(180.5,90),Point(540,90),Point(540,-90),Point(180.5,-90)])

        neg=ref.intersection(total)
        r_po=Polygon([Point(180,90),Point(-180,90),Point(-180,-90),Point(180,-90)])
        po= r_po.intersection(total)

        if neg.is_empty:
            fl=gpd.GeoDataFrame({'geometry':[po]},crs="EPSG:4326")
        else:
            x,y=neg.exterior.coords.xy
            x=[x[i]-360 for i in range(len(x))]
            tr_ne=[Point(x[i],y[i]) for i in range(len(x))]
            neg=Polygon(tr_ne)
            hj= unary_union([neg,po])
            fl=gpd.GeoDataFrame({'geometry':[hj]},crs="EPSG:4326")
    if ty=="Pro":
        if qsr==True and cpe=='nd':
            s=-1*(gdf.geometry[len(gdf)-1].x)+20
            nx=[ko.x for ko in pr.geometry]
            if all (lon>s for lon in nx):
                pass
            else:
                pr['geometry']=pr['geometry'].apply(lambda r: Point(r.x+360,r.y) if(r.x<s) else Point(r.x,r.y))
        elif qsr==True and cpe=='st':
            s=-1*(gdf.geometry[len(gdf)-1].x)-20
            nx=[ko.x for ko in pr.geometry]
            if all (lon<s for lon in nx):
                pass
            else:
                pr['geometry']=pr['geometry'].apply(lambda r: Point(r.x+360,r.y) if(r.x<s) else Point(r.x,r.y))
        elif qsr==False:
            s=gdf.geometry[len(gdf)-1].x+20
            pr['geometry']=pr['geometry'].apply(lambda r: Point(r.x+360,r.y) if(r.x<s) else Point(r.x,r.y))
        total=Polygon(pr.geometry)
        ref=Polygon([Point(180.5,90),Point(540,90),Point(540,-90),Point(180,-90)])
        neg=ref.intersection(total)
        r_po=Polygon([Point(180,90),Point(-180,90),Point(-180,-90),Point(180,-90)])
        po= r_po.intersection(total)

        if neg.is_empty:
            fl=gpd.GeoDataFrame({'geometry':[po]},crs="EPSG:4326")
        else:
            x,y=neg.exterior.coords.xy
            x=[x[i]-360 for i in range(len(x))]
            tr_ne=[Point(x[i],y[i]) for i in range(len(x))]
            neg=Polygon(tr_ne)
            hj= unary_union([neg,po])
            fl=gpd.GeoDataFrame({'geometry':[hj]},crs="EPSG:4326")
    return fl
def cut_geometry(x,sw,mt,gdf,ty,qsr,cpe):
    """
    cut_geometry cuts the polygon into two.
    Args:
        :param x: list of points (mirrored 360)
    Returns:
        :param gdf: geodataframe with coverage area polygon
    """

    lin= LineString(x)
    lin=lin.buffer(sw)
    x,y= lin.exterior.coords.xy
    cv=[Point(x[i],y[i]) for i in range(len(x))]
    pr=gpd.GeoDataFrame({'geometry': cv},crs="EPSG:"+mt)
    pr=pr.to_crs("EPSG:4326")
    fl1=cutter(pr,gdf,ty,qsr,cpe)

    return fl1
def quick_search(tt,sw):
    """
    quick_search: quickly searches if initial and end point projections are likely
    to cross the antimeridian. It will save time for points that won't cross the atimeridian'
    Args:
        tt: Geodataframe in cylindrical coordinates
        sw: swath width
    Returns:
        Boolean: True or False
    """
    cut=False
    lim=4
    cpe='None'
    if  tt.geometry[0].x<0:
        thread=-2e7+lim*sw #sw here equal to half of the swath width
        if tt.geometry[0].x<thread:
            cut=True
            cpe='st'
    else:
        thread=2e7-lim*sw
        if tt.geometry[0].x>thread:
            cut=True
            cpe='st'
    if  tt.geometry[len(tt)-1].x<0:
        thread=-2e7+lim*sw #sw here equal to half of the swath width
        if tt.geometry[len(tt)-1].x<thread:
            cut=True
            cpe='nd'
    else:
        thread=2e7-lim*sw
        if tt.geometry[len(tt)-1].x>thread:
            cut=True
            cpe='nd'
    return cut,cpe

def line_string(gdf,mt,sw):
    '''
    Provides area of coverage using the line string method.
    --------
    Inputs:
    :param gdf: Geodataframe (geodetic coordinates) with ground track points.
    :param mt: cylindrical projection "4087".
    :param sw: half of swath width (sw/2).

    Output:
        gdf: Geodataframe with the area of coverage as a multipolygon
    '''
    cut=False
    qsr=False
    cpe='None'
    for i in range(len(gdf)-1):
        dd=np.abs(gdf.geometry[i].x) +gdf.geometry[i+1].x
        dd1=gdf.geometry[i].x +np.abs(gdf.geometry[i+1].x)

        if gdf.geometry[i].x<0 and gdf.geometry[i+1].x>0 and dd>90:
            cut=True

        if gdf.geometry[i].x>0 and gdf.geometry[i+1].x<0 and dd1>90:
            cut=True
    ty=orbit_type(gdf)


    tt= gdf.to_crs("EPSG:"+mt)
    if ty=="Pro":
        fs=tt.geometry[0].x
        tt['geometry']= tt.geometry.apply(lambda r: Point(r.x+4e7,r.y)if (r.x<fs and cut==True) else Point(r.x, r.y))
        x=tt.geometry
        if cut:
            fl1=cut_geometry(x,sw,mt,gdf,ty,qsr,cpe)

        else:
            qsr,cpe=quick_search(tt,sw)
            if qsr:
                fl1=cut_geometry(x,sw,mt,gdf,ty,qsr,cpe)
            else:
                lin= LineString(x)
                lin=lin.buffer(sw)
                fl1=gpd.GeoDataFrame({'geometry':[lin]},crs="EPSG:"+mt).to_crs("EPSG:4326")
    if ty=="Re":
        fs=tt.geometry[0].x
        lst=tt.geometry[len(tt)-1].x

        tt['geometry']= tt.geometry.apply(lambda r: Point(r.x+4e7, r.y) if (r.x<lst and cut==True) else Point(r.x,r.y))
        x= tt.geometry
        if cut:

            fl1=cut_geometry(x,sw,mt,gdf,ty,qsr,cpe)
        else:
            qsr,cpe=quick_search(tt,sw)
            if qsr:
                fl1=cut_geometry(x,sw,mt,gdf,ty,qsr,cpe)
            else:
                lin= LineString(x)
                lin=lin.buffer(sw)
                fl1=gpd.GeoDataFrame({'geometry':[lin]},crs="EPSG:"+mt).to_crs("EPSG:4326")
    return fl1
