"""
USAXS Fly Scan trajectories
"""

__all__ = [
    "flyscan_trajectories",
]

import logging

from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal

logger = logging.getLogger(__name__)
logger.info(__file__)


class Trajectories(Device):
    """fly scan trajectories"""

    # ar = Component(EpicsSignal, "usxLAX:traj1:M1Traj")
    # ax = Component(EpicsSignal, "usxLAX:traj3:M1Traj")
    # dx = Component(EpicsSignal, "usxLAX:traj2:M1Traj")
    ar = Component(EpicsSignal, "usxAERO:pm1:M6Positions")
    ax = Component(EpicsSignal, "usxAERO:pm1:M4Positions")
    dx = Component(EpicsSignal, "usxAERO:pm1:M1Positions")
    # num_pulse_positions = Component(EpicsSignal, "usxLAX:traj1:NumPulsePositions")
    num_pulse_positions = Component(EpicsSignal, "usxAERO:pm1:NumPoints")


flyscan_trajectories = Trajectories(name="flyscan_trajectories")
