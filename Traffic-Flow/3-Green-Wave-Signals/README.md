# Green Wave Signals

A multi-lane corridor with three traffic lights. Toggle between **synchronized "green wave"** timing (where lights cascade at the speed limit, letting a platoon surf through all three on green) and **unsynchronized** timing (random offsets, forcing stops and shockwaves).

## The concept

A traffic light is a **static control system** — blind to actual flow. Whether one lane has 50 cars and the other has zero, red still means red. The "green wave" is the cheapest possible intelligence layer: phase-shift each downstream light by `Δx / v_max`, so a car cruising at the speed limit hits every green.

## The physics
- **Per-light cycle**: green for `GREEN_FRACTION × CYCLE_PERIOD`, then red
- **Green wave offset**: `offset_i = (x_i - x_0) / v_max mod cycle`
- **Approach deceleration**: cars decel quadratically when within `APPROACH_DIST` of a red light
- **Car-following**: lane-local, gap-based speed reduction
- **Shockwave detection**: counts cars at near-zero velocity; triggers a backward-propagating wave label

## Interactive controls
- **Green Wave toggle** (synced vs unsynced)
- **Light overrides** (force each light Auto / Red / Green to inject perturbations)
- **Sliders**: max speed, signal cycle period, car density, number of lanes (1–6)

## What to watch
- Green wave ON, default speed: cars surf through all 3 lights, no shockwave
- Green wave OFF: random stops form, queues build, shockwaves ripple backward
- Add lanes under high density: throughput barely improves — the *lights* are the bottleneck, not the lane count

## Files
- `traffic-flow-3.py`

## Run
```
python traffic-flow-3.py
```
