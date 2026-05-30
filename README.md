# Instagram-Reels

Tools built during demonstration on reels.

## Utilities in this repository

This repository contains a collection of Python-based educational and visualization utilities created for short-form engineering and science content. Each folder explores a different concept through simulation, animation, or interactive visual explanation.

### Maze-Runner

`Maze-Runner/` is a maze generation and solving utility built around a physics-inspired approach. It creates a random solvable maze, applies Laplacian heat diffusion across the open paths, and then traces the solution by following the temperature gradient.

The project also renders the full process as an animated video, making it useful both as a numerical methods demo and as a visually engaging explanation of potential-field-based pathfinding.

### PID-Drunk-Robot

`PID-Drunk-Robot/` is an interactive control systems simulator that demonstrates how a PID controller stabilizes a simple 1D drone or robot altitude problem. Users can tune the proportional, integral, and derivative gains in real time and immediately observe overshoot, damping, and steady-state correction.

It is designed as a teaching tool for control theory, with an interface optimized for visual demonstrations and screen-recorded educational content.

### heat-exchanger

`heat-exchanger/` visualizes the temperature profiles of a 1D heat exchanger using simplified thermal models. It allows users to compare parallel-flow and counter-flow operation and see how exchanger length affects thermal performance.

This utility is helpful for explaining heat transfer fundamentals, exchanger efficiency, and the practical difference between common flow arrangements.

### Sound-Waves

`Sound-Waves/` is a sound visualization utility that turns audio into a combined spectral and particle-based animation. It shows both the frequency content of sound and a physical-style representation of longitudinal wave motion through moving particles.

The project focuses on making sound feel tangible, connecting signal processing concepts like FFTs with an intuitive visual model of pressure-wave propagation.

### Topology-Optimization

`Topology-Optimization/` demonstrates structural topology optimization for a cantilever beam using the SIMP method. Starting from a full design region, it iteratively removes inefficient material while preserving the load paths needed to carry the applied force.

This utility highlights the relationship between finite element analysis, optimization, and lightweight structural design, and it produces animation output suitable for educational visualization.

### Traffic-Flow

`Traffic-Flow/` is a collection of traffic simulations that treats vehicle movement as a flow-dynamics problem. The scenarios include phantom traffic jams, toll plaza bottlenecks, signal timing effects, and roundabout-versus-intersection comparisons.

Together, these simulations explain how congestion, shockwaves, and control strategies emerge from the dynamics of many interacting drivers rather than from any single vehicle.

### Vortex-Shedding

`Vortex-Shedding/` simulates Von Kármán vortex shedding behind a bluff body using the Lattice Boltzmann Method. It visualizes the alternating vortices that appear when fluid flow separates and forms a repeating wake pattern.

This project is especially useful for explaining unsteady fluid dynamics, flow-induced vibration, and why oscillating aerodynamic forces can become important in real engineering systems.

### battery-cooling

`battery-cooling/` is an interactive EV battery thermal management simulator. It models heat generation during fast charging and shows how coolant flow rate, coolant temperature, and charging power influence the pack temperature field.

The utility is built to explain thermal design tradeoffs in battery systems, including cooling effectiveness, temperature hotspots, and safety thresholds such as degradation or runaway risk.

## Common themes

Across the repository, the utilities are generally:

- Written in **Python**
- Focused on **simulation, visualization, and numerical methods**
- Built for **interactive learning** or **educational animation**
- Designed to support **vertical/video-friendly engineering demonstrations**

## Repository structure

- `README.md` — repository overview
- `Maze-Runner/` — maze generation, heat-diffusion solving, and animation
- `PID-Drunk-Robot/` — PID control simulator
- `heat-exchanger/` — heat exchanger thermal profile simulator
- `Sound-Waves/` — sound and wave propagation visualization
- `Topology-Optimization/` — structural optimization demo
- `Traffic-Flow/` — traffic dynamics simulation series
- `Vortex-Shedding/` — fluid wake and vortex shedding simulation
- `battery-cooling/` — EV battery thermal management simulator
