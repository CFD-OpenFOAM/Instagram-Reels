# Heat Exchanger Thermal Profile Simulator

A lightweight, interactive Python visualization of a 1D heat exchanger's thermal profile. This tool uses `matplotlib` to plot the temperature changes of hot and cold fluids as they travel along the length of a pipe.

It is designed with a 9:16 portrait aspect ratio, making it ideal for mobile viewing or vertical monitor setups.

---

## 🚀 Features

* **Interactive Simulation:** Instantly visualize how changing the pipe length (NTU) affects the heat transfer using a built-in UI slider.
* **Dual Flow Modes:** Toggle between **Parallel Flow** and **Counter-Flow** to see the dramatic difference in thermal efficiency.
* **Visual Cues:** The cold fluid line changes to a dashed style during Counter-Flow to visually indicate the reversed flow direction.

---

## 📊 Flow Modes Comparison

| Feature | Parallel Flow | Counter-Flow |
| --- | --- | --- |
| **Fluid Entry** | Both fluids enter at the same end ($x=0$). | Fluids enter at opposite ends. |
| **Heat Transfer** | High initial heat transfer, tapering off. | Constant temperature gradient. |
| **Efficiency** | Lower max efficiency. Cold fluid can never exceed the exit temp of the hot fluid. | Higher efficiency. Cold fluid exit temperature can exceed the hot fluid exit temperature. |
| **Visual Line Style** | Solid Line (`-`) | Dashed Line (`--`) |

---

## 🧮 The Physics Model

This simulation uses simplified mathematical models to determine the temperature of the hot fluid ($T_h$) and cold fluid ($T_c$) at any given position $x$ along the pipe (where $x$ ranges from $0$ to $1$). The **Number of Transfer Units (NTU)** acts as the proxy for pipe length and heat transfer area.

Boundary conditions are set to $100^\circ\text{C}$ for the hot fluid inlet and $20^\circ\text{C}$ for the cold fluid inlet.

### Parallel Flow Equations

The temperatures experience exponential decay towards the average temperature of the two fluids:

$$T_h(x) = T_{h,in} - \frac{T_{h,in} - T_{c,in}}{2} \left(1 - e^{-2 \cdot \text{NTU} \cdot x}\right)$$

$$T_c(x) = T_{c,in} + \frac{T_{h,in} - T_{c,in}}{2} \left(1 - e^{-2 \cdot \text{NTU} \cdot x}\right)$$

### Counter-Flow Equations

Assuming balanced heat capacity rates, the temperatures follow a linear gradient:

$$T_h(x) = T_{h,in} - (T_{h,in} - T_{c,in}) \left(\frac{\text{NTU}}{1 + \text{NTU}}\right) x$$

$$T_c(x) = T_h(x) - \frac{T_{h,in} - T_{c,in}}{1 + \text{NTU}}$$

---

## 💻 Installation and Setup

### Prerequisites

You need Python installed on your system along with the following libraries:

* `numpy`
* `matplotlib`

### Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/heat-exchanger-sim.git
cd heat-exchanger-sim

```


2. **Install dependencies:**
```bash
pip install numpy matplotlib

```


3. **Run the script:**

```bash
    python heat_exchanger.py
    ```

---

## 🛠️ Usage Guide

> **Note:** Because this script relies on `matplotlib.widgets`, it needs to be run in an environment that supports GUI windows (e.g., your local terminal, Spyder, or VS Code desktop). It will not be interactive inside standard static Jupyter Notebook web outputs without specific magic commands like `%matplotlib notebook` or `%matplotlib widget`.

1.  **Adjust Pipe Length (NTU):** Click and drag the slider at the bottom of the window. Moving it to the right simulates a longer pipe, allowing the fluids more time to exchange heat.
2.  **Switch Modes:** Click the **Mode** button at the very bottom to alternate between Parallel Flow and Counter-Flow physics.

```