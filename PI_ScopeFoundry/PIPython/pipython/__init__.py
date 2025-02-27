#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of libraries to use PI controllers and process GCS data."""

from PI_ScopeFoundry.PIPython.pipython.pidevice import GCS2Device, GCS21Device, GCS2Commands, GCS21Commands
from PI_ScopeFoundry.PIPython.pipython.pidevice import GCSDevice
from PI_ScopeFoundry.PIPython.pipython.pidevice import gcserror
from PI_ScopeFoundry.PIPython.pipython.pidevice.gcserror import GCSError


#from PIPython.pipython.pidevice import GCS2Device, GCS21Device, GCS2Commands, GCS21Commands
#from PIPython.pipython.pidevice import GCSDevice
#from PIPython.pipython.pidevice import gcserror
#from PIPython.pipython.pidevice.gcserror import GCSError
__all__ = ['GCSDevice', 'GCS2Device', 'GCS21Device', 'GCS2Commands', 'GCS21Commands']

__version__ = '2.1.1.2'
__signature__ = 0x8f8860f2b9455c2537de2645ee76d840
