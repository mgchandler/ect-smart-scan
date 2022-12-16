# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 10:14:40 2022

@author: mc16535

(v1) Script for the movement of the Zaber translation stage.
Essentially just a copy-and-paste of Zaber's example script, with automatic
working out which port the device is connected to.

N.B. in device_list, device 0 is the z-axis, device 1 is the y-axis and device
2 is the x-axis.
"""
import handyscope as hs
import helpers as h
import libtiepie as ltp
import matplotlib.pyplot as plt
import numpy as np
import sys
import time
import trajectory as traj
import warnings
from zaber_motion import Library
from zaber_motion.ascii import Connection

# Enables script to be imported for use in other scripts
if __name__ == "__main__":
    try:
        com = h.get_port()
    except RuntimeError:
        warnings.warn("Zaber port not found - proceeding without")
    
    # Update devices from internet
    try:
        Library.enable_device_db_store()
    except NotImplementedError:
        pass #TODO: Demand local storage of device database
    
    # ltp.network.auto_detect_enabled = True
    ltp.device_list.update()
    
    gen_freq = 13e6
    sample_freq = 1e9
    record_length = 1e6
    
    with hs.Handyscope(gen_freq, 0.1, sample_freq, record_length, 4, output_active_channels=0) as handyscope:
        np_data = np.asarray(handyscope.get_record())
        t = np.linspace(0, (record_length-1) / sample_freq, record_length)
        
        plt.plot(t * 1e6, np_data[0, :])
        plt.xlabel("Time (us)")
        plt.ylabel("Voltage (V)")
        plt.show()
        
        t_data   = []
        rms_data = []
        start_time = time.time_ns()*10**-9
        try:
            while True:
                # gen_freq = 13e6
                # n_cycles = 10
                # n_samples_per_cycle = 50
                # sample_freq = int(gen_freq * n_samples_per_cycle)
                # record_length = int(n_cycles * sample_freq / gen_freq) + 1
                
                # handyscope.new_params(input_frequency=gen_freq, output_sample_frequency=sample_freq, output_record_length=record_length)
                np_data = np.asarray(handyscope.get_record())
                t_data.append(time.time_ns()*10**-9 - start_time)
                rms_val = np.sqrt(np.mean(np_data[0, :]**2))
                print(rms_val)
                rms_data.append(rms_val)
                
                plt.plot(t * 1e6, np_data[0, :])
                plt.xlabel("Time (us)")
                plt.ylabel("Voltage (V)")
                plt.show()
        except KeyboardInterrupt:
            plt.plot(t_data, rms_data)
            raise KeyboardInterrupt