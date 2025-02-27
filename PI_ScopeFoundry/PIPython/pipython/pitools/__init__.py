#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Collection of interfaces to PI controllers."""

# Wildcard import pitools pylint: disable=W0401
# Redefining built-in 'basestring' pylint: disable=W0622
# Redefining built-in 'open' pylint: disable=W0622
from .pitools import *

try:
    # Wildcard import pipython.gcs2.gcs2pitools pylint: disable=W0401
    from pipython.pidevice.gcs2.gcs2pitools import *
except ImportError:
    pass

try:
    # Wildcard import pipython.gcs21.gcs21pitools pylint: disable=W0401
    from pipython.pidevice.gcs21.gcs21pitools import *
except ImportError:
    pass

__signature__ = 0x36264f902d0083987d58017b0395ac43
