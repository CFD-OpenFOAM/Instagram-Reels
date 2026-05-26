import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.ndimage import gaussian_filter

print("Initializing FEA Topology Optimizer...")

# --- 1. THE GRID & MATERIAL SETUP ---
# Landscape cantilever beam centered in a 9:16 portrait canvas
nelx = 80  # Width (X-axis) — long beam
nely = 30  # Height (Y-axis) — classic beam proportions
volfrac = 0.30 # We want to keep exactly 30% of the material
penal = 3.0    # Penalty factor to force pixels to be either 100% solid or 100% empty
rmin = 2.0     # Mesh filter radius (prevents checkerboarding)

# Material properties
E0 = 1.0       # Young's modulus of solid material
Emin = 1e-9    # Young's modulus of void material (prevents matrix singularity)
nu = 0.3       # Poisson's ratio

# --- 2. FINITE ELEMENT MATRICES ---
# Building the element stiffness matrix (KE) for a 2D square element
A11 = np.array([[12, 3, -6, -3], [3, 12, 3, 0], [-6, 3, 12, -3], [-3, 0, -3, 12]])
A12 = np.array([[-6, -3, 0, 3], [-3, -6, -3, -6], [0, -3, -6, 3], [3, -6, 3, -6]])
B11 = np.array([[-4, 3, -2, 9], [3, -4, -9, 4], [-2, -9, -4, -3], [9, 4, -3, -4]])
B12 = np.array([[2, -3, 4, -9], [-3, 2, 9, -2], [4, 9, 2, 3], [-9, -2, 3, 2]])

KE = 1.0 / (1.0 - nu**2) / 24.0 * (np.block([[A11, A12], [A12.T, A11]]) + nu * np.block([[B11, B12], [B12.T, B11]]))

# Node numbering map (0-indexed)
nodenrs = np.reshape(np.arange((nelx + 1) * (nely + 1)), (1 + nelx, 1 + nely)).T
edofVec = np.reshape(2 * nodenrs[0:-1, 0:-1] + 2, nelx * nely, 'F')
edofMat = (np.tile(edofVec.reshape(-1, 1), (1, 8))
           + np.tile(np.array([0, 1, 2 * nely + 2, 2 * nely + 3,
                               2 * nely, 2 * nely + 1, -2, -1]),
                     (nelx * nely, 1)))
iK = np.reshape(np.kron(edofMat, np.ones((8, 1))).T, 64 * nelx * nely, 'F').astype(int)
jK = np.reshape(np.kron(edofMat, np.ones((1, 8))).T, 64 * nelx * nely, 'F').astype(int)

# --- 3. BOUNDARY CONDITIONS (Cantilever — fixed left wall, load at bottom-right) ---
ndof = 2 * (nelx + 1) * (nely + 1)

F = np.zeros((ndof, 1))
# Apply a downward load at the bottom-right corner
bottom_right_node = nelx * (nely + 1) + nely  # nodenrs[nely, nelx]
F[2 * bottom_right_node + 1, 0] = -1.0

# Lock the ENTIRE left wall (x = 0) — both X and Y DOFs
fixeddofs = np.arange(0, 2 * (nely + 1))

alldofs = np.arange(ndof)
freedofs = np.setdiff1d(alldofs, fixeddofs)

# --- 4. PRE-COMPUTE DENSITY FILTER ---
nfilter = int(nelx * nely * (2 * (np.ceil(rmin) - 1) + 1) ** 2)
iH = np.zeros(nfilter)
jH = np.zeros(nfilter)
sH = np.zeros(nfilter)
cc = 0
for i1 in range(nelx):
    for j1 in range(nely):
        e1 = i1 * nely + j1
        imin = max(i1 - (int(np.ceil(rmin)) - 1), 0)
        imax = min(i1 + int(np.ceil(rmin)), nelx)
        jmin = max(j1 - (int(np.ceil(rmin)) - 1), 0)
        jmax = min(j1 + int(np.ceil(rmin)), nely)
        for i2 in range(imin, imax):
            for j2 in range(jmin, jmax):
                e2 = i2 * nely + j2
                iH[cc] = e1
                jH[cc] = e2
                sH[cc] = max(0, rmin - np.sqrt((i1 - i2)**2 + (j1 - j2)**2))
                cc += 1
iH = iH[:cc]
jH = jH[:cc]
sH = sH[:cc]
Hs = coo_matrix((sH, (iH.astype(int), jH.astype(int))),
                shape=(nelx * nely, nelx * nely)).tocsc()
Hs_sum = np.array(Hs.sum(1)).flatten()

# --- 5. THE OPTIMIZATION LOOP ---
x = np.full((nely, nelx), volfrac) # Start with a uniform grey block
# Create a 5-second (150 frame) pause at the start of the video
history = [x.copy() for _ in range(150)]
loop = 0
change = 1.0

print("Carving the bone structure... (This involves heavy matrix math, give it a minute!)")

