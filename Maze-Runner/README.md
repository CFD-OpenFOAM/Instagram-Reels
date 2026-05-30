# Maze Runner — Laplacian Heat-Diffusion Maze Solver

A Python script that **generates a random solvable maze**, solves it using **Laplacian heat diffusion** (a physics-based approach), and renders an animated MP4 video of the entire process — from heat spreading through corridors to a glowing neon path tracing the solution.

## How It Works

The pipeline has four stages:

### 1. Random Maze Generation (Recursive Backtracker / DFS)

A perfect maze (exactly one path between any two cells) is carved using the **recursive backtracker** algorithm:

1. Start with a solid grid where every cell is a wall.
2. Pick a starting cell, mark it as visited, and push it onto a stack.
3. While the stack is not empty:
   - Look at the current cell's unvisited neighbours (up / down / left / right).
   - If any exist, **randomly** choose one, remove the wall between them, mark the neighbour as visited, and push it onto the stack.
   - If none exist, backtrack by popping the stack.
4. Punch an **entrance** at the bottom-centre and an **exit** at the top-centre of the grid.

The cell grid is `cell_rows × cell_cols` (default 9 × 7), which maps to a wall grid of size `(2N+1) × (2M+1)` = **19 × 15**. Every run produces a different maze unless a fixed `seed` is provided.

### 2. Laplacian Heat Diffusion

The maze is treated as a thermal system:

- The **entrance** (bottom) is held at **100 °** (hot boundary).
- The **exit** (top) is held at **0 °** (cold boundary).
- Walls are perfect insulators.
- Heat diffuses iteratively through open passages using a 4-neighbour averaging stencil (discrete Laplace equation) for **4 000 iterations**.

At equilibrium the temperature field forms a smooth gradient from start to exit — steep through the solution corridor, nearly flat in dead-ends.

### 3. Gradient-Descent Pathfinder

Starting at the entrance, the solver greedily steps to the neighbouring cell with the **lowest temperature** at each point. Because the Laplacian guarantees a monotonically decreasing potential along the true shortest path, gradient descent recovers the optimal route without any graph search.

### 4. Animated Video Rendering

The output is a **30 fps MP4** with two phases:

| Phase | Content |
|-------|---------|
| Heat diffusion | The temperature field fills the maze in real time (custom purple → magenta → amber → white-hot colourmap). |
| Path trace | A **6-layer neon-glow cyan line** (outer bloom → bright white core) draws the solution path, with a green dot at the entrance and a gold star at the exit. |

A 2-second hold at the end lets the viewer admire the result.

## Dependencies

| Package | Purpose |
|---------|---------|
| **Python 3.8+** | Runtime |
| **NumPy** | Grid operations, heat diffusion math |
| **Matplotlib** | Rendering frames, animation, custom colourmaps |
| **FFmpeg** | Video encoding (must be on `PATH`) |

Install the Python packages:

```bash
pip install numpy matplotlib
```

FFmpeg must be installed separately and available on your system `PATH`:

- **Windows (conda):** `conda install -c conda-forge ffmpeg`
- **Windows (manual):** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add the `bin/` folder to `PATH`.
- **Ubuntu / Debian:** `sudo apt install ffmpeg`
- **macOS:** `brew install ffmpeg`

## Usage

```bash
python maze_solver.py
```

This will:

1. Generate a new random maze.
2. Run 4 000 iterations of heat diffusion.
3. Trace the optimal path.
4. Save the animation as **`laplacian_maze.mp4`** in the working directory.

### Customisation

Edit the `generate_maze()` call near the top of the script:

```python
# Bigger maze (15×11 cells → 31×23 grid)
maze, start_pos, end_pos = generate_maze(cell_rows=15, cell_cols=11)

# Reproducible maze (same layout every time)
maze, start_pos, end_pos = generate_maze(cell_rows=9, cell_cols=7, seed=42)
```

Other tunables:

| Variable | Default | Effect |
|----------|---------|--------|
| `cell_rows`, `cell_cols` | 9, 7 | Maze complexity. Grid becomes `(2N+1) × (2M+1)`. |
| `seed` | `None` | Fix the random seed for reproducible mazes. |
| `iterations` | 4000 | Heat diffusion steps. Increase for larger mazes. |
| `bitrate` | 3000 | Video quality (kbps). |
| `figsize` | (4.5, 8) | Output aspect ratio (width, height in inches). |

## Output

The script prints progress to the console:

```
Generating random maze...
  Grid size: 19x15  |  Start: (18, 7)  |  Exit: (0, 7)
Running Laplacian heat diffusion...
Tracing optimal path...
  Path length: 43 steps
Rendering video...
Done! Video saved as laplacian_maze.mp4
```
