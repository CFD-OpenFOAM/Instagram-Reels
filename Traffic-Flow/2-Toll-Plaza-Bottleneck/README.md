# Toll Plaza Bottleneck

An interactive simulation of a toll plaza: 3 entrance lanes funnel into 6 slow toll booths, then merge back into 3 exit lanes. Demonstrates why adding more booths only helps up to a point — the merge geometry on the *exit* side is the real bottleneck.

## The concept

A toll plaza is a Bernoulli-like constriction in reverse: the road *widens* into many slow channels, then *narrows* back. Cars accelerate hard on exit, divert across lanes to find gaps, and the whole structure behaves like a compressible flow through a nozzle — with shockwaves forming on both approach and exit sides under load.

## The physics
- **Lane divergence**: cars choose the shortest toll queue (load-balancing across booths)
- **Speed drop**: each booth enforces `V_TOLL ≪ V_MAX`
- **Lane convergence**: on exit, two toll lanes feed into one exit lane — cars must wait for gaps
- **Smoothstep funnel geometry**: plaza width varies smoothly from `W_road → W_plaza → W_road`

## Interactive controls
- Inflow density (cars in system)
- Max speed
- Lane balance / divert threshold (in code constants)

## What to watch
- Under low load: cars sweep through smoothly
- Under high load: queue forms *before* the booths, then a second queue forms at the *exit merge* — that's the true bottleneck

## Files
- `traffic-flow-2.py` — simulation with sliders

## Run
```
python traffic-flow-2.py
```