# Run until the structure stabilizes (max 120 iterations for visual speed)
while change > 0.01 and loop < 120:
    loop += 1

    # 1. Finite Element Analysis (FEA)
    # Assemble the global stiffness matrix based on current material density
    sK = np.reshape(KE.flatten()[:, np.newaxis] * (Emin + x.flatten('F')**penal * (E0 - Emin)), 64 * nelx * nely, 'F')
    K = coo_matrix((sK, (iK, jK)), shape=(ndof, ndof)).tocsc()

    # Solve the system of equations (KU = F) to find displacements
    U = np.zeros((ndof, 1))
    U[freedofs, 0] = spsolve(K[freedofs, :][:, freedofs], F[freedofs, 0])

    # 2. Sensitivity Analysis (Where is the stress?)
    Ue = U[edofMat, 0]  # (nelx*nely, 8)
    ce = np.reshape(np.sum((Ue @ KE) * Ue, axis=1), (nely, nelx), 'F')
    dc = -penal * (E0 - Emin) * x**(penal - 1) * ce

    # 3. Mesh Filtering (Smooths the edges)
    dc[:] = np.asarray(
        Hs.dot(x.flatten('F') * dc.flatten('F')) / Hs_sum
    ).reshape(nely, nelx, order='F')

    # 4. Optimality Criteria (Update the material densities)
    l1, l2, move = 0, 1e9, 0.2
    while (l2 - l1) > 1e-4:
        lmid = 0.5 * (l2 + l1)
        xnew = np.maximum(0.001, np.maximum(x - move, np.minimum(1.0, np.minimum(x + move, x * np.sqrt(-dc / lmid)))))
        if np.sum(xnew) - volfrac * nelx * nely > 0:
            l1 = lmid
        else:
            l2 = lmid

    change = np.max(np.abs(xnew - x))
    x = xnew
    history.append(x.copy())

    if loop % 10 == 0:
        print(f"  Iteration {loop}: change = {change:.4f}")

print(f"Optimization converged after {loop} iterations.")

# --- 6. RENDER THE B-ROLL ---
print("Rendering the evolutionary video...")

# 9:16 portrait canvas with beam centered in the middle band
fig = plt.figure(figsize=(4.5, 8))
fig.patch.set_facecolor('#0a0a0a')

# Position the beam axes in the vertical center of the portrait frame
# [left, bottom, width, height] in figure fraction
ax = fig.add_axes([0.04, 0.35, 0.92, 0.30])
ax.set_facecolor('#0a0a0a')
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

# Custom colormap: void -> deep blue -> cyan -> white-hot highlights
colors_list = ['#000000', '#001133', '#0047AB', '#00BFFF', '#00FFFF', '#AAFFFF']
cmap = LinearSegmentedColormap.from_list('alien_bone', colors_list, N=256)

img = ax.imshow(history[0], cmap=cmap, vmin=0, vmax=1, interpolation='bilinear',
                aspect='equal')

# Boundary condition markers
# Fixed wall (left edge) - red triangles along the left side
left_wall_y = np.linspace(0, nely - 1, 6)
ax.plot(np.zeros_like(left_wall_y) - 1.5, left_wall_y, '>',
        color='#FF4444', markersize=7, zorder=5, clip_on=False)
# Hatching line for the fixed wall
for y in np.linspace(-0.5, nely - 0.5, 12):
    ax.plot([-3.5, -0.5], [y - 0.8, y + 0.8], '-', color='#FF4444',
            lw=0.8, clip_on=False, alpha=0.5)
# Load arrow (bottom-right corner)
ax.annotate('', xy=(nelx - 0.5, nely + 3), xytext=(nelx - 0.5, nely - 4),
            arrowprops=dict(arrowstyle='->', color='#FFAA00', lw=2.5),
            annotation_clip=False)
ax.text(nelx - 0.5, nely + 4.5, 'F', ha='center', va='top',
        color='#FFAA00', fontsize=12, fontweight='bold', fontfamily='serif',
        clip_on=False)

# Title above the beam
fig.text(0.5, 0.72, 'TOPOLOGY OPTIMIZATION', ha='center', va='bottom',
         fontsize=16, color='#00FFFF', fontfamily='monospace', fontweight='bold')
fig.text(0.5, 0.69, 'Cantilever Beam  \u2014  30% Volume Fraction',
         ha='center', va='bottom', fontsize=9, color='#557788',
         fontfamily='monospace')

# Iteration counter below the beam
iter_text = fig.text(0.5, 0.30, '', ha='center', va='top',
                     fontsize=11, color='#00FFFF',
                     fontfamily='monospace', fontweight='bold')

# Branding watermark at the bottom
fig.text(0.5, 0.05, 'WRENCH-WISE', ha='center', va='bottom',
         fontsize=10, color='#334455', fontfamily='monospace',
         fontweight='bold', alpha=0.6)

def update(frame):
    idx = min(frame, len(history) - 1)
    data = history[idx]
    # Apply subtle gaussian blur for a glow effect
    glow = gaussian_filter(data, sigma=0.8)
    blended = np.clip(0.7 * data + 0.3 * glow, 0, 1)
    img.set_data(blended)
    # During the intro pause, show setup label; during optimization, show iteration
    n_intro = 150
    if frame < n_intro:
        iter_text.set_text('INITIAL DESIGN DOMAIN')
    elif idx < len(history) - 1:
        opt_iter = idx - n_intro + 1
        iter_text.set_text(f'ITERATION {opt_iter}/{len(history) - n_intro}')
    else:
        iter_text.set_text(f'OPTIMIZED  \u00b7  {volfrac * 100:.0f}% MATERIAL')
    return [img, iter_text]

total_frames = len(history) + 60  # Hold final frame ~2s at 30fps
ani = animation.FuncAnimation(fig, update, frames=total_frames, interval=33, blit=True)

Writer = animation.writers['ffmpeg']
writer = Writer(fps=30, metadata=dict(artist='Wrench-Wise'), bitrate=3000)
ani.save('topology_optimization.mp4', writer=writer, dpi=200)

print("Video saved as topology_optimization.mp4")