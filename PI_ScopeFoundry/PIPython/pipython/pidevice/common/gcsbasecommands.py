#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Provide GCS functions to control a PI device."""
# Trailing newlines pylint: disable=C0305

from abc import  abstractmethod
from logging import debug, warning
from .gcscommands_helpers import checksize

__signature__ = 0x1cb030d73b70221ecff15e8b1691138b

GCS1DEVICES = ('C-843', 'C-702.00', 'C-880', 'C-848', 'E-621', 'E-625', 'E-665', 'E-816', 'E-516',
               'C-663.10', 'C-863.10', 'MERCURY', 'HEXAPOD', 'TRIPOD', 'E-710', 'F-206', 'E-761')

class GCSBaseCommands(object):
    """Provide a gcs commands ."""

    def __init__(self, msgs):
        """Wrapper for PI GCS DLL.
        @type msgs : pipython.pidevice.gcsmessages.GCSMessages
        """
        debug('create an instance of GCSBaseCommands(msgs=%s)', str(msgs))
        self._msgs = msgs
        self._funcs = None
        self._name = None

    @property
    @abstractmethod
    def devname(self):
        """Return device name from its IDN string."""
        pass

    @devname.setter
    def devname(self, devname):
        """Set device name as string, only for testing."""
        self._name = str(devname)
        warning('controller name is coerced to %r', self._name)

    @devname.deleter
    def devname(self):
        """Reset device name."""
        self._name = None
        debug('GCSBaseCommands.devname: reset')

    @property
    def logfile(self):
        """Full path to file where to save communication to/from device."""
        return self._msgs.logfile

    @logfile.setter
    def logfile(self, filepath):
        """Full path to file where to save communication to/from device."""
        self._msgs.logfile = filepath

    @property
    def timeout(self):
        """Get current timeout setting in milliseconds."""
        return self._msgs.timeout

    @timeout.setter
    def timeout(self, value):
        """Set timeout.
        @param value : Timeout in milliseconds as integer.
        """
        self._msgs.timeout = int(value)

    # Method name "SetTimeout" doesn't conform to snake_case naming style pylint: disable=C0103
    def SetTimeout(self, value):
        """Set timeout to 'value' and return current value.
        DEPRECATED: Use GCSMessages.timeout instead.
        @param value : Timeout in milliseconds as integer.
        @return : Current timeout in milliseconds as integer.
        """
        timeout = self._msgs.timeout
        self._msgs.timeout = int(value)
        debug('DEPRECATED -- GCSBaseCommands.SetTimeout(value=%r): %r', value, timeout)
        return timeout

    @property
    @abstractmethod
    def funcs(self):
        """Return list of supported GCS functions."""
        pass

    @funcs.deleter
    def funcs(self):
        """Reset list of supported GCS functions."""
        debug('GCSBaseCommands.funcs: reset')
        self._funcs = None

    def _has(self, funcname):
        """Return True if connected controller supports the command that is called by 'funcname'.
        @param funcname : Case sensitive name of DLL function.
        @return : True if controller supports GCS command according to 'func'.
        """
        hasfunc = funcname in self.funcs
        debug('GCSBaseCommands.Has%s = %s', funcname, hasfunc)
        return hasfunc

    @property
    def bufstate(self):
        """False if no buffered data is available. True if buffered data is ready to use.
        Float value 0..1 indicates read progress. To wait, use "while self.bufstate is not True".
        """
        return self._msgs.bufstate

    @property
    def bufdata(self):
        """Get buffered data as 2-dimensional list of float values.
        Use "while self.bufstate is not True" and then call self.bufdata to get the data. (see docs)
        """
        return self._msgs.bufdata

    @property
    def connectionid(self):
        """Get ID of current connection as integer."""
        return self._msgs.connectionid

    def GetID(self):
        """Get ID of current connection as integer.
        DEPRECATED: Use GCS21Commands.connectionid instead.
        """
        return self._msgs.connectionid

    def GcsCommandset(self, tosend):
        """Send 'tosend' to device, there will not be any check for error.
        @param tosend : String to send to device, with or without trailing linefeed.
        """
        debug('GCSBaseCommands.GcsCommandset(%r)', tosend)
        checksize((1,), tosend)
        errcheck = self._msgs.errcheck
        self._msgs.errcheck = False
        self._msgs.send(tosend)
        self._msgs.errcheck = errcheck

    def send(self, tosend):
        """Send 'tosend' to device and check for error.
        @param tosend : String to send to device, with or without trailing linefeed.
        """
        debug('GCSBaseCommands.send(%r)', tosend)
        checksize((1,), tosend)
        self._msgs.send(tosend)

    def ReadGCSCommand(self, tosend):
        """Send 'tosend' to device, read answer, there will not be any check for error.
        @param tosend : String to send to device.
        @return : Device answer as string.
        """
        debug('2.ReadGCSCommand(%s)', tosend)
        checksize((1,), tosend)
        errcheck = self._msgs.errcheck
        self._msgs.errcheck = False
        answer = self._msgs.read(tosend)
        self._msgs.errcheck = errcheck
        debug('GCSBaseCommands.ReadGCSCommand = %r', answer)
        return answer

    def read(self, tosend):
        """Send 'tosend' to device, read answer and check for error.
        @param tosend : String to send to device.
        @return : Device answer as string.
        """
        debug('GCSBaseCommands.read(%s)', tosend)
        checksize((1,), tosend)
        answer = self._msgs.read(tosend)
        debug('GCSBaseCommands.read = %r', answer)
        return answer


    # GCS FUNCTIONS ### DO NOT MODIFY THIS LINE !!! ###############################################

    def qCSV(self):
        """Get the current GCS syntax version.
        @return : GCS version as float.
        """
        debug('GCSBaseCommands.qCSV()')
        answer = self._msgs.read('CSV?')
        value = float(answer.strip())
        debug('GCS2BaseCommands.qCSV = %r', value)
        return value

    def qIDN(self):
        """Get controller identification.
        @return : Controller ID as string with trailing linefeed.
        """
        debug('GCSBaseCommands.qIDN()')
        answer = self._msgs.read('*IDN?')
        debug('GCSBaseCommands.qIDN = %r', answer)
        return answer

    # CODEGEN BEGIN ### DO NOT MODIFY THIS LINE !!! ###############################################

    def HasqCSV(self):
        """Return True if qCSV() is available."""
        return self._has('qCSV')

    def HasqIDN(self):
        """Return True if qIDN() is available."""
        return self._has('qIDN')
