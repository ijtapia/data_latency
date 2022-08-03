# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 13:21:31 2022
Generates space artchitectures: constellation and ground station network
@author: Josue Tapia 
"""

from tatc_o.schemas.point import GroundStation
from tatc_o.schemas.satellite import Satellite, WalkerConstellation
from tatc_o.schemas.instrument import Instrument
from tatc_o.schemas.orbit import TwoLineElements
from tatc_o.schemas.point import Point

import datetime as dt
from datetime import timezone
import time
from datetime import datetime, timedelta

def get_aws_network():
    """ 
    This function stores the AWS ground station network
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
    aws_network=[gr1, gr2, gr3, gr4, gr5, gr6, gr7, gr8, gr9, gr10]
    
    return aws_network

def add_gr_network():
    """"
    This function stores additional ground stations
    """
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

    """

    add_network=[GroundStation( name= "New Delhi",
                                latitude= 28.6139,
                                longitude= 77.209,
                                min_elevation_angle=25,
                                min_access_time=10
            ),
            GroundStation( name= "Manila",
                                latitude= 14.599,
                                longitude= 120.98,
                                min_elevation_angle=25,
                                min_access_time=10),
            GroundStation( name= "Fortaleza",
                                latitude= -3.73,
                                longitude= -38.52,
                                min_elevation_angle=25,
                                min_access_time=10),
            GroundStation( name= "New Zealand",
                                latitude= -40.9,
                                longitude= 174.88,
                                min_elevation_angle=25,
                                min_access_time=10),
            GroundStation(name= "Wallops",
                                latitude = 37.94,
                                longitude = -75.46,
                                min_elevation_angle = 25,
                                min_access_time= 10)
        ]

    return add_network

def generate_constellation(_for,n_satellites, n_planes):
    ins=Instrument(name= "Scon1",
         field_of_regard=_for,
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
    
    constellation_base= WalkerConstellation(
        name= "ISS_Constellation",
        type='walker',
        configuration= 'delta',
        instruments=[ins],
        orbit= sat1.orbit,
        number_satellites= n_satellites,
        number_planes= n_planes,
        relative_spacing= 0.1
        ).generate_members() #assumes 0 drag coeff.

    return constellation_base
        


