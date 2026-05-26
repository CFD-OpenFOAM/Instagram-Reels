import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import Button, Slider

# ============ GEOMETRY ============
R = 6.0
LANE_OFFSET = 0.75
APPROACH_LEN = 28.0
ROAD_HALF_W = 2.2

# Direction indices: 0=W (going east), 1=E (going west), 2=N (going south), 3=S (going north)
DIR_VEC = np.array([
    [1.0, 0.0],
    [-1.0, 0.0],
    [0.0, -1.0],
    [0.0, 1.0],
])
LANE_OFF_VEC = np.array([
    [0.0, -1.0],
    [0.0, 1.0],
    [-1.0, 0.0],
    [1.0, 0.0],
]) * LANE_OFFSET

SPAWN_PT = -DIR_VEC * APPROACH_LEN + LANE_OFF_VEC
DESPAWN_PT = DIR_VEC * APPROACH_LEN + LANE_OFF_VEC

# CCW arc entry angles per direction
ENTRY_ANGLE = np.array([np.pi, 0.0, np.pi / 2, -np.pi / 2])

# Intersection path: straight line from spawn through center to despawn
INT_PATH_LEN = 2 * APPROACH_LEN
INT_STOP_S = APPROACH_LEN - R  # stop bar at the intersection edge

# Roundabout path: straight to circle, 180° CCW arc, straight to despawn
L1 = APPROACH_LEN - R
L_ARC = np.pi * R
L3 = APPROACH_LEN - R
RB_PATH_LEN = L1 + L_ARC + L3

# ============ PHYSICS ============
ACCEL = 0.06
DECEL = 0.30
SAFE_FOLLOW = 3.6
MIN_GAP = 1.6
STOP_BUFFER = 2.0
SLOW_APPROACH = 11.0

MAX_CARS = 280

sim_params = {
    'v_max': 1.0,
    'inflow': 1.8,
    'signal_cycle': 180,
    'yield_gap': 6.0,
    'show_conflict': False,
    'paused': False,
    'stress_test': False,
}

# ============ SIM STATE ============
def make_sim():
    return {
        'dir': np.zeros(MAX_CARS, dtype=int),
        's': np.zeros(MAX_CARS),
        'v': np.zeros(MAX_CARS),
        'alive': np.zeros(MAX_CARS, dtype=bool),
        'energy_dest': 0.0,
        'through_count': 0,
        'through_window': 0,
    }

sim_int = make_sim()
sim_rb = make_sim()
sim_time = [0]

def reset_all():
    for sim in (sim_int, sim_rb):
        sim['alive'][:] = False
        sim['energy_dest'] = 0.0
        sim['through_count'] = 0
        sim['through_window'] = 0
    sim_time[0] = 0

# ============ PATH POSITIONS ============
def intersection_pos(d, s):
    return SPAWN_PT[d] + DIR_VEC[d] * s

def roundabout_pos(d, s):
    if s < L1:
        f = s / L1
        ep_x = R * np.cos(ENTRY_ANGLE[d])
        ep_y = R * np.sin(ENTRY_ANGLE[d])
        return np.array([SPAWN_PT[d, 0] * (1 - f) + ep_x * f,
                         SPAWN_PT[d, 1] * (1 - f) + ep_y * f])
    elif s < L1 + L_ARC:
        ds = s - L1
        theta = ENTRY_ANGLE[d] + ds / R
        return np.array([R * np.cos(theta), R * np.sin(theta)])
    else:
        ds = s - L1 - L_ARC
        f = min(1.0, ds / L3)
        ea = ENTRY_ANGLE[d] + np.pi
        ex_x = R * np.cos(ea)
        ex_y = R * np.sin(ea)
        return np.array([ex_x * (1 - f) + DESPAWN_PT[d, 0] * f,
                         ex_y * (1 - f) + DESPAWN_PT[d, 1] * f])

# ============ SPAWNING ============
def can_spawn(sim, d):
    for i in np.where(sim['alive'])[0]:
        if sim['dir'][i] == d and sim['s'][i] < 3.8:
            return False
    return True

