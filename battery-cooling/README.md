# EV Battery Thermal Management Simulator

A real-time, interactive 2D thermal simulation of an Electric Vehicle (EV) battery pack during DC fast charging. Built entirely in Python using `numpy` and `matplotlib`, this dashboard visualizes heat generation, conductive heat transfer, and active liquid cooling in a battery module.

## Features

* **Real-Time 2D Heatmap:** Visualizes the temperature distribution across a cross-section of battery cells and cooling channels.
* **Interactive Controls:** Dynamically adjust parameters mid-simulation using sliders:
* **Charge Power (kW):** Simulates the heat load from DC fast charging.
* **Coolant Flow (L/min):** Adjusts the effectiveness of the liquid cooling channels.
* **Coolant Temp (°C):** Sets the baseline temperature of the incoming coolant.


* **Live Telemetry & Warnings:** Monitors the max core temperature and provides visual warnings for:
* **Cell Degradation** (> 45°C)
* **Thermal Runaway Risk** (> 60°C)


* **Historical Tracking:** A live-updating plot charts the maximum cell temperature over time to visualize heating curves and steady states.
* **Scenario Testing:** Quick-action buttons to test edge cases like "Cooling Failure" or "Max Charge".

## Prerequisites

This script requires a standard Python environment with `numpy` and `matplotlib`.

You can install the required dependencies using pip:

```bash
pip install numpy matplotlib

```

*Note: Because this relies on Matplotlib's interactive widgets and animations, it must be run in an environment that supports GUI window pop-ups. If you are using Jupyter Notebook, you may need to set your backend to an interactive mode (e.g., `%matplotlib qt`).*

## Usage

1. Save the script as a Python file, for example, `ev_thermal_sim.py`.
2. Run the script from your terminal:

```bash
python ev_thermal_sim.py

```

3. The Matplotlib window will open. Use the sliders at the bottom left to change the system parameters in real time.
4. Use the buttons on the bottom right to trigger specific test scenarios.

## Controls & Scenarios

### Sliders

* **Charge (kW):** Range from 50 to 350 kW. Higher charge rates generate more waste heat based on a 95% efficiency assumption.
* **Coolant (L/min):** Range from 0 to 100. Higher flow rates extract heat from the cooling channels faster.
* **Coolant Temp (°C):** Range from 5 to 40°C. Lower temperatures provide a stronger thermal gradient for cooling.

### Scenario Buttons

* **Reset:** Clears the thermal history and resets the grid to an ambient 25°C.
* **Max Charge:** Cranks the charge power to 350 kW while maintaining standard cooling.
* **Cool Fail:** Drops the coolant flow to 0 L/min, simulating a pump failure during charging.
* **Normal:** Returns to a standard 150 kW charge with 10 L/min cooling at 20°C.

## How it Works (Under the Hood)

The simulation uses an explicit Euler finite-difference method to solve the 2D heat equation across a grid (`nx=90`, `ny=120`).

* **Battery Cells:** Waste heat is uniformly injected into the masked battery regions based on the selected charge power. Heat dissipates via standard 2D Laplacian diffusion.
* **Cooling Channels:** An unconditionally stable implicit Newton cooling model is applied to the masked cooling channels, allowing them to rapidly extract heat without violating the CFL stability condition of the simulation.
* **Sub-stepping:** To maintain numerical stability while providing a smooth visual framerate, the physics engine runs multiple sub-steps per visual animation frame.