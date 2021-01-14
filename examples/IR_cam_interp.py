#######################################################
# Thermal camera Plotter with AMG8833 Infrared Array
# --- with interpolation routines for smoothing image
#
# by Joshua Hrisko
#    Copyright 2021 | Maker Portal LLC
#
#######################################################
#
import time,sys
sys.path.append('../')
# load AMG8833 module
import amg8833_i2c
import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
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
# Interpolation Properties 
#####################################
#
# original resolution
pix_res = (8,8) # pixel resolution
xx,yy = (np.linspace(0,pix_res[0],pix_res[0]),
                    np.linspace(0,pix_res[1],pix_res[1]))
zz = np.zeros(pix_res) # set array with zeros first
# new resolution
pix_mult = 6 # multiplier for interpolation 
interp_res = (int(pix_mult*pix_res[0]),int(pix_mult*pix_res[1]))
grid_x,grid_y = (np.linspace(0,pix_res[0],interp_res[0]),
                            np.linspace(0,pix_res[1],interp_res[1]))
# interp function
def interp(z_var):
    # cubic interpolation on the image
    # at a resolution of (pix_mult*8 x pix_mult*8)
    f = interpolate.interp2d(xx,yy,z_var,kind='cubic')
    return f(grid_x,grid_y)
grid_z = interp(zz) # interpolated image
#
#####################################
# Start and Format Figure 
#####################################
#
plt.rcParams.update({'font.size':16})
fig_dims = (10,9) # figure size
fig,ax = plt.subplots(figsize=fig_dims) # start figure
fig.canvas.set_window_title('AMG8833 Image Interpolation')
im1 = ax.imshow(grid_z,vmin=18,vmax=37,cmap=plt.cm.RdBu_r) # plot image, with temperature bounds
cbar = fig.colorbar(im1,fraction=0.0475,pad=0.03) # colorbar
cbar.set_label('Temperature [C]',labelpad=10) # temp. label
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
    new_z = interp(np.reshape(pixels,pix_res)) # interpolated image
    im1.set_data(new_z) # update plot with new interpolated temps
    ax.draw_artist(im1) # draw image again
    fig.canvas.blit(ax.bbox) # blitting - for speeding up run
    fig.canvas.flush_events() # for real-time plot
    