def spawn_car(sim, d):
    if not can_spawn(sim, d):
        return
    for i in range(MAX_CARS):
        if not sim['alive'][i]:
            sim['dir'][i] = d
            sim['s'][i] = 0.0
            sim['v'][i] = sim_params['v_max'] * 0.92
            sim['alive'][i] = True
            return

def try_spawns():
    prob = sim_params['inflow'] / 30.0
    for d in range(4):
        if np.random.random() < prob:
            spawn_car(sim_int, d)
        if np.random.random() < prob:
            spawn_car(sim_rb, d)

# ============ INTERSECTION UPDATE ============
def update_intersection(sim, t):
    cycle = sim_params['signal_cycle']
    phase = t % cycle
    half = cycle // 2
    ns_green = phase < half

    alive_idx = np.where(sim['alive'])[0]
    by_dir = [[] for _ in range(4)]
    for i in alive_idx:
        by_dir[int(sim['dir'][i])].append(i)
    for d in range(4):
        by_dir[d].sort(key=lambda i: -sim['s'][i])
    pos_map = {}
    for d in range(4):
        for idx, i in enumerate(by_dir[d]):
            pos_map[i] = idx

    energy = 0.0
    v_max = sim_params['v_max']

    for i in alive_idx:
        d = int(sim['dir'][i])
        s = sim['s'][i]
        v = sim['v'][i]
        v_desired = v_max

        is_ns = d in (2, 3)
        on_red = (is_ns and not ns_green) or (not is_ns and ns_green)
        if on_red:
            dist = INT_STOP_S - s
            if dist > 0.3 and dist < SLOW_APPROACH:
                if dist < STOP_BUFFER:
                    v_desired = 0.0
                else:
                    f = (dist - STOP_BUFFER) / (SLOW_APPROACH - STOP_BUFFER)
                    v_desired = min(v_desired, v_max * f * f)

        my_pos = pos_map[i]
        if my_pos > 0:
            leader = by_dir[d][my_pos - 1]
            gap = sim['s'][leader] - s
            if 0 < gap < SAFE_FOLLOW:
                v_desired = min(v_desired, sim['v'][leader] * (gap / SAFE_FOLLOW))
            elif gap < SAFE_FOLLOW * 1.5:
                v_desired = min(v_desired, sim['v'][leader] + 0.05)

        v_old = v
        diff = v_desired - v
        v_new = v + (ACCEL if diff > 0 else DECEL) * diff
        v_new = max(0.0, min(v_new, v_max * 1.1))
        if v_new < v_old:
            energy += 0.5 * (v_old ** 2 - v_new ** 2)
        sim['v'][i] = v_new
        sim['s'][i] += v_new

        if sim['s'][i] > INT_PATH_LEN:
            sim['alive'][i] = False
            sim['through_count'] += 1
            sim['through_window'] += 1

    for d in range(4):
        q = by_dir[d]
        for k in range(1, len(q)):
            ld, fl = q[k - 1], q[k]
            if not (sim['alive'][ld] and sim['alive'][fl]):
                continue
            gap = sim['s'][ld] - sim['s'][fl]
            if gap < MIN_GAP:
                sim['s'][fl] = sim['s'][ld] - MIN_GAP
                sim['v'][fl] = min(sim['v'][fl], sim['v'][ld])

    sim['energy_dest'] += energy

