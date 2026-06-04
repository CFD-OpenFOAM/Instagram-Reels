# Parametric Heat Sink Optimizer: Choked Flow Visualization

This project features a Python-based physical simulation and visualization tool that demonstrates the concept of **"choked flow"** in heat sink design. It visually explains the engineering trade-off between maximizing surface area (adding more fins) and maintaining adequate convective airflow.

## Overview

When designing a heat sink, a common misconception is that adding more fins will always increase cooling performance. However, as the gap between fins decreases, the boundary layers of the airflow merge, drastically increasing flow resistance and eventually "choking" the air supply. 

This script mathematically models this phenomenon and generates an educational animation showing three states:
1. **Sparse (Too Little Area):** High airflow, but not enough metal surface to dissipate heat.
2. **Optimal (The Peak):** The perfect balance where airflow velocity and surface area maximize total convective cooling.
3. **Overpacked (Choked Flow):** Massive surface area, but air cannot penetrate the dense fins and violently deflects around the outside, causing thermal failure.

## Features

* **Physics & Math Model:** Calculates surface area scaling and exponential airflow drop-off based on boundary layer thickness thresholds.
* **Custom Particle Engine:** Simulates 2D fluid dynamics, visually showing air particles passing through or deflecting off the fins based on aerodynamic drag.
* **Optimization Graph:** Plots real-time performance curves highlighting the mathematical "peak" of cooling efficiency.
* **Automated Video Export:** Renders the simulation into a high-quality, 30fps `.mp4` video format.

## Prerequisites

To run this simulation, you will need Python 3 installed along with the following libraries:

```bash
pip install numpy matplotlib