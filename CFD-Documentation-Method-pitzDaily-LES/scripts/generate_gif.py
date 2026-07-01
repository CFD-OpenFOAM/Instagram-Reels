"""
GIF Animation Generator for pitzDaily LES
Renders each saved timestep as a frame and assembles into an animated GIF.
"""
import pyvista as pv
import numpy as np
import os
import glob
from PIL import Image

CASE_DIR = r"\pitzDaily-LES"
OUTPUT_GIF = os.path.join(CASE_DIR, "images", "velocity_animation.gif")
FRAMES_DIR = os.path.join(CASE_DIR, "images", "frames")
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_GIF), exist_ok=True)

# Find all time directories
time_dirs = []
for d in os.listdir(CASE_DIR):
    try:
        t = float(d)
        if t > 0:
            time_dirs.append(t)
    except ValueError:
        pass

time_dirs.sort()
print(f"Found {len(time_dirs)} time directories: {time_dirs[0]:.4f} to {time_dirs[-1]:.4f}")

# Read the OpenFOAM case
reader = pv.OpenFOAMReader(os.path.join(CASE_DIR, "pitzDaily-LES.foam"))
available_times = reader.time_values
print(f"Available times in reader: {len(available_times)}")

# Filter to times that exist as directories
plot_times = [t for t in available_times if t > 0]
plot_times.sort()
print(f"Will render {len(plot_times)} frames")

# Render each frame
pv.set_plot_theme("document")
frame_files = []

for i, t in enumerate(plot_times):
    reader.set_active_time_value(t)
    reader.cell_to_point_creation = True
    mesh = reader.read()
    internal = mesh["internalMesh"]

    # Compute velocity magnitude
    if "U" in internal.array_names:
        U = internal["U"]
        Umag = np.linalg.norm(U, axis=1)
        internal["Umag"] = Umag

        # Slice at z=0
        slice_mesh = internal.slice(normal="z", origin=(0, 0, 0))

        # Create plot
        pl = pv.Plotter(off_screen=True, window_size=[1600, 500])
        pl.add_mesh(
            slice_mesh,
            scalars="Umag",
            cmap="RdYlBu_r",
            clim=[0, 15],
            show_edges=False,
            scalar_bar_args={
                "title": "Velocity [m/s]",
                "title_font_size": 12,
                "label_font_size": 10,
                "position_x": 0.82,
                "position_y": 0.15,
                "width": 0.12,
                "height": 0.7,
            },
        )

        pl.add_text(
            f"pitzDaily LES — t = {t:.4f} s",
            position="upper_left",
            font_size=11,
            color="black",
        )

        pl.camera_position = "xy"
        pl.camera.tight(padding=0.05)

        frame_path = os.path.join(FRAMES_DIR, f"frame_{i:04d}.png")
        pl.screenshot(frame_path, transparent_background=False, scale=2)
        frame_files.append(frame_path)
        pl.close()

        print(f"  [{i+1}/{len(plot_times)}] t = {t:.4f} s")

# Assemble GIF
print(f"\nAssembling {len(frame_files)} frames into GIF...")
frames = [Image.open(f) for f in frame_files]
frames[0].save(
    OUTPUT_GIF,
    save_all=True,
    append_images=frames[1:],
    duration=150,  # ms per frame
    loop=0,
)

print(f"Saved animation to {OUTPUT_GIF}")
print(f"GIF size: {os.path.getsize(OUTPUT_GIF) / 1024 / 1024:.1f} MB")
