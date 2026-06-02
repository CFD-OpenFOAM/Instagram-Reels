import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.ndimage import gaussian_filter, label, binary_opening, binary_closing, binary_fill_holes, distance_transform_edt, generate_binary_structure

print("Initializing Thermal Conduction Topology Optimizer...")

# --- 1. THE GRID & MATERIAL SETUP ---
nelx = 80
nely = 50
volfrac = 0.30
penal = 4.0    # Higher penalty -> drives densities toward crisp 0/1
rmin = 3.0     # Min feature size enforcement during optimization
# threshold is computed adaptively to preserve the target volume fraction

# Thermal Conductivities
k0 = 1.0       # Copper/Aluminum (High conductivity)
kmin = 1e-6    # Air/Void (Insulator)

# --- 2. FINITE ELEMENT MATRICES (1 DOF per node for Heat Transfer) ---
# Element conductivity matrix for a square 2D element
KE = np.array([[ 4.0, -1.0, -2.0, -1.0],
               [-1.0,  4.0, -1.0, -2.0],
               [-2.0, -1.0,  4.0, -1.0],
               [-1.0, -2.0, -1.0,  4.0]]) / 6.0

nodenrs = np.reshape(np.arange((nelx + 1) * (nely + 1)), (1 + nelx, 1 + nely)).T
edofVec = np.reshape(nodenrs[0:-1, 0:-1], nelx * nely, 'F')
edofMat = (np.tile(edofVec.reshape(-1, 1), (1, 4))
           + np.tile(np.array([0, nely + 1, nely + 2, 1]), (nelx * nely, 1)))

iK = np.reshape(np.kron(edofMat, np.ones((4, 1))).T, 16 * nelx * nely, 'F').astype(int)
jK = np.reshape(np.kron(edofMat, np.ones((1, 4))).T, 16 * nelx * nely, 'F').astype(int)

# --- 3. THERMAL BOUNDARY CONDITIONS ---
ndof = (nelx + 1) * (nely + 1)

# Uniform Heat Generation across the entire domain (The hot EV component)
F = np.full((ndof, 1), 0.01)

# Heat Sink (Cold Plate) location: The middle of the left wall
sink_start = int(nely * 0.4)
sink_end = int(nely * 0.6)
fixeddofs = np.arange(sink_start, sink_end + 1)

alldofs = np.arange(ndof)
freedofs = np.setdiff1d(alldofs, fixeddofs)

# --- 4. DENSITY FILTER (Prevents checkerboarding) ---
nfilter = int(nelx * nely * (2 * (np.ceil(rmin) - 1) + 1) ** 2)
iH, jH, sH = np.zeros(nfilter), np.zeros(nfilter), np.zeros(nfilter)
cc = 0
for i1 in range(nelx):
    for j1 in range(nely):
        e1 = i1 * nely + j1
        imin, imax = max(i1 - (int(np.ceil(rmin)) - 1), 0), min(i1 + int(np.ceil(rmin)), nelx)
        jmin, jmax = max(j1 - (int(np.ceil(rmin)) - 1), 0), min(j1 + int(np.ceil(rmin)), nely)
        for i2 in range(imin, imax):
            for j2 in range(jmin, jmax):
                e2 = i2 * nely + j2
                iH[cc], jH[cc] = e1, e2
                sH[cc] = max(0, rmin - np.sqrt((i1 - i2)**2 + (j1 - j2)**2))
                cc += 1
iH, jH, sH = iH[:cc], jH[:cc], sH[:cc]
Hs = coo_matrix((sH, (iH.astype(int), jH.astype(int))), shape=(nelx * nely, nelx * nely)).tocsc()
Hs_sum = np.array(Hs.sum(1)).flatten()

# --- 5. THE OPTIMIZATION LOOP ---
x = np.full((nely, nelx), volfrac)
history = [x.copy() for _ in range(90)]
loop, change = 0, 1.0

print("Growing the thermal tree... (Solving heat conduction matrices)")

