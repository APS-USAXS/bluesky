"""
define a custom NeXus file writer base for uascan raw data files

See ``instrument.utils.setup_new_user.newFile()``
to replace ``instrument.framework.callbacks.newSpecFile()``
"""

__all__ = [
    # "NXWriterFlyScan",    # not yet tested
    "NXWriterUascan",
    # "NXWriterSaxsWaxs",    # not yet tested
]

import logging

logger = logging.getLogger(__name__)
logger.info(__file__)

import datetime
import os

import numpy as np
from apstools.callbacks import NXWriterAPS

from ..devices import terms
from ..devices.user_data import user_data
from ..utils.cleanup_text import cleanupText
from ..utils.setup_new_user import techniqueSubdirectory


class OurCustomNXWriterBase(NXWriterAPS):
    """
    customize the NXWriter for this instrument

    Structure of the NeXus/HDF5 file

    The HDF5 files are written according to the NeXus structure,
    using only NeXus base classes.  Here is a tree view of
    the structure, edited from an example uascan run::

        entry:NXentry
            # constants and links into bluesky subdirectories
            instrument:NXinstrument
                bluesky_metadata:NXnote
                    # each key in the ``start`` document
                    # structured data encoded here as YAML
                bluesky_streams:NXnote
                    # NXdata groups, one for each monitored signal
                monochromator:NXmonochromator
                    # links to baseline start values
                slits:NXnote
                    guard_slit:NXslit
                        # links to baseline start values
                    usaxs_slit:NXslit
                        # links to baseline start values
                source:NXsource
                    # constants and links to baseline start values
                undulator:NXinsertion_device
                    # constants and links to baseline start values
            sample:NXsample
                # links to metadata and baseline start values
    """

    instrument_name = "APS 12-ID-E USAXS"
    supported_plans = ("name", "the", "supported", "plans")
    file_extension = "h5"  # no dot
    config_version = "1.0"

    def write_entry(self):
        import apstools

        nxentry = super().write_entry()  # default technique
        logger.debug("write_entry of file: %s", self.root.attrs["file_name"])

        nxentry["program_name"].attrs["config_version"] = self.config_version
        nxentry["SPEC_data_file"] = self.get_stream_link("user_data_spec_file")
        nxentry["sample/thickness"] = self.get_stream_link("user_data_sample_thickness")
        nxentry["sample/name"] = self.get_sample_title()
        self.root.attrs["creator_version"] = apstools.__version__

    def write_monochromator(  # override NXWriterAPS
        self,
        parent,
        pre="monochromator_dcm",
        keys="wavelength energy theta".split(),  # <- removed: y_offset mode
    ):
        """
        group: /entry/instrument/monochromator:NXmonochromator
        """

        try:
            links = {key: self.get_stream_link(f"{pre}_{key}") for key in keys}
        except KeyError as exc:
            logger.warning("%s -- not creating monochromator group", str(exc))
            return

        pre = "monochromator"
        key = "feedback_on"
        try:
            links[key] = self.get_stream_link(f"{pre}_{key}")
        except KeyError as exc:
            logger.warning("%s -- feedback signal not found", str(exc))

        nxmonochromator = self.create_NX_group(parent, "monochromator:NXmonochromator")
        for k, v in links.items():
            nxmonochromator[k] = v
        return nxmonochromator

    def get_sample_title(self):
        """
        return the title for this sample
        """
        return self.get_stream_link("user_data_sample_title")

    def start(self, doc):
        "ensure we only collect data for plans we are prepared to handle"
        if doc.get("plan_name") in self.supported_plans:
            # pay attention to this run of documents
            super().start(doc)
            self.scanning = True
            path = techniqueSubdirectory("usaxs")
            fname = (
                f"{cleanupText(user_data.sample_title.get())}"
                f"_{terms.FlyScan.order_number.get():04d}"
                ".h5"
            )
            self.file_name = os.path.join(path, fname)
        else:
            self.scanning = False
            self.file_name = None

    def writer(self):
        "write the data if this plan is supported"
        plan = self.metadata.get("plan_name")
        if plan not in self.supported_plans:
            return

        super().writer()

    def write_stream_internal(self, parent, d, subgroup, stream_name, k, v):
        subgroup.attrs["signal"] = "value"
        subgroup.attrs["axes"] = [
            "time",
        ]
        if isinstance(d, list) and len(d) > 0:
            if v["dtype"] in ("string",):
                d = self.h5string(d)
            elif v["dtype"] in ("integer", "number"):
                d = np.array(d)
        try:
            ds = subgroup.create_dataset("value", data=d)
            ds.attrs["target"] = ds.name
            try:
                self.add_dataset_attributes(ds, v, k)
            except Exception as exc:
                logger.error("%s %s %s %s", v["dtype"], type(d), k, exc)
        except TypeError as exc:
            logger.error("%s %s %s %s", v["dtype"], k, f"TypeError({exc})", v["data"])
        if stream_name == "baseline":
            # make it easier to pick single values
            # identify start&end of acquisition individually
            for key, item in dict(value_start=0, value_end=-1).items():
                try:
                    ds = subgroup.create_dataset(key, data=d[item])
                    self.add_dataset_attributes(ds, v, k)
                    ds.attrs["target"] = ds.name
                except TypeError as exc:
                    raise UnicodeError(
                        f"Could not write '{d[item]}' to h5py from baseline:"
                        f" k={k}, v={v}, key={key}"
                        f"\n{exc}"
                    )

    def h5string(self, text):
        """Local fix for issue #459."""
        if isinstance(text, (tuple, list)):
            return [self.h5string(str(t)) for t in text]
        text = text or ""
        return text.encode("utf8")


