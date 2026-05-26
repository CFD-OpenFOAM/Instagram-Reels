# Intersection vs Roundabout

Side-by-side simulation of identical traffic streams fed into a **signalized 4-way intersection** (left) and a **yield-controlled roundabout** (right). Same inflow, same speeds, same car-following physics — only the geometry of the control regime differs.

## The concept

A traffic light **destroys kinetic energy** by demanding `v → 0` on red, then forces the system to rebuild momentum from zero on green. A roundabout converts the perpendicular 90° shear collision into a **tangential merge**, letting cars retain most of their kinetic energy as they sweep through the curve.

The simulation makes this visible: the intersection accumulates red dots at the stop bars, the roundabout stays mostly green/cyan even under heavy load.

## The physics
- **Intersection**: alternating NS / EW green phases; cars decelerate quadratically to a stop bar at distance `R` from center
- **Roundabout**: 180° CCW arc through the circle. Entry cars yield if any circulating car is within `yield_gap` arc-distance of the entry point. On-arc cars follow the nearest leader CCW, regardless of origin
- **Velocity heatmap**: cyan (full speed) → yellow → red (stopped)
- **Energy destruction tracker**: cumulative `∑ ½(v_old² - v_new²)` across all cars and frames — a direct measure of brake heat dissipated

## Interactive controls
- **Inflow** (cars/sec per direction)
- **Signal cycle** (intersection only)
- **Roundabout yield gap** (how cautiously entry cars yield)
- **Max speed**
- **Show Conflict Points** — overlays 32 dots on the intersection vs 8 on the roundabout
- **Stress Test** — ramps inflow continuously to find each system's breaking point
- **Pause / Reset**

## What to watch
- Live banner: `Roundabout saves X% of kinetic energy vs Intersection`
- Stopped-car counts diverge dramatically as inflow rises
- Under stress test, the intersection backs up first; the roundabout degrades gracefully until it saturates

## Files
- `traffic-flow-4.py`

## Run
```
python traffic-flow-4.py
```
