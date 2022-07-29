# -*- coding: utf-8 -*-
"""
Object schemas for instruments.

@author: Paul T. Grogan <pgrogan@stevens.edu>
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, confloat
from datetime import timedelta
import pandas as pd
from skyfield.api import load, wgs84, EarthSatellite
from shapely.geometry import Point

from ..utils import compute_orbit_period


class DutyCycleScheme(str, Enum):
    """
    Representation of duty cycle informaton
    """
    fixed = "fixed"
    opportunistic = "opportunistic"


class Instrument(BaseModel):
    """
    Representation of a remote sensing instrument.

    :param name: Name of this instrument
    :type  name: str
    :param field_of_regard: Angular field (degrees) of possible observations (with pointing).
    :type field_of_regard: float (0 to 360), default: 180
    :param min_access_time: Minimum access (integration) time to record an observation.
    :type min_access_time: :class:`datetime.timedelta`, default: 0
    :param req_self_sunlit: Option to set the required instrument sunlit state for observation.
    :type req_self_sunlit: bool, optional, default: None
    :param req_target_sunlit: Option to set the required target sunlit state for observation.
    :type req_target_sunlit: bool, optional, default: None
    :param duty_cycle: Fraction of orbit the instrument is operational.
    :type duty_cycle: :class:`pydantic.confloat`, default: 1
    :param duty_cycle_scheme: Scheme for duty cycling instrument (default: fixed)
    :type duty_cycle_scheme: :class:`tatc.schemas.instrument.DutyCycleScheme`, default: fixed
    """

    name: str = Field(..., description="Name of this instrument.")
    field_of_regard: float = Field(
        180,
        description="Angular field (degrees) of possible observations (with pointing).",
        gt=0,
        le=360,
        example=50,
    )
    min_access_time: timedelta = Field(
        timedelta(0),
        description="Minimum access (integration) time to record an observation.",
        example=timedelta(seconds=10),
    )
    req_self_sunlit: Optional[bool] = Field(
        None,
        description="Option to set the required instrument sunlit state for observation.",
    )
    req_target_sunlit: Optional[bool] = Field(
        None,
        description="Option to set the required target sunlit state for observation.",
    )
    duty_cycle: confloat(ge=0, le=1) = Field(
        1, description="Fraction of orbit the instrument is operational."
    )
    duty_cycle_scheme: Optional[DutyCycleScheme] = Field(
        DutyCycleScheme.fixed,
        description="Scheme for duty cycling instrument (default: fixed).",
    )

    def is_valid_observation(self, eph, time, position):
        """Determines if an instrument can provide a valid observations.

        :param eph: Planetary ephemerides (Skyfield).
        :type eph: :obj:`SpiceKernel`
        :param time: Observation time (Skyfield).
        :type time: :obj:`Time`
        :param position: Instrument geocentric position (Skyfield).
        :type position: :obj:`Geocentric`
        :return: True if instrument can provide valid observations, otherwise False
        :rtype: bool
        """
        if self.req_target_sunlit is not None:
            subpoint = wgs84.subpoint(position)
            solar_obs = (
                (eph["earth"] + subpoint).at(time).observe(eph["sun"]).apparent()
            )
            solar_alt, solar_az, solar_dist = solar_obs.altaz()
            if self.req_target_sunlit != (solar_alt.degrees > 0):
                return False
        if self.req_self_sunlit is not None:
            if self.req_self_sunlit != position.is_sunlit(eph):
                return False
        return True

    def generate_ops_intervals(self, eph, ts, sat, times, target_region=None):
        """Generate intervals when this instrument is operational.

        :param eph: Planetary ephemerides (Skyfield).
        :type eph: :obj:`SpiceKernel`
        :param ts: Timescale (Skyfield).
        :type ts: :obj:`Timescale`
        :param sat: Satellite hosting this instrument (Skyfield).
        :type sat: :obj:`EarthSatellite`
        :param times: List of potential observation times.
        :type times list[:obj:`datetime.datetime`]
        :param target_region: Target region (default: None).
        :type target_region: :obj:`Polygon` or :obj:`MultiPolygon`
        :returns: The intervals when the instrument is operational
        :rtype: :obj:`DataFrame`
        """
        if self.duty_cycle >= 1:
            return pd.Series(
                [pd.Interval(pd.Timestamp(times[0]), pd.Timestamp(times[-1]), "both")]
            )
        else:
            # determine operational/non-operational periods based on duty cycle
            satellite_height = wgs84.subpoint(sat.at(ts.utc(times[0]))).elevation.m
            orbit_period = timedelta(seconds=compute_orbit_period(satellite_height))
            ops_duration = orbit_period * self.duty_cycle
            no_ops_duration = orbit_period - ops_duration

            if self.duty_cycle_scheme == DutyCycleScheme.fixed:
                # return list of intervals with fixed ops/no-ops periods
                return pd.Series(
                    pd.date_range(
                        times[0], times[-1], freq=f"{orbit_period.total_seconds()}S"
                    )
                ).apply(lambda r: pd.Interval(r, r + ops_duration, "both"))
            elif self.duty_cycle_scheme == DutyCycleScheme.opportunistic:
                # construct list of intervals based on opportunistic observation
                ops_intervals = pd.Series([], dtype="interval")
                # pre-compute skyfield times, positions, and subpoints
                ts_times = [ts.from_datetime(time) for time in times]
                positions = [sat.at(time) for time in ts_times]
                subpoints = [wgs84.subpoint(position) for position in positions]
                # loop over each supplied time
                for i, time in enumerate(times):
                    if (
                        self.is_valid_observation(eph, ts_times[i], positions[i])
                        and (
                            target_region is None
                            or target_region.contains(
                                Point(
                                    subpoints[i].longitude.degrees,
                                    subpoints[i].latitude.degrees,
                                )
                            )
                        )
                        and (
                            len(ops_intervals.index) == 0
                            or ops_intervals.iloc[-1].right + no_ops_duration <= time
                        )
                    ):
                        # create a new interval if:
                        #   1) valid observations
                        #   2) within target observation region
                        #   3) either first operational interval or follows
                        #      required no-ops period
                        ops_intervals = ops_intervals.append(
                            pd.Series(pd.Interval(time, time + ops_duration, "both"))
                        )
                return ops_intervals