# ============ ROUNDABOUT UPDATE ============
def update_roundabout(sim, t):
    yield_gap = sim_params['yield_gap']
    alive_idx = np.where(sim['alive'])[0]

    arc_cars = []
    for i in alive_idx:
        s = sim['s'][i]
        if L1 <= s < L1 + L_ARC:
            d = int(sim['dir'][i])
            theta = (ENTRY_ANGLE[d] + (s - L1) / R) % (2 * np.pi)
            arc_cars.append((theta, i, sim['v'][i]))

    by_dir = [[] for _ in range(4)]
    for i in alive_idx:
        by_dir[int(sim['dir'][i])].append(i)
    for d in range(4):
        by_dir[d].sort(key=lambda i: -sim['s'][i])
    pos_map = {}
    for d in range(4):
        for idx, i in enumerate(by_dir[d]):
            pos_map[i] = idx

    energy = 0.0
    v_max = sim_params['v_max']

    for i in alive_idx:
        d = int(sim['dir'][i])
        s = sim['s'][i]
        v = sim['v'][i]
        v_desired = v_max

        if s < L1:
            entry_a = ENTRY_ANGLE[d] % (2 * np.pi)
            dist_to_entry = L1 - s
            min_conflict = float('inf')
            for theta_a, _, _ in arc_cars:
                delta = (entry_a - theta_a) % (2 * np.pi)
                arc_dist = delta * R
                if 0.1 < arc_dist < yield_gap and arc_dist < min_conflict:
                    min_conflict = arc_dist
            if min_conflict < float('inf') and dist_to_entry < SLOW_APPROACH:
                if dist_to_entry < STOP_BUFFER:
                    v_desired = 0.0
                else:
                    f = (dist_to_entry - STOP_BUFFER) / (SLOW_APPROACH - STOP_BUFFER)
                    cf = min_conflict / yield_gap
                    v_desired = min(v_desired, v_max * (0.3 + 0.6 * cf) * f)

        my_pos = pos_map[i]
        if my_pos > 0:
            leader = by_dir[d][my_pos - 1]
            gap = sim['s'][leader] - s
            if 0 < gap < SAFE_FOLLOW:
                v_desired = min(v_desired, sim['v'][leader] * (gap / SAFE_FOLLOW))
            elif gap < SAFE_FOLLOW * 1.5:
                v_desired = min(v_desired, sim['v'][leader] + 0.05)

        if L1 <= s < L1 + L_ARC:
            my_theta = (ENTRY_ANGLE[d] + (s - L1) / R) % (2 * np.pi)
            best_gap = float('inf')
            best_v = None
            for theta_a, i_a, v_a in arc_cars:
                if i_a == i:
                    continue
                delta = (theta_a - my_theta) % (2 * np.pi)
                if 0.05 < delta < np.pi:
                    ad = delta * R
                    if ad < best_gap:
                        best_gap = ad
                        best_v = v_a
            if best_v is not None and best_gap < SAFE_FOLLOW:
                v_desired = min(v_desired, best_v * (best_gap / SAFE_FOLLOW))

        v_old = v
        diff = v_desired - v
        v_new = v + (ACCEL if diff > 0 else DECEL) * diff
        v_new = max(0.0, min(v_new, v_max * 1.1))
        if v_new < v_old:
            energy += 0.5 * (v_old ** 2 - v_new ** 2)
        sim['v'][i] = v_new
        sim['s'][i] += v_new

        if sim['s'][i] > RB_PATH_LEN:
            sim['alive'][i] = False
            sim['through_count'] += 1
            sim['through_window'] += 1

    sim['energy_dest'] += energy

# ============ STATS ============
through_history_int = []
through_history_rb = []

def tick_stats():
    if sim_time[0] % 30 == 0 and sim_time[0] > 0:
        through_history_int.append(sim_int['through_window'])
        through_history_rb.append(sim_rb['through_window'])
        sim_int['through_window'] = 0
        sim_rb['through_window'] = 0
        if len(through_history_int) > 30:
            through_history_int.pop(0)
            through_history_rb.pop(0)

def stopped_count(sim):
    idx = np.where(sim['alive'])[0]
    if len(idx) == 0:
        return 0
    return int(np.sum(sim['v'][idx] < 0.08))

def avg_speed(sim):
    idx = np.where(sim['alive'])[0]
    if len(idx) == 0:
        return 0.0
    return float(np.mean(sim['v'][idx]))

# ============ FIGURE ============
print("Intersection vs Roundabout — Traffic Flow Geometry")
print("Same inflow, two different control regimes. Watch energy destruction & stops.")

fig = plt.figure(figsize=(15, 9))
fig.patch.set_facecolor('#0a0a0a')

