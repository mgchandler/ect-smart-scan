# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 15:30:00 2022

@author: mc16535

A file containing helper functions for ect-smart-scan, which do not belong in
any other file. Should consist of short, easily read functions, rather than
anything too much more extensive.
"""
import csv
import libtiepie as ltp
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import os
from serial.tools.list_ports import comports
from zaber_motion import Units
import yaml

def get_port(manufacturer="FTDI"):
    """
    Returns the port which the device of interest is connected to. Serial does
    not guarantee that comports() returns ports in order, thus we sort by port.
    It is assumed that only one connection is available, thus the first one is
    returned; if none available then RuntimeError raised.
    """
    ports = sorted(comports(), key=lambda port: port.device)
    for port in ports:
        if port.manufacturer == manufacturer:
            return port.device
    raise RuntimeError("Device cannot be found! Connect it and make sure drivers are installed.")

def velocity_units(length_units):
    """
    Returns the equivalent units of velocity for the supplied length units.
    """
    if length_units == Units.LENGTH_METRES:
        return Units.VELOCITY_METRES_PER_SECOND
    elif length_units == Units.LENGTH_CENTIMETRES:
        return Units.VELOCITY_CENTIMETRES_PER_SECOND
    elif length_units == Units.LENGTH_MILLIMETRES:
        return Units.VELOCITY_MILLIMETRES_PER_SECOND
    elif length_units == Units.LENGTH_MICROMETRES:
        return Units.VELOCITY_MICROMETRES_PER_SECOND
    elif length_units == Units.LENGTH_NANOMETRES:
        return Units.VELOCITY_NANOMETRES_PER_SECOND
    elif length_units == Units.LENGTH_INCHES:
        return Units.VELOCITY_INCHES_PER_SECOND
    else:
        raise TypeError("Length units are invalid")

def find_gen(device_list):
    """
    Returns the index of the item in device_list which corresponds to a
    generator.
    """
    for idx, item in enumerate(device_list):
        if item.can_open(ltp.DEVICETYPE_GENERATOR):
            gen = item.open_generator()
            if gen.signal_types and ltp.ST_ARBITRARY:
                # del gen
                return idx
    return None

def find_scp(device_list):
    """
    Returns the index of the item in device_list which corresponds to a
    oscilloscope.
    """
    for idx, item in enumerate(device_list):
        if item.can_open(ltp.DEVICETYPE_OSCILLOSCOPE):
            scp = item.open_oscilloscope()
            if scp.measure_modes and ltp.MM_BLOCK:
                # del scp
                return idx
    return None

def rms(x):
    """
    Compute the root-mean-square of a numpy vector.
    """
    return np.sqrt(np.mean(np.asarray(x)**2))

def read_settings(filename):
    """
    Reads in settings from file, and assigns default values when not given.
    """
    # Redefine default_settings here in case it has been overwritten in the
    # past.
    default_settings = {
        "job":{
            # Loose requirement: name of scan, used for saving.
            "name":"TestScan",
        },
        "material":{
            # Loose requirement: not used at the moment.
            "name":"Aluminium",
        },
        # # All generator parameters are required.
        # "generator":{
        # 
        # },
        "oscilloscope":{
            # Loose requirement: method of data acquisition.
            "mode":"MM_BLOCK",
            # Optional: bit-resolution of the oscilloscope.
            "resolution":12,
            # Optional: channels on which measurements are taken.
            "active_channels":[-1],
            # Optional: kind of data to be captured on all channels.
            "coupling":"CK_ACV",
        },
        "trajectory":{
            # Optional: initial position of the x-axis. Set to the middle.
            "init_x":100,
            # Optional: initial position of the y-axis. Set to the middle.
            "init_y":0,
        },
    }
    with open(filename, 'r') as file:
        settings = yaml.safe_load(file)
    dict_merge(default_settings, settings)
    # default_settings now contains all the default values, plus everything
    # which has been overwritten by settings.
    return default_settings
    
def dict_merge(dict1, dict2):
    """
    Merge two dictionaries preserving sub-dictionaries contained within. Values
    from dict2 are merged into dict1, taking dict2's value over dict1's in
    conflicts.
    """
    for k, v in dict2.items():
        # Typical dictionary-merging behaviour is to overwrite the values in
        # dict1 with those in dict2. If the value is a dictionary, the entire
        # thing is overwritten rather than just duplicate terms. To preserve
        # values in dict1[k] which are not present in dict2[k], recursively
        # call dict_merge when we find a dictionary.
        if (k in dict1 and isinstance(dict1[k], dict) and isinstance(dict2[k], dict)):
            dict_merge(dict1[k], dict2[k])
        # Either we do not have a dictionary, or this item is not a dictionary
        # in dict1, thus we want to overwrite it anyway.
        else:
            dict1[k] = dict2[k]

def save_csv(filename, x, y, z, xunits="mm", yunits="mm", zlabel="RMS Voltage (V)", zaxis=None, ignore_long_z_warning=False):
    """
    Saves a csv of data.
    """
    x, y, z = np.squeeze(x), np.squeeze(y), np.squeeze(z).reshape(z.shape[0], -1)
    zlabel = np.asarray(zlabel)
    # Only check 0th dim of z as it may be 2D.
    if x.shape != y.shape and y.shape[0] != z.shape[0]:
        raise ValueError("x, y and z should all have broadcastable shapes.")
    
    if z.shape[1] != 1:
        if z.shape[1] != zaxis.shape[0]:
            raise ValueError("1st dim of z and zaxis must have the same shape.")
        if z.shape[1] > 10 and not ignore_long_z_warning:
            raise ValueError("zaxis is too large. If you meant to save more than 10, set ignore_long_z_warning=True")
        zlabel = np.char.add(zlabel, zaxis.astype(str))
        
    # Check if the file already exists.
    if os.path.isfile(f"{filename}.csv"):
        idx = 1
        while os.path.isfile(f"{filename} ({idx}).csv"):
            idx += 1
        filename += f" ({idx})"
    
    print(f"Saving {filename}.csv ...")
    with open(f"{filename}.csv", 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([f"x ({xunits})", f"y ({yunits})"] + ["{}".format(label) for label in zlabel])
        for idx in range(x.shape[0]):
            csvwriter.writerow([x[idx], y[idx]] + list(z[idx, :]))
            
def plot_data(filename, x, y, z, xunits="mm", yunits="mm", zlabel="RMS Voltage (V)"):
    """
    Saves a single figure.
    """
    x, y, z = np.squeeze(x), np.squeeze(y), np.squeeze(z)
    zlabel = np.asarray(zlabel)
    # z must have the same shape - call plot_data() multiple times if multiple z's required.
    if x.shape != y.shape and y.shape != z.shape:
        raise ValueError("x, y and z should all have broadcastable shapes.")
        
    # Check if the file already exists.
    if os.path.isfile(f"{filename}.png"):
        idx = 1
        while os.path.isfile(f"{filename} ({idx}).png"):
            idx += 1
        filename += f" ({idx})"
    
    # For plotting, if complex do absolute
    if z.dtype == complex:
        z = np.abs(z)
    fig = plt.figure(figsize=(8,6), dpi=100)
    ax = fig.add_axes([0.1, 0.1, 0.6, 0.8], projection='3d')
    graph = ax.scatter(x, y, z, c=z)
    ax.set_xlabel(f"x ({xunits})")
    ax.set_ylabel(f"y ({yunits})")
    ax.set_zlabel(zlabel)
    ax2 = fig.add_subplot(111)
    ax2.set_axis_off()
    fig.colorbar(graph, ax=ax2, label=zlabel)
    plt.savefig(f"{filename}.png")