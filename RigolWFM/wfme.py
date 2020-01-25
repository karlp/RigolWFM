#pylint: disable=invalid-name
#pylint: disable=too-many-instance-attributes

"""
Extract signals or description from Rigol 1000E Oscilloscope waveform file.

Use like this::

    import RigolWFM.wfme as wfme

    channels = wfme.parse("filename.wfm")
    for ch in channels:
        print(ch)
"""

import tempfile
import requests
import numpy as np

import RigolWFM.wfm1000e


def engineering_string(number):
    """Format number with proper prefix"""
    absnr = abs(number)

    if absnr == 0:
        engr_str = '%g ' % (number / 1e-12)
    elif absnr < 0.99999999e-9:
        engr_str = '%g p' % (number / 1e-12)
    elif absnr < 0.99999999e-6:
        engr_str = '%g n' % (number / 1e-9)
    elif absnr < 0.99999999e-3:
        engr_str = '%g µ' % (number / 1e-6)
    elif absnr < 0.99999999:
        engr_str = '%g m' % (number / 1e-3)
    elif absnr < 0.99999999e3:
        engr_str = '%g ' % (number)
    elif absnr < 0.99999999e6:
        engr_str = '%g k' % (number / 1e3)
    elif absnr < 0.999999991e9:
        engr_str = '%g M' % (number / 1e6)
    else:
        engr_str = '%g G' % (number / 1e9)
    return engr_str


class Channel():
    """Base class for a single channel."""

    def __init__(self):
        self.channel_number = 1
        self.enabled = False
        self.volt_scale = 1    # s/div
        self.volt_offset = 0   # s
        self.time_scale = 1    # s/div
        self.time_delta = 0.1  # s
        self.time_offset = 0   # s
        self.points = 0
        self.raw = None

    def __str__(self):
        s = "Channel %d\n" % self.channel_number
        s += "    Enabled:   %s\n" % self.enabled
        s += "    Roll Stop: %s\n" % self.roll_stop
        s += "    Voltage:\n"
        s += "        Scale  = " + engineering_string(self.volt_scale) + "V/div\n"
        s += "        Offset = " + engineering_string(self.volt_offset) + "V\n"
        s += "    Time:\n"
        s += "        Scale  = " + engineering_string(self.time_scale) + "s/div\n"
        s += "        Delay  = " + engineering_string(self.time_offset) + "s\n"
        s += "        Delta  = " + engineering_string(self.time_per_point) + "s/point\n"
        s += "    Data:\n"
        s += "        Points = %d\n" % self.points
        if self.enabled:
            s += "        Raw    = [%9d,%9d,%9d  ... %9d,%9d]\n" % (
                self.raw[0], self.raw[1], self.raw[2], self.raw[-2], self.raw[-1])
            v = [engineering_string(self.volts[i])+"V" for i in [0,1,2,-2,-1]]
            s += "        Volts  = [%9s,%9s,%9s  ... %9s,%9s]\n" % (v[0],v[1],v[2],v[3],v[4])
            t = [engineering_string(self.times[i])+"s" for i in [0,1,2,-2,-1]]
            s += "        Times  = [%9s,%9s,%9s  ... %9s,%9s]\n" % (t[0],t[1],t[2],t[3],t[4])
        return s


class ChannelE(Channel):
    """Base class for a single channel from 1000E series scopes."""

    def __init__(self, w, ch=1):
        super().__init__()
        self.channel_number = ch
        self.roll_stop = w.header.roll_stop
        self.time_per_point = 1/w.header.sample_rate

        if ch == 1:
            self.enabled = w.header.ch1.enabled
            self.volts_per_division = w.header.ch1_volts_per_division
            self.volts_offset = w.header.ch1_volts_offset
            self.time_offset = w.header.ch1_time_delay
            self.time_scale = w.header.ch1_time_scale
            self.points = w.header.ch1_points
            if self.enabled:
                self.raw = np.array(w.data.ch1)
                self.volts = self.volts_per_division * (5.0 - self.raw/25.0) - self.volts_offset
                self.times  = np.arange(self.points) * self.time_per_point

                
        elif ch == 2:
            self.enabled = w.header.ch2.enabled
            self.volts_per_division = w.header.ch2_volts_per_division
            self.volts_offset = w.header.ch2_volts_offset
            self.time_offset = w.header.ch2_time_delay
            self.time_scale = w.header.ch2_time_scale
            self.points = w.header.ch2_points
            if self.enabled:
                self.raw = np.array(w.data.ch2)
                self.volts = self.volts_per_division * (5.0 - self.raw/25.0) - self.volts_offset
                self.times  = np.arange(self.points) * self.time_per_point


class ReadWFMError(Exception):
    """Generic Read Error."""


class ParseWFMError(Exception):
    """Generic Parse Error."""


def parse(wfm_filename):
    """Return a list of channels."""

    channels = [None, None]

    try:
        w = RigolWFM.wfm1000e.Wfm1000e.from_file(wfm_filename)
        channels = [ChannelE(w, i) for i in [1,2]]
        return channels

    except:
        raise ParseWFMError("File format is not 1000E.  Sorry.")

    return channels