while change > 0.01 and loop < 150:
    loop += 1

    # Assemble global conductivity matrix
    sK = np.reshape(KE.flatten()[:, np.newaxis] * (kmin + x.flatten('F')**penal * (k0 - kmin)), 16 * nelx * nely, 'F')
    K = coo_matrix((sK, (iK, jK)), shape=(ndof, ndof)).tocsc()

    # Solve Thermal FEA (K * T = Q)
    U = np.zeros((ndof, 1))
    U[freedofs, 0] = spsolve(K[freedofs, :][:, freedofs], F[freedofs, 0])

    # Sensitivity Analysis (Thermal Compliance)
    Ue = U[edofMat, 0]
    ce = np.reshape(np.sum((Ue @ KE) * Ue, axis=1), (nely, nelx), 'F')
    dc = -penal * (k0 - kmin) * x**(penal - 1) * ce

    # Mesh Filtering (enforces min feature size -> uniform sheet thickness)
    dc[:] = np.asarray(Hs.dot(x.flatten('F') * dc.flatten('F')) / Hs_sum).reshape(nely, nelx, order='F')

    # Optimality Criteria (Update metal distribution)
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

    if loop % 10 == 0: print(f"  Iteration {loop}: change = {change:.4f}")

# --- 5b. IDEAL DESIGN: BINARIZE FOR INSPECTION ---
# Pre-smooth so the threshold finds coherent regions, not speckle from grey OC output.
x_smooth = gaussian_filter(x, sigma=rmin * 0.6)
threshold = float(np.quantile(x_smooth, 1.0 - volfrac))
x_ideal = (x_smooth > threshold).astype(float)
print(f"\nIdeal binarized design: threshold={threshold:.3f}, volume fraction={x_ideal.mean():.3f}")

# --- 5c. MANUFACTURABILITY VERIFICATION ---
print("\n=== MANUFACTURABILITY CHECKS ===")

def disk_kernel(r):
    r = int(np.ceil(r))
    y, xs = np.ogrid[-r:r + 1, -r:r + 1]
    return (xs**2 + y**2 <= r * r).astype(np.uint8)

def compliance(rho):
    sKp = np.reshape(KE.flatten()[:, np.newaxis] * (kmin + rho.flatten('F')**penal * (k0 - kmin)),
                     16 * nelx * nely, 'F')
    Kp = coo_matrix((sKp, (iK, jK)), shape=(ndof, ndof)).tocsc()
    Up = np.zeros((ndof, 1))
    Up[freedofs, 0] = spsolve(Kp[freedofs, :][:, freedofs], F[freedofs, 0])
    return float((F.T @ Up).item())

struct8 = generate_binary_structure(2, 2)  # 8-connectivity

# CHECK 1: Connectivity — drop islands not touching the cold sink
labels, n_components = label(x_ideal, structure=struct8)
sink_mask = np.zeros_like(x_ideal, dtype=bool)
sink_mask[sink_start:sink_end, 0] = True   # elements with sink boundary on left edge
sink_labels = np.unique(labels[sink_mask & (labels > 0)])
x_connected = np.isin(labels, sink_labels).astype(float)
n_islands = n_components - len(sink_labels)
print(f"  [1] Connectivity:   {n_components} solid components -> dropped {n_islands} floating island(s)")

# CHECK 2: Enclosed voids — holes not reachable from outer boundary
void = 1 - x_connected
void_labels, n_void = label(void, structure=struct8)
boundary_mask = np.zeros_like(void, dtype=bool)
boundary_mask[0, :] = boundary_mask[-1, :] = True
boundary_mask[:, 0] = boundary_mask[:, -1] = True
external_void_labels = np.unique(void_labels[boundary_mask & (void_labels > 0)])
enclosed_count = n_void - len(external_void_labels)
print(f"  [2] Enclosed voids: {n_void} void region(s), {enclosed_count} enclosed (need pierce ops)")

# CHECK 3: Corner filleting via binary_closing (fills threshold pinholes
# and rounds sharp inside corners). Kernel scales with rmin so the physical
# fillet radius is the same across mesh resolutions.
fillet_r = max(1, int(round(rmin / 2)))
kernel = disk_kernel(fillet_r)
x_practical = binary_closing(x_connected.astype(bool), structure=kernel, border_value=1)