ax_int = fig.add_axes([0.02, 0.30, 0.46, 0.66])
ax_rb = fig.add_axes([0.52, 0.30, 0.46, 0.66])

cmap = LinearSegmentedColormap.from_list('traffic', ['#FF0044', '#FFAA00', '#00FFCC'], N=256)

LIM = APPROACH_LEN + 3

def draw_static(ax, is_rb):
    ax.set_facecolor('#0a0a0a')
    ax.set_xlim(-LIM, LIM)
    ax.set_ylim(-LIM, LIM)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])

    rh = ROAD_HALF_W
    ax.add_patch(patches.Rectangle((-LIM, -rh), 2 * LIM, 2 * rh,
                                   facecolor='#1a1a24', zorder=1))
    ax.add_patch(patches.Rectangle((-rh, -LIM), 2 * rh, 2 * LIM,
                                   facecolor='#1a1a24', zorder=1))

    # center dividers (yellow dash)
    for x in np.arange(-LIM, LIM, 2.0):
        if abs(x) > R + 0.2:
            ax.plot([x, x + 1.0], [0, 0], color='#665522', lw=0.7, alpha=0.6, zorder=2)
            ax.plot([0, 0], [x, x + 1.0], color='#665522', lw=0.7, alpha=0.6, zorder=2)

    if is_rb:
        island = plt.Circle((0, 0), R - 1.2, facecolor='#152015',
                            edgecolor='#446644', lw=2, zorder=4)
        ax.add_patch(island)
        path_ring = plt.Circle((0, 0), R, facecolor='none',
                               edgecolor='#33443a', lw=0.8, ls=':', zorder=3)
        ax.add_patch(path_ring)
    else:
        # cover the intersection box so road shows as a box
        ax.add_patch(patches.Rectangle((-R, -R), 2 * R, 2 * R,
                                       facecolor='#1a1a24', zorder=1.5))

draw_static(ax_int, False)
draw_static(ax_rb, True)

# Traffic signals on intersection
SIGNAL_OFFSETS = np.array([
    [-R - 0.3, -ROAD_HALF_W - 1.0],
    [R + 0.3, ROAD_HALF_W + 1.0],
    [-ROAD_HALF_W - 1.0, R + 0.3],
    [ROAD_HALF_W + 1.0, -R - 0.3],
])
int_signals = []
for d in range(4):
    c = plt.Circle(SIGNAL_OFFSETS[d], 0.55, facecolor='#00CC44',
                   edgecolor='#444', lw=1.2, zorder=10)
    ax_int.add_patch(c)
    int_signals.append(c)
    ax_int.plot([SIGNAL_OFFSETS[d, 0]], [SIGNAL_OFFSETS[d, 1]], zorder=9)

# Yield triangles on roundabout
yield_marks = []
for d in range(4):
    ep = -DIR_VEC[d] * (R + 1.4) + LANE_OFF_VEC[d]
    t = patches.RegularPolygon(ep, 3, radius=0.55,
                               orientation=np.arctan2(DIR_VEC[d, 1], DIR_VEC[d, 0]) - np.pi / 2,
                               facecolor='#221100', edgecolor='#FFAA22', lw=1.2, zorder=10)
    ax_rb.add_patch(t)
    yield_marks.append(t)

# Car scatters
scat_int = ax_int.scatter([], [], s=42, c=[], cmap=cmap, vmin=0, vmax=1,
                          zorder=6, edgecolors='none')
scat_rb = ax_rb.scatter([], [], s=42, c=[], cmap=cmap, vmin=0, vmax=1,
                        zorder=6, edgecolors='none')

