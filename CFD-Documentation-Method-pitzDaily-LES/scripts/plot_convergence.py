"""
Convergence Plot Generator for pitzDaily LES
Parses OpenFOAM log file and plots residuals vs. time step.
"""
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

LOG_FILE = r"\pitzDaily-LES\log.pisoFoam"
OUTPUT_FILE = r"\images\convergence_plot.png"

import os
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# Parse log file
times = []
residuals = {"Ux": [], "Uy": [], "p": [], "k": []}
courant_max = []

time_pattern = re.compile(r"^Time = ([\d.e+-]+)$")
ux_pattern = re.compile(r"Solving for Ux, Initial residual = ([\d.e+-]+)")
uy_pattern = re.compile(r"Solving for Uy, Initial residual = ([\d.e+-]+)")
p_pattern = re.compile(r"Solving for p, Initial residual = ([\d.e+-]+)")
k_pattern = re.compile(r"Solving for k, Initial residual = ([\d.e+-]+)")
courant_pattern = re.compile(r"Courant Number mean:.*max: ([\d.e+-]+)")

current_time = None
current_ux = None
current_uy = None
current_p = None
current_k = None
current_co = None

with open(LOG_FILE, "r") as f:
    for line in f:
        m = time_pattern.match(line.strip())
        if m:
            # Save previous timestep data
            if current_time is not None and current_ux is not None:
                times.append(current_time)
                residuals["Ux"].append(current_ux)
                residuals["Uy"].append(current_uy)
                residuals["p"].append(current_p)
                residuals["k"].append(current_k)
                courant_max.append(current_co)
            current_time = float(m.group(1))
            current_ux = current_uy = current_p = current_k = current_co = None
            continue

        m = ux_pattern.search(line)
        if m and current_ux is None:
            current_ux = float(m.group(1))
        m = uy_pattern.search(line)
        if m and current_uy is None:
            current_uy = float(m.group(1))
        m = p_pattern.search(line)
        if m and current_p is None:
            current_p = float(m.group(1))
        m = k_pattern.search(line)
        if m and current_k is None:
            current_k = float(m.group(1))
        m = courant_pattern.search(line)
        if m:
            current_co = float(m.group(1))

# Save last timestep
if current_time is not None and current_ux is not None:
    times.append(current_time)
    residuals["Ux"].append(current_ux)
    residuals["Uy"].append(current_uy)
    residuals["p"].append(current_p)
    residuals["k"].append(current_k)
    courant_max.append(current_co)

times = np.array(times)
print(f"Parsed {len(times)} timesteps from {times[0]:.6f} to {times[-1]:.6f}")

# --- Plot ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
fig.suptitle("pitzDaily LES — Convergence History", fontsize=16, fontweight="bold")

# Residuals
for key, color in zip(["Ux", "Uy", "p", "k"], ["#2196F3", "#FF5722", "#4CAF50", "#9C27B0"]):
    ax1.semilogy(times, residuals[key], label=key, color=color, linewidth=0.6, alpha=0.85)

ax1.set_ylabel("Initial Residual", fontsize=12)
ax1.legend(loc="upper right", fontsize=10, framealpha=0.9)
ax1.grid(True, which="both", alpha=0.3)
ax1.set_title("Residuals", fontsize=13)

# Courant number
ax2.plot(times, courant_max, color="#FF9800", linewidth=0.6, alpha=0.85)
ax2.set_ylabel("Max Courant Number", fontsize=12)
ax2.set_xlabel("Time [s]", fontsize=12)
ax2.grid(True, alpha=0.3)
ax2.set_title("Courant Number", fontsize=13)
ax2.axhline(y=1.0, color="red", linestyle="--", alpha=0.5, label="Co = 1")
ax2.legend(loc="upper right", fontsize=10)

plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=200, bbox_inches="tight", facecolor="white")
print(f"Saved convergence plot to {OUTPUT_FILE}")

# Print final metrics
print("\n--- Final Simulation Metrics ---")
print(f"Final time: {times[-1]:.6f} s")
print(f"Total timesteps parsed: {len(times)}")
print(f"Final Ux residual: {residuals['Ux'][-1]:.6e}")
print(f"Final Uy residual: {residuals['Uy'][-1]:.6e}")
print(f"Final p residual:  {residuals['p'][-1]:.6e}")
print(f"Final k residual:  {residuals['k'][-1]:.6e}")
print(f"Final max Courant: {courant_max[-1]:.4f}")
print(f"Mean max Courant:  {np.mean(courant_max):.4f}")
