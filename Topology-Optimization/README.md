# Topology Optimization — Cantilever Beam

2D topology optimization of a cantilever beam using the SIMP (Solid Isotropic Material with Penalization) method. The script solves the compliance minimization problem via finite element analysis and renders the iterative material removal process as an animated video.

## Problem Setup

| Parameter | Value |
|---|---|
| Design domain | 80 x 30 elements (landscape) |
| Volume fraction | 30% |
| Boundary condition | Fixed left wall, point load at bottom-right corner |
| Penalization factor | 3.0 |
| Filter radius | 2.0 |
| Max iterations | 120 |
| Convergence threshold | 0.01 (max element density change) |

The optimizer starts from a uniform density field and iteratively removes material from regions with low strain energy, preserving only the load-carrying members. The result is an organic, truss-like structure that minimizes compliance (maximizes stiffness) under the given volume constraint.

## Method

1. **Finite Element Analysis** — Assembles and solves the global stiffness system (KU = F) at each iteration using sparse direct solvers.
2. **Sensitivity Analysis** — Computes the derivative of compliance with respect to element densities.
3. **Density Filtering** — Applies a spatial filter to prevent checkerboard artifacts and mesh dependency.
4. **Optimality Criteria Update** — Adjusts element densities using a bisection method on the Lagrange multiplier to satisfy the volume constraint.

Based on the 88-line MATLAB topology optimization code by Andreassen et al. (2011), ported to Python with NumPy/SciPy.

## Output

The script produces `topology_optimization.mp4` — a 9:16 portrait-format video suitable for social media (Instagram Reels, YouTube Shorts, TikTok). The video shows:

- 5-second hold on the initial design domain with boundary condition markers
- Progressive material removal across all optimization iterations
- 2-second hold on the final optimized structure

Visual elements include fixed-wall hatching, load arrow annotation, iteration counter, and a custom dark-to-cyan colormap.

## Requirements

- Python 3.8+
- NumPy
- SciPy
- Matplotlib
- FFmpeg (must be installed and accessible on PATH for video export)

### Install dependencies

```
pip install numpy scipy matplotlib
```

FFmpeg can be installed from https://ffmpeg.org/download.html or via a package manager:

```
conda install -c conda-forge ffmpeg
```

## Usage

```
python alien_bone.py
```

The script prints iteration progress to the console and saves the output video to `topology_optimization.mp4` in the working directory.

## References

- Andreassen, E., Clausen, A., Schevenels, M., Lazarov, B.S., Sigmund, O. (2011). "Efficient topology optimization in MATLAB using 88 lines of code." *Structural and Multidisciplinary Optimization*, 43(1), 1-16.
- Bendsoe, M.P., Sigmund, O. (2003). *Topology Optimization: Theory, Methods, and Applications*. Springer.