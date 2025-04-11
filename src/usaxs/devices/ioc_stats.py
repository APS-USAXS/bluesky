"""
IOC statistics: synApps iocStats
"""

# TODO: optional, remove.
# fmt: off
__all__ = [
    "gp_stats",
    # "ad_stats",
]
# fmt: on

import logging

from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignalRO

logger = logging.getLogger(__name__)

logger.info(__file__)


class IocInfoDevice(Device):
    iso8601 = Component(EpicsSignalRO, "iso8601")
    uptime = Component(EpicsSignalRO, "UPTIME")