# CHECK 3b: Fill all enclosed voids -> part can be made in a single stamping
# blow with no secondary pierce operations.
x_practical = binary_fill_holes(x_practical).astype(float)

# Re-verify connectivity after closing/fill (these only add, can't sever)
labels2, _ = label(x_practical, structure=struct8)
sink_labels2 = np.unique(labels2[sink_mask & (labels2 > 0)])
x_practical = np.isin(labels2, sink_labels2).astype(float)
print(f"  [3] Corner fillet:  applied disk kernel r={fillet_r} (rounds 90deg corners for die)")
print(f"  [3b] Voids filled:  {enclosed_count} enclosed void(s) filled for single-blow stamping")

# CHECK 4: Member width audit via distance transform
dist_solid = distance_transform_edt(x_practical)
if (x_practical > 0).any():
    # Skeleton-ish: thickness = 2 * local distance peak along medial axis
    from scipy.ndimage import maximum_filter
    local_max = (dist_solid == maximum_filter(dist_solid, size=3)) & (dist_solid > 0)
    widths = 2 * dist_solid[local_max]
    min_width = float(widths.min()) if widths.size else 0.0
    max_width = float(widths.max()) if widths.size else 0.0
else:
    min_width = max_width = 0.0
print(f"  [4] Member widths:  min={min_width:.1f} px, max={max_width:.1f} px (rmin target={rmin})")

# Performance comparison: ideal continuous vs ideal binary vs practical
c_continuous = compliance(np.clip(x, 1e-3, 1.0))
c_ideal      = compliance(np.clip(x_ideal, 1e-3, 1.0))
c_practical  = compliance(np.clip(x_practical, 1e-3, 1.0))
penalty_bin  = 100 * (c_ideal - c_continuous) / c_continuous
penalty_prac = 100 * (c_practical - c_continuous) / c_continuous
print(f"\nThermal compliance (lower = cooler part):")
print(f"  Continuous optimum: {c_continuous:.3f}")
print(f"  Ideal binarized:    {c_ideal:.3f}  ({penalty_bin:+.1f}%)")
print(f"  Practical (mfg):    {c_practical:.3f}  ({penalty_prac:+.1f}%)")
print(f"  Practical volume:   {x_practical.mean():.3f}")

# --- 5d. BUILD VIDEO FRAME SEQUENCE ---
# raw continuous -> ideal binary (30) -> hold ideal (30) -> practical (30) -> hold practical
for alpha in np.linspace(0, 1, 30):
    history.append((1 - alpha) * x + alpha * x_ideal)
n_hold_ideal = 30
for _ in range(n_hold_ideal):
    history.append(x_ideal.copy())
for alpha in np.linspace(0, 1, 30):
    history.append((1 - alpha) * x_ideal + alpha * x_practical)
n_hold_practical = 60
for _ in range(n_hold_practical):
    history.append(x_practical.copy())

# --- 6. RENDER THE B-ROLL ---
print("Rendering the thermal evolution video...")
fig = plt.figure(figsize=(4.5, 8))
fig.patch.set_facecolor('#0a0a0a')

# Axes positioned with enough left margin for the COLD SINK annotation
# and centered vertically in the 9:16 frame.
ax = fig.add_axes([0.22, 0.36, 0.70, 0.28])
ax.set_facecolor('#0a0a0a')
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values(): spine.set_visible(False)

# Minimalist Copper Colormap
colors_list = ['#0a0500', '#331400', '#8a3b00', '#cc5c00', '#ff9933']
cmap = LinearSegmentedColormap.from_list('copper', colors_list, N=256)

img = ax.imshow(history[0], cmap=cmap, vmin=0, vmax=1, interpolation='bilinear', aspect='equal')

# Boundary Annotations — cold sink line sits flush to the image left edge
ax.plot(np.full(sink_end - sink_start, -0.5), np.arange(sink_start, sink_end),
        color='#00FFFF', lw=4, zorder=5, clip_on=False)
