#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Provide GCS functions to control a PI device."""

from . import GCS2Commands
from . import GCS21Commands

try:
    from .gcs21 import gcs21commands_helpers
except ImportError:
    gcs21commands_helpers = None

__signature__ = 0x55f70ab0d505a59c802f6f998ef391ff


# Function name "GCSCommands" doesn't conform to snake_case naming style pylint: disable=C0103
def GCSCommands(gcsmessage=None, gcscommands=None):
    """Get instance of GCS2Commands or GCS21Commands dependent on the connected controller and on the availability
    of the GCS2Commnads and GCS21Commands class.
    Forcing a specific GCSxxCommand version is possible by 'gcscommands=GCS2Commnads' or 'gcscommnads=GCS21Commands'
    @param gcsmessage : pipython.pidevice.gcsmessages.GCSMessages
    @param gcscommands : None or pipython.pidevice.GCS2Commands or pipython.pidevice.GCS21Commands
    @return: Instance of GCS2Commnads or GCS21Commands
    """

    if not gcsmessage:
        raise TypeError("gcsmessage must not be 'None'")

    # if 'gcscommands != None' force the specific GCSxxCommands version
    if not gcscommands:
        if GCS2Commands and GCS21Commands and gcs21commands_helpers:
            # if both GCSxxCommand calsses ar available, use isgcs21 function to find out which if a GCS2 or GCS21
            # controller is connected and return an instance to the according class
            if gcs21commands_helpers.isgcs21(gcsmessage):
                gcscommands = GCS21Commands
            else:
                gcscommands = GCS2Commands
        elif GCS2Commands:
            # If only the GCS2Commands class is available returns an instance of GCS2Commands
            gcscommands = GCS2Commands
        elif GCS21Commands:
            # If only the GCS21Commands class is available returns an instance of GCS21Commands
            gcscommands = GCS21Commands

    if not gcscommands:
        # at this point gcscommands must not be None.
        raise TypeError("syntaxversion must be 'GCS2Commands' or 'GCS21Commands'")

    return gcscommands(gcsmessage)
