# The Drunk Robot: PID Controller Simulator 🚁

An interactive, mobile-optimized (9:16 portrait) educational physics simulator designed to visually teach the mechanics of a **Proportional-Integral-Derivative (PID) Controller**.

This script creates a 1D physics environment where a "drone" attempts to stabilize at a target altitude. By tuning the P, I, and D parameters in real-time, users can observe how control systems manage momentum, damping, and steady-state errors (like gravity or wind).

## Features

* **Real-Time Tuning:** Dynamically adjust P, I, and D sliders while the simulation is running.
* **Locked-Camera Graph:** The timeline dynamically scrolls, keeping the drone perfectly centered on the screen—ideal for screen recording and mobile viewing.
* **Wind Gust Simulation:** Introduce sudden external forces (downdrafts) to test the robustness of your tuning (and demonstrate the necessity of the Integral term).
* **B-Roll Ready:** Includes Play/Pause and Reset controls for staging perfect educational "takes."

## Prerequisites

To run this simulator, you will need **Python 3.x** and the following libraries:

* `numpy`
* `matplotlib`

You can install these dependencies using pip:

```bash
pip install numpy matplotlib

```

## How to Run

### 1. From the Command Line / Terminal

Simply execute the Python script from your terminal:

```bash
python drunk_robot.py

```

A native interactive window will pop up with the simulation.

### 2. From Jupyter Notebook

If you are running this inside a Jupyter Notebook, you **must** use an interactive matplotlib backend for the sliders and animations to work. Add the following magic command to the very top of your cell before running the code:

```python
%matplotlib tk 

```

*(Note: If you are using JupyterLab or VS Code, you may need to use `%matplotlib widget` and ensure `ipympl` is installed).*

## How to Use the Simulator (The 3 Stages of Tuning)

1. **The Drunk Robot (Proportional - P):**
* Set `P = 2.0`, `I = 0.0`, `D = 0.0`.
* **Observe:** The drone overshoots the target altitude, panics, and oscillates wildly like a pendulum. Proportional control knows *where* to go, but ignores momentum.


2. **The Brakes (Derivative - D):**
* Increase `D` to `~5.0` (Leave `P = 2.0`).
* **Observe:** The violent oscillations instantly dampen. The Derivative term calculates how fast the error is closing and applies the brakes *before* the drone overshoots.


3. **The Nudge (Integral - I):**
* Hit the **Wind Gust** button to push the drone down. With only P and D active, the drone will stabilize *below* the target line (Steady-State Error).
* Increase `I` to `~1.5`.
* **Observe:** The drone slowly and smoothly creeps back up to perfectly match the target line. The Integral term "remembers" past errors and builds up the force needed to overcome constant resistance.



## Project Context

This tool was built to generate visual assets for the **Wrench-Wise** educational engineering platform. It is designed to bridge the gap between heavy mathematical control theory and intuitive, visual learning.