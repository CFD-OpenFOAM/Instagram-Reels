```markdown
# 🌪️ The Invisible Hammer: LBM Vortex Shedding Simulation

Welcome to the digital wind tunnel. This repository contains the complete Python source code for simulating a **Von Kármán Vortex Street** using the Lattice Boltzmann Method (LBM). 

This simulation is part of the **Wrench-Wise** educational series and the **Physics By Design** curriculum, aimed at bridging the gap between idealized digital theory and the destructive, real-world physics that engineers face every day.

## The Physics: What is Vortex Shedding?
When fluid (like wind or water) hits a blunt object (like a skyscraper, a power line, or a bridge support) at a specific velocity, it doesn't just split cleanly. The intense shear stress causes the fluid to roll up and snap off into alternating whirlpools of low pressure. 

These whirlpools create massive, alternating vacuums that physically suck the structure back and forth. It acts like an invisible hammer. If the rhythm of these alternating whirlpools matches the structure's natural frequency, the resulting **resonance** can literally tear steel apart—which is exactly what caused the infamous Tacoma Narrows Bridge collapse.

## The Math: Lattice Boltzmann Method (LBM)
Unlike traditional Computational Fluid Dynamics (CFD) solvers that iteratively crunch massive Navier-Stokes equations on complex meshes, this script uses **LBM**. 

It divides the fluid into a uniform grid (a D2Q9 lattice) and simulates packets of digital particles "streaming" to neighboring nodes and "colliding." It is highly efficient and visually stunning.

### Key Simulation Parameters in the Code:
* **`Re = 100` (Reynolds Number):** This is the sweet spot. It is the exact mathematical threshold where the fluid stops flowing smoothly and begins violently snapping into alternating whirlpools.
* **Obstacle Bounce-Back:** The code enforces a "no-slip" condition on the central cylinder. When digital air particles hit the grey wall, they completely stop, creating the shear stress needed for the vortices.
* **Curl Calculation:** The script calculates the rotational "spin" in the fluid, separating the whirlpools into alternating red (positive spin) and blue (negative spin) zones.

## How to Run the Simulation

### Prerequisites
You only need a standard Python installation and two core scientific libraries. 
```bash
pip install numpy matplotlib

```

### Execution

Run the script directly from your terminal.

```bash
python LBM_Vortex_Shedding.py

```

### What to Expect

1. The terminal will output `LBM Started | Re=100.0 | Tau=0.515 | Slip Walls Active`.
2. The solver will iterate through 4,000 timesteps (printing progress every 500 steps).
3. Once the math is complete, it will automatically render and save an animated file named `LBM_Vortex_Shedding_Slip.gif` directly to your folder.

## Sandbox Mode (Things to Tweak)

This code is meant to be broken and explored. Open the script and try changing these variables in **SECTION 1**:

* `Re = 10.0`: Watch what happens when the Reynolds number is too low (Hint: The fluid hugs the cylinder smoothly and no whirlpools form).
* `u_max = 0.15`: Increase the inlet velocity.
* `r_cyl`: Change the size of the obstacle to see how it affects the vortex frequency!

## About Physics By Design

This code is provided as a practical, hands-on tool for the **Physics By Design** curriculum. Our goal is to teach the next generation of engineers how to build, simulate, and understand the physical constraints of the real world before they ever hit the factory floor.