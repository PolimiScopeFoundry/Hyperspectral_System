#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Provide a device, connected via the PI GCS DLL."""

from abc import  abstractmethod
from ..interfaces.gcsdll import GCSDll

__signature__ = 0x4f6edb735ac0a52f6ced70efcd08aea1


class GCSBaseDevice(object):
    """Provide a device connected via the PI GCS DLL or antoher gateway, can be used as context manager."""

    def __init__(self, devname='', gcsdll='', gateway=None):
        """Provide a device, connected via the PI GCS DLL or another 'gateway'.
        @param devname : Name of device, chooses according DLL which defaults to PI_GCS2_DLL.
        @param gcsdll : Name or path to GCS DLL to use, overwrites 'devname'.
        @type gateway : pipython.pidevice.interfaces.pigateway.PIGateway
        """
        self.dll = gateway or GCSDll(devname, gcsdll)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def dcid(self):
        """Get ID of current daisy chain connection as integer."""
        return self.dll.dcid

    @property
    def dllpath(self):
        """Get full path to GCS DLL."""
        return self.dll.dllpath

    @abstractmethod
    def close(self):
        """Close connection to device and daisy chain."""
        pass
