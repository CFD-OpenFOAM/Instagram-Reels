"""
Contour Plot Generator for pitzDaily LES
Uses PyVista to read the final OpenFOAM result and create
velocity magnitude + streamlines contour plot showing reattachment.
"""
import pyvista as pv
import numpy as np
import os

CASE_DIR = r"pitzDaily-LES"
OUTPUT_FILE = os.path.join(CASE_DIR, "images", "velocity_contour.png")
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# Find the latest time directory
time_dirs = []
for d in os.listdir(CASE_DIR):
    try:
        t = float(d)
        if t > 0:
            time_dirs.append((t, d))
    except ValueError:
        pass

time_dirs.sort()
latest_time = time_dirs[-1][1]
print(f"Using time directory: {latest_time}")

# Read the OpenFOAM case using pyvista
reader = pv.OpenFOAMReader(os.path.join(CASE_DIR, "pitzDaily-LES.foam"))

# Set to latest time
reader.set_active_time_value(float(latest_time))

# Read all patches
reader.cell_to_point_creation = True
mesh = reader.read()

# Get internal mesh
internal = mesh["internalMesh"]
print(f"Internal mesh cells: {internal.n_cells}")
print(f"Available arrays: {internal.array_names}")

# Compute velocity magnitude from instantaneous U
if "U" in internal.array_names:
    U = internal["U"]
    Umag = np.linalg.norm(U, axis=1)
    internal["Umag"] = Umag
    print(f"Velocity magnitude range: {Umag.min():.4f} - {Umag.max():.4f} m/s")

# Compute mean velocity magnitude
if "UMean" in internal.array_names:
    UMean = internal["UMean"]
    UMeanMag = np.linalg.norm(UMean, axis=1)
    internal["UMeanMag"] = UMeanMag
    print(f"Mean velocity magnitude range: {UMeanMag.min():.4f} - {UMeanMag.max():.4f} m/s")

# Extract 2D slice at z=0
slice_mesh = internal.slice(normal="z", origin=(0, 0, 0))
print(f"Slice cells: {slice_mesh.n_cells}")

# --- Create the plot ---
pv.set_plot_theme("document")
pl = pv.Plotter(off_screen=True, window_size=[1800, 600])

# Velocity magnitude contour
pl.add_mesh(
    slice_mesh,
    scalars="Umag",
    cmap="RdYlBu_r",
    clim=[0, 15],
    show_edges=False,
    scalar_bar_args={
        "title": "Velocity Magnitude [m/s]",
        "title_font_size": 14,
        "label_font_size": 12,
        "position_x": 0.82,
        "position_y": 0.15,
        "width": 0.12,
        "height": 0.7,
    },
)

# Add step edge annotation
pl.add_text(
    "pitzDaily LES — Velocity Magnitude (OpenFOAM v2506)",
    position="upper_left",
    font_size=12,
    color="black",
)

pl.camera_position = "xy"
pl.camera.tight(padding=0.05)

pl.screenshot(OUTPUT_FILE, transparent_background=False, scale=2)
print(f"Saved contour plot to {OUTPUT_FILE}")

# --- Mean velocity contour ---
MEAN_OUTPUT = os.path.join(CASE_DIR, "images", "mean_velocity_contour.png")
if "UMeanMag" in slice_mesh.array_names:
    pl2 = pv.Plotter(off_screen=True, window_size=[1800, 600])
    pl2.add_mesh(
        slice_mesh,
        scalars="UMeanMag",
        cmap="RdYlBu_r",
        clim=[0, 15],
        show_edges=False,
        scalar_bar_args={
            "title": "Mean Velocity [m/s]",
            "title_font_size": 14,
            "label_font_size": 12,
            "position_x": 0.82,
            "position_y": 0.15,
            "width": 0.12,
            "height": 0.7,
        },
    )
    pl2.add_text(
        "pitzDaily LES — Time-Averaged Velocity (OpenFOAM v2506)",
        position="upper_left",
        font_size=12,
        color="black",
    )
    pl2.camera_position = "xy"
    pl2.camera.tight(padding=0.05)
    pl2.screenshot(MEAN_OUTPUT, transparent_background=False, scale=2)
    print(f"Saved mean velocity contour to {MEAN_OUTPUT}")

# --- Compute approximate reattachment length ---
# The step height h = 25.4 mm = 0.0254 m
# Step is at x = 0
# Reattachment: where Ux changes sign along the lower wall (y ~ -0.0254)
step_height = 0.0254  # m

# Sample along a line near the lower wall (y ~ -0.012, mid-height of recirculation)
y_sample = -0.012
line_start = (0.001, y_sample, 0.0)
line_end = (0.25, y_sample, 0.0)
sampled = slice_mesh.sample_over_line(line_start, line_end, resolution=1000)

# Use UMean for reattachment (instantaneous U has eddies)
if "UMean" in sampled.array_names:
    Ux_line = sampled["UMean"][:, 0]
elif "U" in sampled.array_names:
    Ux_line = sampled["U"][:, 0]
else:
    Ux_line = None

if Ux_line is not None:
    x_coords = sampled.points[:, 0]
    # Find where Ux changes from negative to positive
    sign_changes = np.where(np.diff(np.sign(Ux_line)) > 0)[0]
    if len(sign_changes) > 0:
        idx = sign_changes[0]
        # Linear interpolation
        x_reattach = x_coords[idx] + (x_coords[idx+1] - x_coords[idx]) * \
                     (-Ux_line[idx]) / (Ux_line[idx+1] - Ux_line[idx])
        reattach_ratio = x_reattach / step_height
        print(f"\n--- Reattachment Length ---")
        print(f"Reattachment point x = {x_reattach*1000:.1f} mm")
        print(f"x/h = {reattach_ratio:.2f}")
        print(f"(Literature: x/h ≈ 6-7 for Re_h ~ 25,400)")
    else:
        print("No reattachment point found in sampled region")
