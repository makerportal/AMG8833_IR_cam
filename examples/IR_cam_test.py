#######################################################
# Thermal camera Plotter with AMG8833 Infrared Array
#
# by Joshua Hrisko
#    Copyright 2021 | Maker Portal LLC
#
#######################################################
#
# load AMG8833 module first
import amg8833_i2c,time,sys
import numpy as np
import matplotlib.pyplot as plt
#
#####################################
# Initialization of Sensor
#####################################
#
t0 = time.time()
sensor = []
while (time.time()-t0)<1: # wait 1sec for sensor to start
    try:
        # AD0 = GND, addr = 0x68 | AD0 = 5V, addr = 0x69
        sensor = amg8833_i2c.AMG8833(addr=0x69) # start AMG8833
    except:
        sensor = amg8833_i2c.AMG8833(addr=0x68)
    finally:
        pass
time.sleep(0.1) # wait for sensor to settle

# If no device is found, exit the script
if sensor==[]:
    print("No AMG8833 Found - Check Your Wiring")
    sys.exit(); # exit the app if AMG88xx is not found 
#
#####################################
# Start and Format Figure 
#####################################
#
fig,ax = plt.subplots(figsize=(9,9)) # start figure
pix_res = (8,8) # pixel resolution
zz = np.zeros(pix_res) # set array with zeros first
im1 = ax.imshow(zz,vmin=15,vmax=30) # plot image, with temperature bounds
fig.canvas.draw() # draw figure

ax_bgnd = fig.canvas.copy_from_bbox(ax.bbox) # background for speeding up runs
fig.show() # show figure
#
#####################################
# Plot AMG8833 temps in real-time
#####################################
#
pix_to_read = 64 # read all 64 pixels
while True:
    status,pixels = sensor.read_temp(pix_to_read) # read pixels with status
    if status: # if error in pixel, re-enter loop and try again
        continue
    
    T_thermistor = sensor.read_thermistor() # read thermistor temp
    fig.canvas.restore_region(ax_bgnd) # restore background (speeds up run)
    im1.set_data(np.reshape(pixels,pix_res)) # update plot with new temps
    ax.draw_artist(im1) # draw image again
    fig.canvas.blit(ax.bbox) # blitting - for speeding up run
    fig.canvas.flush_events() # for real-time plot
    print("Thermistor Temperature: {0:2.2f}".format(T_thermistor)) # print thermistor temp
