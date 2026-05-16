import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap

# --- SECTION 1: PARAMETERS ---
nx = 400            
ny = 100            
Re = 100.0          # Safe Re for D2Q9 stability
u_max = 0.1         
L_cyl = 20          

# Derived
D_cyl = 2 * L_cyl
nu = u_max * D_cyl / Re       
tau = 3.0 * nu + 0.5          
omega = 1.0 / tau             

steps = 10000        
save_every = 20     

# Geometry
cx, cy = nx // 4, ny // 2 
r_cyl = L_cyl             

# Colors
C_WALL = "#2C3E50"
C_VORT_POS = "#E74C3C" 
C_VORT_NEG = "#3498DB" 
C_WHITE = "#FFFFFF"
cmap_vort = LinearSegmentedColormap.from_list("Vorticity", [C_VORT_NEG, C_WHITE, C_VORT_POS])

# --- SECTION 2: LATTICE SETUP ---
# 0:C, 1:E, 2:N, 3:W, 4:S, 5:NE, 6:NW, 7:SW, 8:SE
v_x = np.array([0, 1, 0, -1, 0, 1, -1, -1, 1])
v_y = np.array([0, 0, 1, 0, -1, 1, 1, -1, -1])
weights = np.array([4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36])
# Opposite mapping for bounce-back (Cylinder)
opposite = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6])

# --- SECTION 3: INITIALIZATION ---
Y, X = np.meshgrid(np.arange(ny), np.arange(nx), indexing='ij')
mask_cyl = (X - cx)**2 + (Y - cy)**2 < r_cyl**2

vel_x = np.full((ny, nx), u_max)
vel_x[:, :] += np.random.normal(0, 0.005, (ny, nx)) 
vel_y = np.zeros((ny, nx))

rho = np.ones((ny, nx))
f = np.zeros((9, ny, nx))

def get_equilibrium(rho, ux, uy):
    u_sq = ux**2 + uy**2
    f_eq = np.zeros((9, ny, nx))
    for i in range(9):
        eu = v_x[i]*ux + v_y[i]*uy
        f_eq[i] = weights[i] * rho * (1 + 3*eu + 4.5*eu**2 - 1.5*u_sq)
    return f_eq

f = get_equilibrium(rho, vel_x, vel_y)

# --- SECTION 4: MAIN LBM LOOP ---
history = []
print(f"LBM Started | Re={Re} | Tau={tau:.3f} | Slip Walls Active")

for it in range(steps):
    
    # 1. MACROSCOPIC
    rho = np.sum(f, axis=0)
    vel_x = np.sum(f * v_x[:, None, None], axis=0) / rho
    vel_y = np.sum(f * v_y[:, None, None], axis=0) / rho
    
    # 2. COLLISION
    f_eq = get_equilibrium(rho, vel_x, vel_y)
    f = f - omega * (f - f_eq)
    
    # 3. OBSTACLE BOUNCE-BACK (No-Slip on Cylinder)
    for i in range(9):
        f_out = f[i][mask_cyl]
        f[opposite[i]][mask_cyl] = f_out
        
    # 4. STREAMING
    for i in range(9):
        f[i] = np.roll(f[i], shift=(v_x[i], v_y[i]), axis=(1, 0))
        
    # 5. BOUNDARY CONDITIONS
    
    # A. Inlet (Fixed U_max)
    f[:, :, 0] = get_equilibrium(1.0, u_max, 0)[:, :, 0]
    
    # B. Outlet (Zero Gradient)
    f[:, :, -1] = f[:, :, -2]
    
    # C. FREE SLIP WALLS (Specular Reflection)
    # Top Wall (y = -1): Reflect N, NE, NW -> S, SE, SW
    # Directions: 2->4, 5->8, 6->7
    f[4, -1, :] = f[2, -1, :]
    f[8, -1, :] = f[5, -1, :]
    f[7, -1, :] = f[6, -1, :]
    
    # Bottom Wall (y = 0): Reflect S, SE, SW -> N, NE, NW
    # Directions: 4->2, 8->5, 7->6
    f[2, 0, :] = f[4, 0, :]
    f[5, 0, :] = f[8, 0, :]
    f[6, 0, :] = f[7, 0, :]
    
    # 6. SAVING
    if it % save_every == 0:
        # Vorticity
        dv_dx = np.gradient(vel_y, axis=1)
        du_dy = np.gradient(vel_x, axis=0)
        curl = dv_dx - du_dy
        curl[mask_cyl] = np.nan
        history.append(curl.copy())
        
    if it % 500 == 0:
        print(f"Step {it}/{steps}")

# --- SECTION 5: ANIMATION ---
print("Generating Animation...")

fig, ax = plt.subplots(figsize=(14, 5))
plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.15)

# Color limit
im_vort = ax.imshow(history[0], cmap=cmap_vort, origin='lower', 
                    vmin=-0.03, vmax=0.03, aspect='equal') 

circle = mpatches.Circle((cx, cy), r_cyl, color='gray', zorder=10)
ax.add_patch(circle)

ax.set_title(f"LBM Von Kármán Vortex Street (Re={int(Re)})", fontsize=16, fontweight='bold', color=C_WALL)
ax.set_yticks([])
ax.set_xticks([])

txt_step = ax.text(0.02, 0.05, "", transform=ax.transAxes, fontweight='bold', color='black')

def update(frame):
    im_vort.set_data(history[frame])
    txt_step.set_text(f"Step: {frame*save_every}")
    return im_vort, txt_step

ani = animation.FuncAnimation(fig, update, frames=len(history), interval=30, blit=False)
ani.save("LBM_Vortex_Shedding_Slip.gif", writer="pillow", fps=30, dpi=120)
plt.close(fig)
print("Saved LBM_Vortex_Shedding_Slip.gif")