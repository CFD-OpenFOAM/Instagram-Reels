import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
import random

# --- 1. RANDOM MAZE GENERATION (Recursive Backtracker / DFS) ---
def generate_maze(cell_rows=9, cell_cols=7, seed=None):
    """Build a guaranteed-solvable maze on a (2N+1)x(2M+1) grid."""
    if seed is not None:
        random.seed(seed)

    grid_rows = 2 * cell_rows + 1
    grid_cols = 2 * cell_cols + 1

    # Start with every cell walled off
    maze = np.ones((grid_rows, grid_cols), dtype=int)
    visited = np.zeros((cell_rows, cell_cols), dtype=bool)

    def cell_to_grid(r, c):
        return (2 * r + 1, 2 * c + 1)

    # --- DFS carve ---
    start_cell = (0, 0)
    visited[start_cell] = True
    gr, gc = cell_to_grid(*start_cell)
    maze[gr, gc] = 0
    stack = [start_cell]

    while stack:
        r, c = stack[-1]
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < cell_rows and 0 <= nc < cell_cols and not visited[nr, nc]:
                neighbors.append((nr, nc))

        if neighbors:
            nr, nc = random.choice(neighbors)
            # Remove the wall between current and chosen neighbour
            maze[2 * r + 1 + (nr - r), 2 * c + 1 + (nc - c)] = 0
            maze[cell_to_grid(nr, nc)] = 0
            visited[nr, nc] = True
            stack.append((nr, nc))
        else:
            stack.pop()

    # Punch entrance (bottom-centre) and exit (top-centre)
    entrance_gc = 2 * (cell_cols // 2) + 1
    exit_gc     = 2 * (cell_cols // 2) + 1
    maze[grid_rows - 1, entrance_gc] = 0
    maze[0, exit_gc] = 0

    start_pos = (grid_rows - 1, entrance_gc)
    end_pos   = (0, exit_gc)
    return maze, start_pos, end_pos


print("Generating random maze...")
maze, start_pos, end_pos = generate_maze(cell_rows=9, cell_cols=7)
rows, cols = maze.shape
print(f"  Grid size: {rows}x{cols}  |  Start: {start_pos}  |  Exit: {end_pos}")

# --- 2. HEAT-DIFFUSION SOLVER (Laplacian) ---
V = np.zeros((rows, cols))
path_mask = (maze == 0)
history = []
iterations = 4000

print("Running Laplacian heat diffusion...")
for i in range(iterations):
    if i % 40 == 0:
        history.append(V.copy())

    V_new = V.copy()

    V_up    = np.roll(V, 1, axis=0)
    V_down  = np.roll(V, -1, axis=0)
    V_left  = np.roll(V, 1, axis=1)
    V_right = np.roll(V, -1, axis=1)

    mask_up    = np.roll(path_mask, 1, axis=0)
    mask_down  = np.roll(path_mask, -1, axis=0)
    mask_left  = np.roll(path_mask, 1, axis=1)
    mask_right = np.roll(path_mask, -1, axis=1)

    mask_up[0, :]    = False
    mask_down[-1, :] = False
    mask_left[:, 0]  = False
    mask_right[:, -1] = False

    sum_V = (V_up * mask_up + V_down * mask_down
             + V_left * mask_left + V_right * mask_right)
    count = (mask_up.astype(int) + mask_down.astype(int)
             + mask_left.astype(int) + mask_right.astype(int))

    valid = path_mask & (count > 0)
    V_new[valid] = sum_V[valid] / count[valid]

    V_new[end_pos]   = 0.0
    V_new[start_pos] = 100.0
    V = V_new

history.append(V.copy())

# --- 3. GRADIENT-DESCENT PATHFINDER ---
print("Tracing optimal path...")
path = [start_pos]
current = start_pos
visited_set = {start_pos}

while current != end_pos:
    r, c = current
    best_step = current
    lowest_temp = V[current]

    for nr, nc in [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]:
        if (0 <= nr < rows and 0 <= nc < cols
                and path_mask[nr, nc] and (nr, nc) not in visited_set):
            if V[nr, nc] < lowest_temp:
                lowest_temp = V[nr, nc]
                best_step = (nr, nc)

    if best_step == current:
        print("Error: Pathfinder stuck!")
        break

    visited_set.add(best_step)
    path.append(best_step)
    current = best_step

print(f"  Path length: {len(path)} steps")

# --- 4. ENHANCED VIDEO RENDERING ---
print("Rendering video...")

fig, ax = plt.subplots(figsize=(4.5, 8))
fig.patch.set_facecolor('#06060e')
ax.set_facecolor('#06060e')
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_xlim(-0.5, cols - 0.5)
ax.set_ylim(rows - 0.5, -0.5)

# ---- Colour maps ----
# Heat: dark → deep purple → magenta → amber → white-hot
heat_cmap = LinearSegmentedColormap.from_list('heat', [
    '#06060e', '#1b0530', '#3d0a66', '#7b2d8e',
    '#c2185b', '#ff6f00', '#ffca28', '#fff9e6',
], N=256)


def get_rgb_frame(V_frame):
    norm_V = np.clip(V_frame / 100.0, 0, 1)
    colored = heat_cmap(norm_V)[:, :, :3]

    out = np.zeros((rows, cols, 3))
    out[~path_mask] = [0.07, 0.07, 0.11]   # dark walls
    out[path_mask]  = colored[path_mask]
    return out


img = ax.imshow(get_rgb_frame(history[0]), interpolation='nearest', zorder=0)

# ---- Glow-layered solution path (outer bloom → bright core) ----
glow_specs = [
    {'color': '#00ffff', 'alpha': 0.04, 'lw': 14},
    {'color': '#00ffff', 'alpha': 0.08, 'lw': 10},
    {'color': '#00e5ff', 'alpha': 0.15, 'lw': 7},
    {'color': '#00e5ff', 'alpha': 0.30, 'lw': 4.5},
    {'color': '#80ffff', 'alpha': 0.60, 'lw': 2.8},
    {'color': '#ffffff', 'alpha': 0.92, 'lw': 1.2},
]
glow_lines = []
for spec in glow_specs:
    ln, = ax.plot([], [], color=spec['color'], alpha=spec['alpha'],
                  lw=spec['lw'], solid_capstyle='round',
                  solid_joinstyle='round', zorder=2)
    glow_lines.append(ln)

# ---- Start / Exit markers ----
start_dot, = ax.plot([], [], 'o', color='#00ff88', markersize=11, zorder=5,
                     markeredgecolor='white', markeredgewidth=1.5)
exit_star, = ax.plot([], [], '*', color='#ffdd00', markersize=16, zorder=5,
                     markeredgecolor='white', markeredgewidth=1.0)

# Pre-compute path coords
path_y, path_x = zip(*path)


def update(frame):
    # --- Phase 1: heat diffusion animation ---
    if frame < len(history):
        img.set_data(get_rgb_frame(history[frame]))
        for ln in glow_lines:
            ln.set_data([], [])
        start_dot.set_data([], [])
        exit_star.set_data([], [])
        return [img] + glow_lines + [start_dot, exit_star]

    # --- Phase 2: path drawing ---
    idx = min(frame - len(history), len(path) - 1)
    img.set_data(get_rgb_frame(history[-1]))

    xs = path_x[:idx + 1]
    ys = path_y[:idx + 1]
    for ln in glow_lines:
        ln.set_data(xs, ys)

    start_dot.set_data([start_pos[1]], [start_pos[0]])
    if idx >= len(path) - 1:
        exit_star.set_data([end_pos[1]], [end_pos[0]])
    else:
        exit_star.set_data([], [])

    return [img] + glow_lines + [start_dot, exit_star]


total_frames = len(history) + len(path) + 60   # +2 s pause at the end

ani = animation.FuncAnimation(fig, update, frames=total_frames,
                              interval=33, blit=True)

writer = animation.FFMpegWriter(fps=30, metadata={'artist': 'Wrench-Wise'},
                                bitrate=3000)
ani.save('laplacian_maze.mp4', writer=writer)

print("Done! Video saved as laplacian_maze.mp4")