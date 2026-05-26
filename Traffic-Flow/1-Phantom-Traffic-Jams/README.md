# Phantom Traffic Jams

A side-by-side simulation of two circular roads. Both start identical. One car taps the brakes once. The top ring recovers smoothly. The bottom ring — with a single "damper" car that overreacts — collapses into a self-sustaining shockwave that propagates backward through the platoon.

## The concept

Traffic on a closed loop with no obstacles, no lights, no merges. The jam appears out of nothing because of a single perturbation amplified by reaction-time lag. This is the canonical demonstration that congestion is a fluid-dynamic instability, not a "cause-and-effect" of any specific event.

## The physics

Uses the **Bando optimal velocity model**:

```
a_i = α · (V(Δx_i) - v_i)
```

where `V(Δx)` is a `tanh`-based optimal velocity as a function of headway to the car ahead. The damper car uses a higher sensitivity `α`, modelling an overreactive driver.

## What to watch
- A single brake-tap at frame 100 perturbs both rings identically
- The top ring damps the wave out within seconds
- The bottom ring builds a standing shockwave that travels *backward* relative to traffic flow at ~15 km/h — the classic "kinematic wave" speed

## Files
- `traffic_flow.py` — simulation
- `traffic_fluid.mp4` — rendered output

## Run
```
python traffic_flow.py
```