class NXWriterFlyScan(OurCustomNXWriterBase):

    supported_plans = ("Flyscan",)

    def write_streams(self, parent):
        "write all bluesky document streams in this run"
        bluesky = super().write_streams(parent)

        if "primary" not in bluesky and "mca" in bluesky:
            # link the two
            bluesky["primary"] = bluesky["mca"]

        return bluesky


class NXWriterSaxsWaxs(OurCustomNXWriterBase):
    """
    writes NeXus data file from USAXS instrument SAXS & WAXS area detector scans
    """

    supported_plans = (
        "SAXS",
        "WAXS",
    )

    def getResourceFile(self, resource_id):
        """
        full path to the resource file specified by uid ``resource_id``

        override in subclass as needed
        """
        # logger.debug(self.__class__.__name__)
        fname = super().getResourceFile(resource_id)
        # logger.debug("before: %s", fname)
        fname = os.path.abspath(fname)
        key = "/mnt/usaxscontrol/USAXS_data/"
        revision = "/share1/USAXS_data/"
        if fname.startswith(key):
            fname = revision + fname[len(key) :]
        # logger.debug("after: %s", fname)
        return fname


class NXWriterUascan(OurCustomNXWriterBase):
    """
    write raw uascan data to a NeXus/HDF5 file, no specific application definition
    """

    # TODO: identify what additional data is needed to collect
    # add RE.md["detectors"] = list : first item is for NXdata @signal attribute
    # add RE.md["positioners"] = list : entire list is for NXdata @axes attribute

    nxdata_signal = "PD_USAXS"
    nxdata_signal_axes = [
        "a_stage_r",
    ]
    supported_plans = ("uascan",)

    # convention: methods written in alphabetical order

    def save_reduced_as_nxdata(self, addr, data):
        """Save the reduced ``data`` to NXdata group ``key``."""
        nxdata = self.root.create_group(addr)
        nxdata.attrs["NX_class"] = "NXdata"
        nxdata.attrs["Q_indices"] = 0
        nxdata.attrs["axes"] = "Q"
        nxdata.attrs["signal"] = "R"
        nxdata.attrs["timestamp"] = str(datetime.datetime.now())

        for k, v in data.items():
            nxdata.create_dataset(k, data=v)
        nxdata["Q"].attrs["units"] = "1/A"
        nxdata["R"].attrs["units"] = "none"

    def write_entry(self):
        "Write reduced SAXS data from here."
        super().write_entry()  # write the raw data

        # https://github.com/APS-USAXS/usaxs-bluesky/issues/588
        logger.info("DIAGNOSTIC: this is when to write reduced 1-D data")
        logger.info("DIAGNOSTIC: HDF5 file='%s'", self.root.filename)
        logger.info("DIAGNOSTIC: Is HDF5 file open? %s", self.root.id.valid == 1)
        if self.root.id.valid == 1:
            logger.info("DIAGNOSTIC: HDF5 file access mode=%s", self.root.mode)

        try:
            from .calculate_reduced_data import reduce_uascan

            data = reduce_uascan(self.root)
            h5_address = "/entry/uascan_reduced_full"
            logger.info("TODO: save reduced uascan data to group: %s", h5_address)
            self.save_reduced_as_nxdata(h5_address, data)
        except Exception as exinfo:
            logger.warning("Did not write reduced uascan data: %s", exinfo)

    def write_slits(self, parent):
        """
        group: /entry/instrument/slits:NXnote/SLIT:NXslit
        """
        group = self.create_NX_group(parent, f"slits:NXnote")
        for pre in "guard_slit usaxs_slit".split():
            slit = self.create_NX_group(group, f"{pre}:NXslit")
            slit["x_gap"] = self.get_stream_link(f"{pre}_h_size")
            slit["y_gap"] = self.get_stream_link(f"{pre}_v_size")
            for key in "x y".split():
                slit[key] = self.get_stream_link(f"{pre}_{key}")