# Conflict point overlays
def make_intersection_conflict_pts():
    pts = []
    # 16 crossings: 4x4 grid in the center
    grid_xy = [-2.4, -0.9, 0.9, 2.4]
    for gx in grid_xy:
        for gy in grid_xy:
            pts.append((gx, gy))
    # 8 merges (where cars join from approach lanes into intersection)
    merge_offsets = [
        (-R + 0.5, -LANE_OFFSET), (-R + 0.5, LANE_OFFSET),
        (R - 0.5, -LANE_OFFSET), (R - 0.5, LANE_OFFSET),
        (-LANE_OFFSET, R - 0.5), (LANE_OFFSET, R - 0.5),
        (-LANE_OFFSET, -R + 0.5), (LANE_OFFSET, -R + 0.5),
    ]
    pts.extend(merge_offsets)
    # 8 diverges (exits)
    div_offsets = [
        (R - 0.5, -LANE_OFFSET - 0.6), (R - 0.5, LANE_OFFSET + 0.6),
        (-R + 0.5, -LANE_OFFSET - 0.6), (-R + 0.5, LANE_OFFSET + 0.6),
        (-LANE_OFFSET - 0.6, -R + 0.5), (LANE_OFFSET + 0.6, -R + 0.5),
        (-LANE_OFFSET - 0.6, R - 0.5), (LANE_OFFSET + 0.6, R - 0.5),
    ]
    pts.extend(div_offsets)
    return np.array(pts)

def make_roundabout_conflict_pts():
    pts = []
    for a in [0.0, np.pi / 2, np.pi, -np.pi / 2]:
        for off in [-0.18, 0.18]:
            ang = a + off
            pts.append((R * np.cos(ang), R * np.sin(ang)))
    return np.array(pts)

INT_CONFLICT = make_intersection_conflict_pts()
RB_CONFLICT = make_roundabout_conflict_pts()

conflict_int = ax_int.scatter(INT_CONFLICT[:, 0], INT_CONFLICT[:, 1],
                              s=55, facecolors='none', edgecolors='#FFFFFF',
                              lw=1.2, zorder=11, alpha=0.0)
conflict_rb = ax_rb.scatter(RB_CONFLICT[:, 0], RB_CONFLICT[:, 1],
                            s=70, facecolors='none', edgecolors='#FFFFFF',
                            lw=1.4, zorder=11, alpha=0.0)
conflict_int_label = ax_int.text(0, -LIM + 1.5, '', color='#FFFFFF',
                                 fontsize=10, ha='center', fontweight='bold',
                                 fontfamily='monospace', zorder=12, alpha=0.0)
conflict_rb_label = ax_rb.text(0, -LIM + 1.5, '', color='#FFFFFF',
                               fontsize=10, ha='center', fontweight='bold',
                               fontfamily='monospace', zorder=12, alpha=0.0)

# Titles
ax_int.set_title('INTERSECTION  —  Signalized 4-Way',
                 color='#FF6644', fontsize=13, fontweight='bold', pad=6,
                 fontfamily='monospace')
ax_rb.set_title('ROUNDABOUT  —  Yield-Controlled',
                color='#00FFCC', fontsize=13, fontweight='bold', pad=6,
                fontfamily='monospace')

# Stat overlays
stat_int = ax_int.text(-LIM + 1, LIM - 1.5, '', color='#cccccc',
                       fontsize=9, va='top', fontfamily='monospace', zorder=12)
stat_rb = ax_rb.text(-LIM + 1, LIM - 1.5, '', color='#cccccc',
                     fontsize=9, va='top', fontfamily='monospace', zorder=12)

# Comparison banner
banner = fig.text(0.5, 0.965, '', color='#FFCC66', fontsize=11,
                  ha='center', fontfamily='monospace', fontweight='bold')

# ============ CONTROLS ============
ax_inflow = fig.add_axes([0.10, 0.22, 0.55, 0.024])
ax_inflow.set_facecolor('#1a1a2a')
sl_inflow = Slider(ax_inflow, 'Inflow (cars/s/dir)', 0.3, 5.0,
                   valinit=sim_params['inflow'], valstep=0.1, color='#CC8800')
sl_inflow.label.set_color('white')
sl_inflow.valtext.set_color('white')

ax_cycle = fig.add_axes([0.10, 0.18, 0.55, 0.024])
ax_cycle.set_facecolor('#1a1a2a')
sl_cycle = Slider(ax_cycle, 'Signal Cycle', 80, 360,
                  valinit=sim_params['signal_cycle'], valstep=10, color='#CCAA00')