ax.text(-2.0, (sink_start + sink_end) / 2, 'COLD\nSINK', ha='right', va='center',
        color='#00FFFF', fontsize=9, fontweight='bold', fontfamily='monospace')

# Text formatting
fig.text(0.5, 0.72, 'THERMAL TOPOLOGY', ha='center', va='bottom',
         fontsize=16, color='#ff9933', fontfamily='monospace', fontweight='bold')
phase_text = fig.text(0.5, 0.69, '', ha='center', va='bottom',
                      fontsize=9, color='#8a3b00', fontfamily='monospace')
iter_text = fig.text(0.5, 0.31, '', ha='center', va='top',
                     fontsize=11, color='#ff9933', fontfamily='monospace', fontweight='bold')

# Bottom report panel: 4 checks, populated during practical phase
report_lines = [
    f"[1] CONNECTIVITY  : {n_islands} ISLANDS REMOVED",
    f"[2] ENCLOSED VOIDS: {enclosed_count} FILLED (1-BLOW STAMP)",
    f"[3] CORNER FILLET : DISK r={fillet_r}px APPLIED",
    f"[4] MIN WIDTH     : {min_width:.1f}px  (rmin={rmin})",
    f"COMPLIANCE PENALTY: {penalty_prac:+.1f}% vs IDEAL",
]
report_texts = [
    fig.text(0.08, 0.22 - i * 0.022, '', ha='left', va='top',
             fontsize=7.5, color='#00FFFF', fontfamily='monospace')
    for i in range(len(report_lines))
]

def update(frame):
    idx = min(frame, len(history) - 1)
    data = history[idx]
    glow = gaussian_filter(data, sigma=0.6)
    img.set_data(np.clip(0.75 * data + 0.25 * glow, 0, 1))

    n_intro = 90
    n_opt_end = n_intro + loop
    n_to_ideal_end = n_opt_end + 30
    n_hold_ideal_end = n_to_ideal_end + n_hold_ideal
    n_to_prac_end = n_hold_ideal_end + 30
    n_hold_prac_end = n_to_prac_end + n_hold_practical

    # Default: clear report
    for t in report_texts:
        t.set_text('')

    if frame < n_intro:
        phase_text.set_text('Heat Conduction Setup')
        iter_text.set_text('INITIALIZING HEAT GENERATION DOMAIN')
    elif idx < n_opt_end:
        phase_text.set_text('SIMP Optimization  \u2014  30% Copper Volume')
        iter_text.set_text(f'ITERATION {idx - n_intro + 1}')
    elif idx < n_to_ideal_end:
        phase_text.set_text('Binarizing  \u2014  threshold @ 0.5')
        iter_text.set_text('IDEAL TOPOLOGY')
    elif idx < n_hold_ideal_end:
        phase_text.set_text('Ideal Optimum  \u2014  not yet manufacturable')
        iter_text.set_text(f'IDEAL  \u00b7  c = {c_ideal:.2f}')
    elif idx < n_to_prac_end:
        phase_text.set_text('Applying manufacturing constraints')
        iter_text.set_text('CLEANUP \u2192 STAMPABLE')
    else:
        phase_text.set_text(f'Stampable Cutout  \u2014  {x_practical.mean() * 100:.0f}% material')
        iter_text.set_text(f'PRACTICAL  \u00b7  c = {c_practical:.2f}  ({penalty_prac:+.0f}%)')
        for t, line in zip(report_texts, report_lines):
            t.set_text(line)

    return [img, iter_text, phase_text, *report_texts]

total_frames = len(history) + 60 
ani = animation.FuncAnimation(fig, update, frames=total_frames, interval=33, blit=True)

Writer = animation.writers['ffmpeg']
writer = Writer(fps=30, metadata=dict(artist='Wrench-Wise'), bitrate=3000)
ani.save('thermal_topology.mp4', writer=writer, dpi=200)

print("Boom! Video saved as thermal_topology.mp4")