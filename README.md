# Instagram-Reels

A showcase of Python-based engineering, physics, and numerical-method visualization tools created for short-form educational content.

These projects are designed to make technical ideas easier to see, explore, and explain — whether through simulation, interactive controls, or rendered animation optimized for vertical video formats.

## What this repository contains

Each folder in this repository is a self-contained utility focused on a different engineering or science concept. Together, they form a small library of visual demos for topics such as control systems, heat transfer, optimization, acoustics, traffic dynamics, and fluid mechanics.

## Project showcase

| Utility | Focus area | What it demonstrates |
|---|---|---|
| [`Maze-Runner/`](./Maze-Runner/) | Numerical methods / pathfinding | Random maze generation, Laplacian heat diffusion, and gradient-based path tracing rendered as an animation. |
| [`PID-Drunk-Robot/`](./PID-Drunk-Robot/) | Control systems | Real-time PID tuning for a 1D stabilization problem, showing overshoot, damping, and steady-state correction. |
| [`heat-exchanger/`](./heat-exchanger/) | Heat transfer | Interactive comparison of parallel-flow and counter-flow heat exchanger temperature profiles. |
| [`Sound-Waves/`](./Sound-Waves/) | Acoustics / signal processing | Audio visualization using both frequency-domain analysis and particle-based wave motion. |
| [`Topology-Optimization/`](./Topology-Optimization/) | Structural optimization | SIMP-based cantilever beam topology optimization using finite element analysis and material removal. |
| [`Traffic-Flow/`](./Traffic-Flow/) | Traffic dynamics | A set of simulations showing phantom jams, bottlenecks, signal timing effects, and geometric traffic design tradeoffs. |
| [`Vortex-Shedding/`](./Vortex-Shedding/) | Fluid dynamics | Lattice Boltzmann simulation of Von Kármán vortex shedding behind a bluff body. |
| [`battery-cooling/`](./battery-cooling/) | Thermal management | Interactive EV battery cooling simulation showing heat buildup, coolant effects, and thermal risk thresholds. |

## Utilities overview

### Maze Runner

A physics-inspired maze solver that combines random maze generation with Laplacian heat diffusion. Instead of using a traditional shortest-path algorithm directly, it constructs a temperature field through the maze and follows the resulting gradient to recover the solution path.

This project is especially useful as a visual explanation of potential fields, diffusion-based reasoning, and algorithmic animation.

### PID Drunk Robot

An interactive simulator for understanding PID control in an intuitive way. By adjusting proportional, integral, and derivative gains live, users can see how each term changes the behavior of a drone-like system attempting to hold a target altitude.

It works well as a teaching aid for control theory because it turns abstract tuning concepts into visible motion and response curves.

### Heat Exchanger

A compact heat-transfer visualization that compares how hot and cold fluid temperatures evolve in parallel-flow versus counter-flow exchangers. The interactive controls help show why exchanger geometry and flow arrangement matter.

It is a practical demo for explaining thermal gradients, exchanger efficiency, and introductory heat-transfer design concepts.

### Sound Waves

A sound visualization tool that links audio signals to physical wave behavior. It combines spectral analysis with a particle-based rendering of longitudinal wave motion, helping bridge the gap between signal-processing plots and physical intuition.

This makes it a strong educational utility for explaining both what sound looks like mathematically and what it means physically.

### Topology Optimization

A structural design utility that uses SIMP-based topology optimization to evolve a cantilever beam toward an efficient load-bearing form. Material is progressively removed from low-value regions while the key structural paths remain.

It demonstrates the connection between optimization algorithms, finite element analysis, and lightweight engineering design.

### Traffic Flow

A collection of traffic simulations that treats vehicle systems as flow systems. Different scenarios explore how instabilities, bottlenecks, light timing, and roadway geometry create congestion patterns and shockwaves.

These examples are especially useful for showing that traffic problems often emerge from system-level dynamics rather than isolated driver decisions.

### Vortex Shedding

A fluid simulation focused on Von Kármán vortex streets, showing how alternating vortices form downstream of a bluff body. The implementation uses the Lattice Boltzmann Method to create an accessible and visually striking CFD-style demonstration.

It is well suited for explaining unsteady wakes, aerodynamic forcing, and flow-induced vibration in engineering systems.

### Battery Cooling

An interactive EV battery thermal-management simulator that visualizes heat generation and extraction during fast charging. Users can vary charge power, coolant flow, and coolant temperature to see how the pack responds over time.

This utility helps explain practical thermal-design tradeoffs, cooling effectiveness, and safety-related temperature thresholds in battery systems.

## Common characteristics

Across the repository, the utilities are generally:

- Written in **Python**
- Built around **simulation, visualization, and numerical methods**
- Intended for **interactive learning** or **educational animation**
- Designed to support **vertical/video-friendly engineering demonstrations**

## Repository structure

- `README.md` — root showcase and repository overview
- `Maze-Runner/` — maze generation, diffusion-based solving, and animation
- `PID-Drunk-Robot/` — PID control simulator
- `heat-exchanger/` — heat exchanger thermal profile visualizer
- `Sound-Waves/` — sound and wave propagation visualizer
- `Topology-Optimization/` — structural optimization demo
- `Traffic-Flow/` — traffic dynamics simulation series
- `Vortex-Shedding/` — vortex shedding and wake simulation
- `battery-cooling/` — EV battery thermal management simulator
