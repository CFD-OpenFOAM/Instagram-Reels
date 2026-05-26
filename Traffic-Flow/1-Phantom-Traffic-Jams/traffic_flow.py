import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap

print("Initializing Traffic Fluid Dynamics Simulator...")

# --- 1. PHYSICS PARAMETERS ---
N = 22                # Number of cars
L = 250.0             # Length of the circular road (meters)
v_max = 10.0          # Max speed (m/s)
safe_dist = 5.0       # Minimum safe distance
alpha = 1.5           # Sensitivity/Reaction acceleration
dt = 0.05             # Time step
steps = 1500          # Total frames

# Optimal velocity function (Bando model)
def v_opt(dx):
    # Transition from 0 to v_max based on distance
    return v_max * (np.tanh(dx - safe_dist) + np.tanh(safe_dist)) / (1.0 + np.tanh(safe_dist))

# --- 2. INITIALIZE TWO SIMULATIONS ---
# x1/v1 = Top Ring (Normal Humans)
# x2/v2 = Bottom Ring (One Damper Car)
x1 = np.linspace(0, L, N, endpoint=False)
v1 = np.ones(N) * v_opt(L/N)
x2 = x1.copy()
v2 = v1.copy()

history_x1 = np.zeros((steps, N))
history_v1 = np.zeros((steps, N))
history_x2 = np.zeros((steps, N))
history_v2 = np.zeros((steps, N))

print("Simulating kinematic waves...")

for t in range(steps):
    # Calculate distances to the car ahead (with circular wrap-around)
    dx1 = np.roll(x1, -1) - x1
    dx1[dx1 < 0] += L
    
    dx2 = np.roll(x2, -1) - x2
    dx2[dx2 < 0] += L
    
    # Introduce a perturbation (someone tapping brakes at t=100)
    if t == 100:
        v1[0] *= 0.5
        v2[0] *= 0.5
        
    # Standard Car-Following Acceleration (Top Ring)
    a1 = alpha * (v_opt(dx1) - v1)
    
    # Bottom Ring: Car 10 is the "Damper"
    a2 = alpha * (v_opt(dx2) - v2)
    # The Damper ignores the car immediately in front and holds a steady average speed
    a2[10] = 0.5 * ( (v_max * 0.45) - v2[10] ) 
    
    # Update velocities and positions
    v1 += a1 * dt
    v1 = np.clip(v1, 0, v_max)
    x1 += v1 * dt
    x1 %= L
    
    v2 += a2 * dt
    v2 = np.clip(v2, 0, v_max)
    x2 += v2 * dt
    x2 %= L
    
    history_x1[t] = x1
    history_v1[t] = v1
    history_x2[t] = x2
    history_v2[t] = v2

# --- 3. RENDERING THE VIDEO ---
print("Rendering 9:16 Video...")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(4.5, 8), gridspec_kw={'height_ratios': [1, 1]})
fig.patch.set_facecolor('#0a0a0a')

for ax in [ax1, ax2]:
    ax.set_facecolor('#0a0a0a')
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    # Draw the road
    circle = plt.Circle((0, 0), 1, color='#1a1a24', fill=False, lw=15)
    ax.add_patch(circle)

# Titles
ax1.set_title("HUMAN DRIVERS\n(Kinematic Shockwave)", color='#FFFFFF', fontfamily='monospace', fontsize=12, pad=10)
ax2.set_title("THE DAMPER\n(Wave Absorption)", color='#FFFFFF', fontfamily='monospace', fontsize=12, pad=10)

# Velocity Colormap: Red (Stopped) -> Yellow -> Green (Fast)
cmap = LinearSegmentedColormap.from_list('traffic', ['#FF0044', '#FFCC00', '#00FF66'], N=256)

# Create scatter plots
scat1 = ax1.scatter([], [], s=80, zorder=5)
scat2 = ax2.scatter([], [], s=80, zorder=5)

def update(frame):
    # We skip frames to speed up the visual playback
    f = frame * 3 
    if f >= steps: f = steps - 1
    
    # Convert linear road position to Polar coordinates for the ring
    theta1 = 2 * np.pi * history_x1[f] / L
    x1_circ = np.cos(theta1)
    y1_circ = np.sin(theta1)
    
    theta2 = 2 * np.pi * history_x2[f] / L
    x2_circ = np.cos(theta2)
    y2_circ = np.sin(theta2)
    
    scat1.set_offsets(np.c_[x1_circ, y1_circ])
    scat1.set_color(cmap(history_v1[f] / v_max))
    
    # Color the Damper car Cyan so the viewer can track it
    colors2 = cmap(history_v2[f] / v_max)
    colors2[10] = [0.0, 1.0, 1.0, 1.0] # Cyan Damper
    scat2.set_offsets(np.c_[x2_circ, y2_circ])
    scat2.set_color(colors2)
    
    return scat1, scat2

ani = animation.FuncAnimation(fig, update, frames=steps//3, interval=33, blit=True)

Writer = animation.writers['ffmpeg']
writer = Writer(fps=30, metadata=dict(artist='Wrench-Wise'), bitrate=2500)
ani.save('traffic_fluid.mp4', writer=writer)

print("Done! Video saved as traffic_fluid.mp4")