import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import matplotlib.animation as animation

# --- Physics & PID Setup ---
y = 0.0          
v = 0.0          
target = 10.0    
mass = 1.0       
gravity = 9.81   
dt = 0.05        

integral_error = 0.0
prev_error = target - y

# History for plotting
time_data = [0]
y_data = [y]

# Start the simulation completely paused
is_playing = False 

# --- Figure Setup (MOBILE PORTRAIT 9:16 RATIO) ---
fig, ax = plt.subplots(figsize=(4.5, 8))
plt.subplots_adjust(bottom=0.4) # Leave the bottom 40% for controls

# Center the camera right from the start
ax.set_xlim(-5, 5)
ax.set_ylim(-2, 20)
ax.set_title("PID Drone Stabilizer")
ax.set_ylabel("Altitude")
ax.axhline(target, color='teal', linestyle='--', label='Target')

# The Flight Path
line, = ax.plot(time_data, y_data, color='#0047AB', lw=2, alpha=0.5, label='Flight Path')

# The Actual "Drone" Marker
drone_marker, = ax.plot([0], [y], marker='s', color='#0047AB', markersize=12, label='Drone')

ax.legend(loc='upper right', fontsize='small')

# --- Interactive Sliders (Stacked Vertically) ---
axcolor = 'lightgoldenrodyellow'
# [left, bottom, width, height]
ax_p = plt.axes([0.25, 0.30, 0.6, 0.025], facecolor=axcolor)
ax_i = plt.axes([0.25, 0.25, 0.6, 0.025], facecolor=axcolor)
ax_d = plt.axes([0.25, 0.20, 0.6, 0.025], facecolor=axcolor)

s_p = Slider(ax_p, 'P', 0.1, 20.0, valinit=2.0)
s_i = Slider(ax_i, 'I', 0.0, 5.0, valinit=0.0)
s_d = Slider(ax_d, 'D', 0.0, 20.0, valinit=0.0)

# --- New Control Buttons (Compact Grid) ---
ax_play = plt.axes([0.15, 0.12, 0.3, 0.05])
ax_reset = plt.axes([0.55, 0.12, 0.3, 0.05])
ax_wind = plt.axes([0.35, 0.04, 0.3, 0.05])

btn_play = Button(ax_play, 'Play / Pause', hovercolor='0.975')
btn_reset = Button(ax_reset, 'Reset', hovercolor='0.975')
btn_wind = Button(ax_wind, 'Wind Gust', hovercolor='0.975')

wind_force = 0.0

def toggle_play(event):
    global is_playing
    is_playing = not is_playing

def reset_sim(event):
    global y, v, integral_error, prev_error, time_data, y_data, is_playing, wind_force
    y = 0.0
    v = 0.0
    integral_error = 0.0
    prev_error = target - y
    wind_force = 0.0
    time_data = [0]
    y_data = [y]
    is_playing = False 
    
    ax.set_xlim(-5, 5)
    line.set_data(time_data, y_data)
    drone_marker.set_data([0], [y])
    fig.canvas.draw_idle()

def apply_wind(event):
    global wind_force
    wind_force = -30.0 

btn_play.on_clicked(toggle_play)
btn_reset.on_clicked(reset_sim)
btn_wind.on_clicked(apply_wind)

# --- Animation Loop ---
def update(frame):
    global y, v, integral_error, prev_error, wind_force
    
    if not is_playing:
        return line, drone_marker,
    
    error = target - y
    integral_error += error * dt
    derivative_error = (error - prev_error) / dt
    
    thrust = (s_p.val * error) + (s_i.val * integral_error) + (s_d.val * derivative_error)
    
    total_force = thrust - (mass * gravity) + wind_force
    acceleration = total_force / mass
    v += acceleration * dt
    y += v * dt
    
    wind_force *= 0.8 
    prev_error = error
    
    current_time = time_data[-1] + dt
    time_data.append(current_time)
    y_data.append(y)
    
    # LOCK THE CAMERA
    ax.set_xlim(current_time - 5, current_time + 5)
        
    line.set_data(time_data, y_data)
    drone_marker.set_data([current_time], [y])
    
    return line, drone_marker,

ani = animation.FuncAnimation(fig, update, frames=200, interval=50, blit=False)
plt.show()