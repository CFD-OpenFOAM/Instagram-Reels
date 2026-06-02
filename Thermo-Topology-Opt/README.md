# Thermal Topology Optimization

SIMP-based topology optimizer for a flat copper conduction spreader plate
cooled at the middle of its left edge, with uniform volumetric heat
generation across the domain. Output is a stampable cutout pattern with
manufacturability post-processing baked in.

## Files

| File | Mesh | `rmin` | Iter cap | Output |
|---|---|---|---|---|
| `thermal_topology.py`       | 80 × 50  | 3.0 | 150 | `thermal_topology.mp4` |
| `thermal_topology_hires.py` | 160 × 100 | 6.0 | 500 | `thermal_topology_hires.mp4` |
| `topology-optimization.py`  | 80 × 30  | 2.0 | 120 | `topology_optimization.mp4` (structural cantilever — reference port) |

The two thermal scripts are intentionally a matched pair for mesh-refinement
comparison: `rmin` is doubled in the hi-res script so the physical minimum
feature size is identical. The morphology kernel `fillet_r` auto-scales as
`round(rmin / 2)`, keeping the physical corner-fillet radius constant too.

## Running

Both scripts require the `heatsink-opt` conda env (numpy, scipy, matplotlib,
ffmpeg).

```bash
conda run -n heatsink-opt python thermal_topology.py        # ~30 s
conda run -n heatsink-opt python thermal_topology_hires.py  # ~5 min
```

## The optimization

Standard density-based SIMP for thermal compliance:

- **Element conductivity matrix:** 4×4 (1 DOF/node, temperature)
- **Interpolation:** `k(x) = kmin + x^penal · (k0 − kmin)`, `penal = 4.0`
- **Volume constraint:** 30% via Optimality Criteria update
- **Density filter:** linear hat with radius `rmin` (prevents checkerboarding,
  enforces minimum feature size)
- **Boundary conditions:** Dirichlet T=0 at sink nodes on left wall
  (rows `0.4·nely` to `0.6·nely`); uniform heat source `F = 0.01` at every node

## Manufacturability post-processing

After optimization, the continuous density `x` is binarized (volume-preserving
quantile threshold on a Gaussian-smoothed copy) and run through four checks:

1. **Connectivity** — `scipy.ndimage.label` finds all solid components; only
   the one(s) touching the cold-sink edge are kept. Floating islands are
   reported and discarded.
2. **Enclosed voids** — `binary_fill_holes` fills any cavity that does not
   reach the part perimeter, so the geometry can be made in a single
   stamping blow with no secondary pierce operations.
3. **Corner fillet** — `binary_closing` with a disk kernel of radius
   `round(rmin / 2)` rounds 90° internal corners and bridges threshold
   pinholes. Uses `border_value=1` so the sink edge isn't eroded.
4. **Member width audit** — distance transform + local-maxima medial axis
   reports min and max member widths, validated against the `rmin` target.

Then the practical design's thermal compliance is recomputed and compared to
the ideal binary design. The compliance penalty from cleanup is overlaid on
the video.

## Video sequence

Each video walks through five phases:

1. Intro — 3-second hold on the initial uniform density
2. SIMP optimization iterations
3. Cross-dissolve to ideal binarized topology
4. Cross-dissolve to practical (cleaned-up) topology
5. Hold on practical design with the 4-check report overlaid

## Reference: baseline vs hi-res

| Metric                       | 80 × 50 | 160 × 100 |
|---|---|---|
| Final `change` at cap        | 0.0252  | 0.0193    |
| `fillet_r` (auto-scaled)     | 2       | 3         |
| Islands dropped              | 0       | 0         |
| Enclosed voids filled        | 0       | 0         |
| Min member width             | 2.8 px  | 2.0 px    |
| Max member width             | 19.7 px | 41.2 px   |
| Practical volume fraction    | 0.304   | 0.302     |
| Practical penalty vs ideal binary | +0.4% | +0.25% |

The hi-res mesh cuts the cleanup penalty by ~40% — finer boundary resolution
means smaller stair-stepping artifacts at the threshold step.

## Known limitations

- **Convergence.** Plain OC chatters at fine resolution; neither script
  reaches `change < 0.01` within its iteration cap. Topology is visually
  stable well before that. A move-limit damper or MMA replacement would fix
  this if needed.
- **Continuous-vs-binary gap.** The `+60,000%` compliance gap between the
  continuous SIMP optimum and the binary design is an artifact of grey
  intermediate-density material providing nonzero conduction in SIMP. The
  *meaningful* comparison is practical-vs-ideal-binary (the cleanup penalty).
  Heaviside projection during optimization would close this gap but
  destabilizes the simple OC update.
- **2D only.** The result is the in-plane silhouette of a constant-thickness
  sheet, not a 3D heat sink with fins. Realistic use cases: stamped /
  laser-cut spreader plates, vapor chamber backing plates, busbars.
