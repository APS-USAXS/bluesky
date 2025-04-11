"""
Linkam temperature controllers
This is modified version of APS tools devices code
for new linkam TC1 version
++++++++++++++++++++++++++++++

.. autosummary::

   ~Linkam_T96_Device
"""

# from apstools.devices import PVPositionerSoftDoneWithStop
from apstools.devices import PVPositionerSoftDone
from ophyd import Component
from ophyd import Device
from ophyd import EpicsSignal
from ophyd import EpicsSignalRO
from ophyd import Signal


# this makes temperature to automatically start heating when changed
class T96Temperature(PVPositionerSoftDone):
    actuate = Component(EpicsSignal, "STARTHEAT", kind="config", string=True)
    actuate_value = "On"


class Linkam_T96_Device(Device):
    """
    Linkam model T96 temperature controller
    Linux ioc version

    EXAMPLE::

        tc1 = Linkam_T96("IOC:tc1:", name="tc1")

    to get temperature, ramprate etc:
    linkam_tc1.temperature.position which returns the current T in C

    """

    # use linkam.temperature.position to get the value, this is positoner...
    controller_name = "Linkam T96"
    temperature = Component(
        T96Temperature,
        "",
        readback_pv="TEMP",
        setpoint_pv="SETPOINT:SET",
        tolerance=1.0,
        kind="hinted",
    )
    ramprate = Component(
        PVPositionerSoftDone,
        "",
        readback_pv="RAMPRATE",
        setpoint_pv="RAMPRATE:SET",
        tolerance=1.0,
        kind="hinted",
    )
    units = Component(Signal, value="C", kind="config")
    controller_error = Component(EpicsSignalRO, "CTRLLR:ERR", kind="omitted")
    heater_power = Component(EpicsSignalRO, "POWER", kind="omitted")
    lnp_mode = Component(
        PVPositionerSoftDone,
        "",
        readback_pv="LNP_MODE",
        setpoint_pv="LNP_MODE:SET",
        # tolerance=1.0,
        kind="omitted",
    )
    lnp_speed = Component(
        PVPositionerSoftDone,
        "",
        readback_pv="LNP_SPEED",
        setpoint_pv="LNP_SPEED:SET",
        # tolerance=1.0,
        kind="omitted",
    )
    pressure = Component(EpicsSignalRO, "PRESSURE", kind="omitted")
    vacuum = Component(
        PVPositionerSoftDone,
        "",
        readback_pv="VACUUM",
        setpoint_pv="VACUUM:SET",
        # tolerance=1.0,
        kind="omitted",
    )
    humidity = Component(
        PVPositionerSoftDone,
        "",
        readback_pv="HUMIDITY",
        setpoint_pv="HUMIDITY:SET",
        # tolerance=1.0,
        kind="omitted",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # temperature component is the main value
        self.temperature.name = self.name
