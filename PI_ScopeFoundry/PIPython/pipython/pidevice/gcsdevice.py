#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Provide a device, connected via the PI GCS DLL."""

# Cyclic import (pipython -> pipython.gcsdevice) pylint: disable=R0401
from . import GCS2Device
from . import GCS21Device

__signature__ = 0x9b5482cefb8a1100db9691b59a28814e


# Function name "GCSDevice" doesn't conform to snake_case naming style pylint: disable=C0103
def GCSDevice(devname='', gcsdll='', gateway=None, gcsdevice=None):
    """Get instance of the GCSDevice."""

    if not gcsdevice:
        if GCS2Device and GCS21Device:
            gcsdevice = GCS2Device
            #gcsdevice = GCS21Device
        elif GCS2Device:
            gcsdevice = GCS2Device
        elif GCS21Device:
            gcsdevice = GCS21Device

    if not gcsdevice:
        raise SyntaxError("syntaxversion must be 'GCS2Device' or 'GCS21Device'")

    return gcsdevice(devname, gcsdll, gateway)