sl_cycle.label.set_color('white')
sl_cycle.valtext.set_color('white')

ax_yield = fig.add_axes([0.10, 0.14, 0.55, 0.024])
ax_yield.set_facecolor('#1a1a2a')
sl_yield = Slider(ax_yield, 'Roundabout Yield Gap', 2.0, 14.0,
                  valinit=sim_params['yield_gap'], valstep=0.5, color='#00AACC')
sl_yield.label.set_color('white')
sl_yield.valtext.set_color('white')

ax_speed = fig.add_axes([0.10, 0.10, 0.55, 0.024])
ax_speed.set_facecolor('#1a1a2a')
sl_speed = Slider(ax_speed, 'Max Speed', 0.4, 1.6,
                  valinit=sim_params['v_max'], valstep=0.05, color='#AA44CC')
sl_speed.label.set_color('white')
sl_speed.valtext.set_color('white')

def on_inflow(v): sim_params['inflow'] = v
def on_cycle(v): sim_params['signal_cycle'] = int(v)
def on_yield(v): sim_params['yield_gap'] = v
def on_speed(v): sim_params['v_max'] = v
sl_inflow.on_changed(on_inflow)
sl_cycle.on_changed(on_cycle)
sl_yield.on_changed(on_yield)
sl_speed.on_changed(on_speed)

# Buttons
ax_btn_conflict = fig.add_axes([0.72, 0.21, 0.24, 0.04])
btn_conflict = Button(ax_btn_conflict, 'Show Conflict Points',
                      color='#222233', hovercolor='#333355')
btn_conflict.label.set_color('white')
btn_conflict.label.set_fontfamily('monospace')

def toggle_conflict(_):
    sim_params['show_conflict'] = not sim_params['show_conflict']
    if sim_params['show_conflict']:
        btn_conflict.label.set_text('Hide Conflict Points')
    else:
        btn_conflict.label.set_text('Show Conflict Points')
btn_conflict.on_clicked(toggle_conflict)

ax_btn_stress = fig.add_axes([0.72, 0.16, 0.24, 0.04])
btn_stress = Button(ax_btn_stress, 'Stress Test (ramp inflow)',
                    color='#331111', hovercolor='#552222')
btn_stress.label.set_color('#FFAA88')
btn_stress.label.set_fontfamily('monospace')

def toggle_stress(_):
    sim_params['stress_test'] = not sim_params['stress_test']
    if sim_params['stress_test']:
        btn_stress.label.set_text('Stop Stress Test')
        btn_stress.label.set_color('#FF4444')
    else:
        btn_stress.label.set_text('Stress Test (ramp inflow)')
        btn_stress.label.set_color('#FFAA88')
btn_stress.on_clicked(toggle_stress)

ax_btn_pause = fig.add_axes([0.72, 0.11, 0.115, 0.04])
btn_pause = Button(ax_btn_pause, 'Pause', color='#222233', hovercolor='#333355')
btn_pause.label.set_color('white')
btn_pause.label.set_fontfamily('monospace')

def toggle_pause(_):
    sim_params['paused'] = not sim_params['paused']
    btn_pause.label.set_text('Resume' if sim_params['paused'] else 'Pause')
btn_pause.on_clicked(toggle_pause)

ax_btn_reset = fig.add_axes([0.845, 0.11, 0.115, 0.04])
btn_reset = Button(ax_btn_reset, 'Reset', color='#222233', hovercolor='#333355')
btn_reset.label.set_color('white')
btn_reset.label.set_fontfamily('monospace')

def do_reset(_):
    reset_all()
    through_history_int.clear()
    through_history_rb.clear()
btn_reset.on_clicked(do_reset)

