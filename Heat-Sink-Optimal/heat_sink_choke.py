import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec

print("Initializing Parametric Heat Sink Optimizer...")

# --- 1. THE PHYSICS & MATH MODEL ---
W = 100.0        # Total width of the heat sink
t_fin = 1.0      # Thickness of each fin
delta = 3.0      # Boundary layer thickness threshold

def calculate_physics(N):
    """Calculates Area, Airflow, and Total Cooling for N fins."""
    N = np.maximum(N, 1)
    gap = (W - N * t_fin) / N
    
    # Surface area scales linearly with number of fins
    area = N / 50.0 
    
    # Airflow drops exponentially as the gap shrinks below the boundary layer thickness
    flow = 1.0 - np.exp(-gap / delta)
    flow = np.maximum(flow, 0.0)
    
    # Convective cooling combines Area and Flow (Q = h * A * dT, where h ~ sqrt(flow))
    cooling = area * np.sqrt(flow)
    return area, flow, cooling

# Generate the curve data
N_range = np.linspace(2, 50, 100)
areas, flows, coolings = calculate_physics(N_range)
# Normalize cooling for plotting
coolings = coolings / np.max(coolings)

# --- 2. SETUP THE FIGURE & LAYOUT ---
fig = plt.figure(figsize=(10, 8))
fig.patch.set_facecolor('#0a0a0a')
gs = GridSpec(2, 3, height_ratios=[1.2, 1], figure=fig)

# The 3 Heat Sink Viewports
ax_sparse = fig.add_subplot(gs[0, 0])
ax_optimal = fig.add_subplot(gs[0, 1])
ax_choked = fig.add_subplot(gs[0, 2])
axes_top = [ax_sparse, ax_optimal, ax_choked]

# The Optimization Graph Viewport
ax_graph = fig.add_subplot(gs[1, :])

# --- 3. DRAW THE STATIC GRAPH ---
ax_graph.set_facecolor('#0a0a0a')
for spine in ax_graph.spines.values(): spine.set_color('#333333')
ax_graph.tick_params(colors='#888888')
ax_graph.set_xlabel("Number of Cooling Fins", color='#888888', fontfamily='monospace')
ax_graph.set_ylabel("Performance", color='#888888', fontfamily='monospace')
ax_graph.set_xlim(0, 50)
ax_graph.set_ylim(0, 1.1)

ax_graph.plot(N_range, areas, color='#FFCC00', alpha=0.5, linestyle='--', label='Surface Area')
ax_graph.plot(N_range, flows, color='#00AACC', alpha=0.5, linestyle='--', label='Airflow Velocity')
ax_graph.plot(N_range, coolings, color='#11AA44', linewidth=3, label='Total Cooling Dissipated')
ax_graph.legend(facecolor='#111111', edgecolor='#333333', labelcolor='white', loc='upper right')

# Peak marker
optimal_idx = np.argmax(coolings)
opt_N = N_range[optimal_idx]
ax_graph.plot(opt_N, 1.0, 'o', color='#FFFFFF', markersize=8)
ax_graph.vlines(opt_N, 0, 1.0, color='#FFFFFF', linestyle=':', alpha=0.5)

# --- 4. DRAW THE HEAT SINKS ---
N_configs = [5, int(opt_N), 45] # Sparse, Optimal, Overpacked
colors_fin = ['#FF8800', '#00FFCC', '#FF0044'] # Orange, Cyan, Red
titles = ["SPARSE (Too Little Area)", "OPTIMAL (The Peak)", "OVERPACKED (Choked Flow)"]

for i, ax in enumerate(axes_top):
    ax.set_facecolor('#0a0a0a')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(-20, 120)
    ax.set_ylim(0, W)
    for spine in ax.spines.values(): spine.set_visible(False)
    
    ax.set_title(titles[i], color=colors_fin[i], fontfamily='monospace', fontweight='bold', fontsize=10)
    
    # Draw fins
    n_fins = N_configs[i]
    gap = W / n_fins
    for j in range(n_fins):
        y_pos = j * gap + gap/2
        ax.plot([0, 100], [y_pos, y_pos], color=colors_fin[i], linewidth=2.5, solid_capstyle='round')

# --- 5. PARTICLE ENGINE (THE FLUID DYNAMICS) ---
n_particles = 150
particles = []

# Initialize particles for each viewport: [x, y, vx, vy]
for i in range(3):
    pts = np.zeros((n_particles, 4))
    pts[:, 0] = np.random.uniform(-50, 0, n_particles) # Start left of the fins
    pts[:, 1] = np.random.uniform(0, W, n_particles)   # Spread evenly across height
    pts[:, 2] = np.random.uniform(2.0, 3.0, n_particles) # X Velocity
    pts[:, 3] = 0.0 # Y Velocity starts at 0
    particles.append(pts)

scatters = [ax.scatter([], [], s=10, color='#00AACC', alpha=0.6, edgecolors='none') for ax in axes_top]

def update(frame):
    for i in range(3):
        pts = particles[i]
        n_fins = N_configs[i]
        _, flow, _ = calculate_physics(n_fins)
        
        for p in range(n_particles):
            x, y, vx, vy = pts[p]
            
            # If approaching the heat sink (x between -5 and 0)
            if -5 < x < 0:
                if flow < 0.2: # CHOKED (Overpacked)
                    # Air violently deflects around the outside (up or down)
                    vx *= 0.8
                    if y > W/2: vy += 0.5
                    else: vy -= 0.5
                else: # FLOWING (Sparse or Optimal)
                    # Slow down slightly based on physics flow penalty
                    vx = 2.5 * flow 
            
            # Apply movement
            pts[p, 0] += vx
            pts[p, 1] += vy
            
            # Reset particle if it flies off screen
            if pts[p, 0] > 120 or pts[p, 1] > W + 20 or pts[p, 1] < -20:
                pts[p, 0] = np.random.uniform(-20, -5)
                pts[p, 1] = np.random.uniform(0, W)
                pts[p, 2] = np.random.uniform(2.0, 3.0)
                pts[p, 3] = 0.0
                
        scatters[i].set_offsets(pts[:, :2])
        
    return scatters

# Render a quick 10-second looping animation
print("Rendering MP4... (This will only take a few seconds)")
ani = animation.FuncAnimation(fig, update, frames=300, interval=33, blit=True)

Writer = animation.writers['ffmpeg']
writer = Writer(fps=30, metadata=dict(artist='Sid'), bitrate=2500)
ani.save('heatsink_choked.mp4', writer=writer)

print("Done! Video saved as heatsink_choked.mp4")