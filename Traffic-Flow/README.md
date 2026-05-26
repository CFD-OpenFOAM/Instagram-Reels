# Traffic Flow

A series of Python simulations exploring traffic as a **fluid-dynamic system**. Each project isolates one phenomenon — a phantom jam, a bottleneck, a control policy, a geometric choice — and renders it as an interactive matplotlib animation.

All sims share a common philosophy: traffic is not about cars, it's about *flow*. The same equations that describe shockwaves in compressible gas describe queues at a red light. The same nozzle physics that describes choked flow describes a toll plaza.

---

## The series

### [1 — Phantom Traffic Jams](./1-Phantom-Traffic-Jams/)
Two identical circular roads. One car taps the brakes. On one ring the wave damps out; on the other, a single overreactive "damper" driver amplifies it into a self-sustaining backward-propagating shockwave. The Bando optimal-velocity model in action.

**Key idea:** Jams emerge from instability, not from causes.

### [2 — Toll Plaza Bottleneck](./2-Toll-Plaza-Bottleneck/)
3 entrance lanes → 6 toll booths → 3 exit lanes. Cars load-balance across booths, decelerate through them, then fight for gaps on the merge-back. Demonstrates that the *exit merge* is often a worse bottleneck than the booths themselves.

**Key idea:** Widening then narrowing a flow channel creates shocks on both sides.

### [3 — Green Wave Signals](./3-Green-Wave-Signals/)
A multi-lane corridor with 3 traffic lights. Toggle between synchronized green-wave timing (cars surf through all greens at the speed limit) and random unsynced timing (stops, queues, shockwaves). Override individual lights to inject perturbations and watch the wave propagate.

**Key idea:** A traffic light is a static, flow-blind controller. The cheapest possible intelligence — phase offsets matched to the speed limit — eliminates most of the damage.

### [4 — Intersection vs Roundabout](./4-Intersection-vs-Roundabout/)
Side-by-side: identical inflow into a signalized 4-way intersection vs a yield-controlled roundabout. Live tracker shows cumulative kinetic energy destroyed by braking. The intersection accumulates a glowing red "heat sink" at the stop bars; the roundabout stays cyan.

**Key idea:** Sometimes you don't need smarter algorithms — you need different geometry. 90° shear becomes tangential merge.

---

## Through-lines

| Theme                | 1 | 2 | 3 | 4 |
|----------------------|---|---|---|---|
| Shockwaves           | ● | ● | ● |   |
| Bottleneck geometry  |   | ● |   | ● |
| Control policy       |   |   | ● | ● |
| Kinetic energy loss  |   |   |   | ● |
| Driver heterogeneity | ● |   |   |   |

Each sim is self-contained — pick any folder and run its single Python file. Sims 2–4 include sliders and buttons; sim 1 renders directly to MP4.

## Requirements
```
numpy
matplotlib
```

## Run any project
```
cd <folder-name>
python <script.py>
```