# ============ ANIMATION ============
def render_cars(sim, scat, pos_fn):
    alive = np.where(sim['alive'])[0]
    if len(alive) == 0:
        scat.set_offsets(np.empty((0, 2)))
        scat.set_array(np.array([]))
        return
    pts = np.zeros((len(alive), 2))
    for k, i in enumerate(alive):
        pts[k] = pos_fn(int(sim['dir'][i]), sim['s'][i])
    colors = np.clip(sim['v'][alive] / sim_params['v_max'], 0, 1)
    scat.set_offsets(pts)
    scat.set_array(colors)

def animate(frame):
    if sim_params['paused']:
        return scat_int, scat_rb

    if sim_params['stress_test']:
        sim_params['inflow'] = min(5.0, sim_params['inflow'] + 0.003)
        sl_inflow.eventson = False
        sl_inflow.set_val(sim_params['inflow'])
        sl_inflow.eventson = True

    sim_time[0] += 1
    t = sim_time[0]

    try_spawns()
    update_intersection(sim_int, t)
    update_roundabout(sim_rb, t)
    tick_stats()

    render_cars(sim_int, scat_int, intersection_pos)
    render_cars(sim_rb, scat_rb, roundabout_pos)

    # Signals
    cycle = sim_params['signal_cycle']
    phase = t % cycle
    ns_green = phase < cycle // 2
    for d in range(4):
        is_ns = d in (2, 3)
        green = (is_ns and ns_green) or (not is_ns and not ns_green)
        if green:
            int_signals[d].set_facecolor('#00CC44')
            int_signals[d].set_edgecolor('#00FF55')
        else:
            int_signals[d].set_facecolor('#FF0044')
            int_signals[d].set_edgecolor('#FF2255')

    # Conflict overlay
    a = 0.85 if sim_params['show_conflict'] else 0.0
    conflict_int.set_alpha(a)
    conflict_rb.set_alpha(a)
    if sim_params['show_conflict']:
        conflict_int_label.set_text('32 conflict points')
        conflict_rb_label.set_text('8 conflict points')
        conflict_int_label.set_alpha(1.0)
        conflict_rb_label.set_alpha(1.0)
    else:
        conflict_int_label.set_alpha(0.0)
        conflict_rb_label.set_alpha(0.0)

    # Stats text
    flow_int = sum(through_history_int[-6:]) if through_history_int else 0
    flow_rb = sum(through_history_rb[-6:]) if through_history_rb else 0
    si = stopped_count(sim_int)
    sr = stopped_count(sim_rb)
    asi = avg_speed(sim_int)
    asr = avg_speed(sim_rb)

    stat_int.set_text(
        f"Throughput:  {flow_int:>4} cars / 6s\n"
        f"Stopped:     {si:>4}\n"
        f"Avg speed:   {asi:>4.2f}\n"
        f"KE destroyed:{sim_int['energy_dest']:>7.1f}"
    )
    stat_rb.set_text(
        f"Throughput:  {flow_rb:>4} cars / 6s\n"
        f"Stopped:     {sr:>4}\n"
        f"Avg speed:   {asr:>4.2f}\n"
        f"KE destroyed:{sim_rb['energy_dest']:>7.1f}"
    )

    total_e = sim_int['energy_dest'] + sim_rb['energy_dest']
    if total_e > 5:
        saved = 100.0 * (sim_int['energy_dest'] - sim_rb['energy_dest']) / max(sim_int['energy_dest'], 1e-6)
        if saved > 0:
            banner.set_text(f"Roundabout saves {saved:.0f}% of kinetic energy vs Intersection  "
                            f"|  stopped: {si} vs {sr}  |  inflow: {sim_params['inflow']:.1f}/s/dir")
        else:
            banner.set_text(f"Intersection currently ahead  |  inflow: {sim_params['inflow']:.1f}/s/dir")
    else:
        banner.set_text(f"Inflow: {sim_params['inflow']:.1f} cars/s per direction  —  warming up...")

    return (scat_int, scat_rb, stat_int, stat_rb, banner,
            conflict_int, conflict_rb, conflict_int_label, conflict_rb_label,
            *int_signals)

ani = animation.FuncAnimation(fig, animate, interval=33, blit=False, cache_frame_data=False)
plt.show()
