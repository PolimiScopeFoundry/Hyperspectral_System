#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of libraries to use PI controllers and process GCS data."""

from . import gcserror
from .gcserror import GCSError

try:
    from .gcs2.gcs2commands import GCS2Commands
except ImportError:
    GCS2Commands = None

try:
    from .gcs2.gcs2device import GCS2Device
except ImportError:
    GCS2Device = None

try:
    from .gcs21.gcs21commands import GCS21Commands
except ImportError:
    GCS21Commands = None

try:
    from .gcs21.gcs21device import GCS21Device
except ImportError:
    GCS21Device = None

from .gcsdevice import GCSDevice


__all__ = ['GCSDevice', 'GCS2Device', 'GCS21Device', 'GCS2Commands', 'GCS21Commands']

__signature__ = 0x2139516246e921a2bd0b9e1f1355a851
