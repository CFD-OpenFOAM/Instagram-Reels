import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import Button, Slider

# --- CONSTANTS ---
N_CARS = 150
Y_MIN, Y_MAX = -5, 102
TOLL_Y = 50
ENTRANCE_LANES = 3
TOLL_LANES = 6

V_MAX = 1.8
V_TOLL = 0.4
V_EXIT = V_MAX * 1.4
SAFE_DIST = 3.5
MIN_GAP = 1.5
ACCEL = 0.12
DECEL = 0.4
DIVERT_THRESHOLD = 12

LANE_MAP = {0: [0, 1], 1: [2, 3], 2: [4, 5]}
EXIT_MAP = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 2}

# --- MUTABLE SIM PARAMETERS (controlled by sliders) ---
sim_params = {'v_max': V_MAX, 'n_active': N_CARS}

# --- GEOMETRY ---

def smoothstep(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)

def get_plaza_width(y):
    if y < 20:
        return 4.0
    elif y < 40:
        return 4.0 + 8.0 * smoothstep((y - 20) / 20)
    elif y < 60:
        return 12.0
    elif y < 80:
        return 12.0 - 8.0 * smoothstep((y - 60) / 20)
    else:
        return 4.0

def entrance_lane_x(lane, n=ENTRANCE_LANES):
    spacing = 3.2 / (n - 1) if n > 1 else 0
    return -1.6 + lane * spacing

def toll_lane_x(lane, n=TOLL_LANES):
    spacing = 10.0 / (n - 1) if n > 1 else 0
    return -5.0 + lane * spacing

def get_lane_x(lane, y, is_toll_lane=True):
    if is_toll_lane:
        target_x = toll_lane_x(lane)
        src_lane = EXIT_MAP[lane]
        src_x = entrance_lane_x(src_lane)
    else:
        target_x = entrance_lane_x(lane)
        src_x = target_x

    if y < 20:
        return src_x
    elif y < 40:
        t = smoothstep((y - 20) / 20)
        return src_x + (target_x - src_x) * t
    elif y < 60:
        return target_x
    elif y < 80:
        exit_x = entrance_lane_x(EXIT_MAP[lane]) if is_toll_lane else target_x
        t = smoothstep((y - 60) / 20)
        return target_x + (exit_x - target_x) * t
    else:
        exit_x = entrance_lane_x(EXIT_MAP[lane]) if is_toll_lane else target_x
        return exit_x

# --- SIMULATION STATE ---
gate_active = [True] * TOLL_LANES
throughput_count = [0]
throughput_display = [0.0]
frame_counter = [0]

MAX_CARS = 250
car_y = np.zeros(MAX_CARS)
car_vy = np.zeros(MAX_CARS)
car_lane = np.zeros(MAX_CARS, dtype=int)
car_toll_lane = np.full(MAX_CARS, -1, dtype=int)
car_x = np.zeros(MAX_CARS)
car_wait = np.zeros(MAX_CARS, dtype=int)
car_has_toll_lane = np.zeros(MAX_CARS, dtype=bool)
car_passed_toll = np.zeros(MAX_CARS, dtype=bool)
car_merge_target = np.full(MAX_CARS, -1, dtype=int)
car_merge_progress = np.zeros(MAX_CARS)
car_alive = np.zeros(MAX_CARS, dtype=bool)

def spawn_car(i, stagger=True):
    car_lane[i] = np.random.randint(0, ENTRANCE_LANES)
    car_y[i] = np.random.uniform(-8, -1) if stagger else np.random.uniform(-5, -1)
    car_vy[i] = np.random.uniform(sim_params['v_max'] * 0.7, sim_params['v_max'])
    car_x[i] = entrance_lane_x(car_lane[i])
    car_toll_lane[i] = -1
    car_has_toll_lane[i] = False
    car_passed_toll[i] = False
    car_wait[i] = 0
    car_merge_target[i] = -1
    car_merge_progress[i] = 0
    car_alive[i] = True

for i in range(N_CARS):
    spawn_car(i)
    car_y[i] = np.random.uniform(-5, 85)
    if car_y[i] > 18:
        tl = np.random.choice(LANE_MAP[car_lane[i]])
        car_toll_lane[i] = tl
        car_has_toll_lane[i] = True
        car_x[i] = get_lane_x(tl, car_y[i], is_toll_lane=True)
        if car_y[i] > TOLL_Y + 2:
            car_passed_toll[i] = True

def pick_toll_lane(car_idx):
    ent = car_lane[car_idx]
    options = LANE_MAP[ent]
    counts = []
    for tl in options:
        if not gate_active[tl]:
            counts.append(999)
        else:
            n_ahead = sum(1 for j in range(MAX_CARS)
                          if car_alive[j] and car_toll_lane[j] == tl and car_y[j] > car_y[car_idx])
            counts.append(n_ahead)
    return options[np.argmin(counts)]

def find_merge_lane(toll_lane_idx):
    for offset in [1, -1, 2, -2]:
        candidate = toll_lane_idx + offset
        if 0 <= candidate < TOLL_LANES and gate_active[candidate]:
            return candidate
    return -1

def check_merge_gap(car_idx, target_lane):
    my_y = car_y[car_idx]
    for j in range(MAX_CARS):
        if j == car_idx or not car_alive[j]:
            continue
        if car_toll_lane[j] == target_lane and abs(car_y[j] - my_y) < SAFE_DIST * 0.7:
            return False
    return True

# --- PHYSICS ---

def update_physics():
    frame_counter[0] += 1
    v_max = sim_params['v_max']
    v_exit = v_max * 1.4
    n_target = int(sim_params['n_active'])

    if frame_counter[0] % 30 == 0:
        throughput_display[0] = throughput_count[0]
        throughput_count[0] = 0

    n_alive = int(np.sum(car_alive))
    if n_alive < n_target:
        for i in range(MAX_CARS):
            if not car_alive[i]:
                spawn_car(i, stagger=False)
                n_alive += 1
                if n_alive >= n_target:
                    break
    elif n_alive > n_target:
        kill = n_alive - n_target
        for i in range(MAX_CARS):
            if car_alive[i] and kill > 0:
                car_alive[i] = False
                kill -= 1

    alive_idx = np.where(car_alive)[0]

    lane_cars = {}
    for tl in range(TOLL_LANES):
        indices = [i for i in alive_idx if car_toll_lane[i] == tl]
        indices.sort(key=lambda i: -car_y[i])
        lane_cars[tl] = indices

    ent_cars = {}
    for el in range(ENTRANCE_LANES):
        indices = [i for i in alive_idx if not car_has_toll_lane[i] and car_lane[i] == el]
        indices.sort(key=lambda i: -car_y[i])
        ent_cars[el] = indices

    exit_cars = {}
    for el in range(ENTRANCE_LANES):
        indices = [i for i in alive_idx if car_passed_toll[i] and EXIT_MAP.get(car_toll_lane[i], -1) == el]
        indices.sort(key=lambda i: -car_y[i])
        exit_cars[el] = indices

    for i in alive_idx:
        y = car_y[i]

        if not car_has_toll_lane[i] and y >= 16:
            tl = pick_toll_lane(i)
            car_toll_lane[i] = tl
            car_has_toll_lane[i] = True

        if car_has_toll_lane[i] and not car_passed_toll[i]:
            if y > TOLL_Y + 3:
                car_passed_toll[i] = True
                car_wait[i] = 0
                car_merge_target[i] = -1
                car_merge_progress[i] = 0

        v_desired = v_max

        if y < 20:
            v_desired = v_max
        elif y < 40:
            v_desired = v_max * 0.85
        elif y < 60:
            if car_has_toll_lane[i]:
                tl = car_toll_lane[i]
                if gate_active[tl]:
                    dist_to_toll = TOLL_Y - y
                    if dist_to_toll > 0 and dist_to_toll < 12:
                        v_desired = V_TOLL + (v_max - V_TOLL) * (dist_to_toll / 12)
                    elif dist_to_toll <= 0:
                        v_desired = V_TOLL * 1.5
                else:
                    dist_to_toll = TOLL_Y - y
                    if dist_to_toll > 2:
                        v_desired = max(0.0, v_max * 0.3 * (dist_to_toll / 15))
                    elif dist_to_toll > -1:
                        v_desired = 0.0
                        car_wait[i] += 1
                        queue = lane_cars.get(tl, [])
                        stopped_count = sum(1 for qi in queue if car_vy[qi] < 0.1 and car_y[qi] < TOLL_Y)
                        my_rank = 0
                        for qi in queue:
                            if car_y[qi] > car_y[i] and car_y[qi] < TOLL_Y:
                                my_rank += 1
                        if stopped_count >= DIVERT_THRESHOLD and my_rank >= DIVERT_THRESHOLD - 2 and car_merge_target[i] == -1:
                            mt = find_merge_lane(tl)
                            if mt >= 0 and check_merge_gap(i, mt):
                                car_merge_target[i] = mt
                                car_merge_progress[i] = 0
                    else:
                        v_desired = V_TOLL * 0.5
            else:
                v_desired = V_TOLL
        elif y < 80:
            v_desired = v_max * 0.75
        else:
            v_desired = v_exit

        if car_merge_target[i] >= 0:
            car_merge_progress[i] += 0.05
            if car_merge_progress[i] >= 1.0:
                car_toll_lane[i] = car_merge_target[i]
                car_merge_target[i] = -1
                car_merge_progress[i] = 0
                car_wait[i] = 0
            v_desired = max(v_desired, 0.15)

        def find_leader(queue, idx):
            my_pos = None
            for qi, qidx in enumerate(queue):
                if qidx == idx:
                    my_pos = qi
                    break
            if my_pos is not None and my_pos > 0:
                leader = queue[my_pos - 1]
                gap = car_y[leader] - car_y[idx]
                if 0 < gap < SAFE_DIST * 2:
                    if gap < SAFE_DIST:
                        return car_vy[leader] * (gap / SAFE_DIST)
                    elif gap < SAFE_DIST * 1.5:
                        return car_vy[leader] + 0.2
            return None

        if car_has_toll_lane[i] and not car_passed_toll[i]:
            tl = car_toll_lane[i]
            if tl in lane_cars:
                lv = find_leader(lane_cars[tl], i)
                if lv is not None:
                    v_desired = min(v_desired, lv)
        elif not car_has_toll_lane[i]:
            el = car_lane[i]
            if el in ent_cars:
                lv = find_leader(ent_cars[el], i)
                if lv is not None:
                    v_desired = min(v_desired, lv)
        elif car_passed_toll[i]:
            el = EXIT_MAP.get(car_toll_lane[i], 0)
            if el in exit_cars:
                lv = find_leader(exit_cars[el], i)
                if lv is not None:
                    v_desired = min(v_desired, lv)

        v_desired = max(0.0, v_desired)
        diff = v_desired - car_vy[i]
        if diff > 0:
            car_vy[i] += ACCEL * diff
        else:
            car_vy[i] += DECEL * diff

        car_vy[i] = np.clip(car_vy[i], 0.0, v_exit * 1.1)
        car_y[i] += car_vy[i]

        if car_y[i] > Y_MAX:
            throughput_count[0] += 1
            spawn_car(i, stagger=False)

    for tl in range(TOLL_LANES):
        queue = [i for i in alive_idx if car_alive[i] and car_toll_lane[i] == tl]
        queue.sort(key=lambda i: -car_y[i])
        for qi in range(1, len(queue)):
            leader = queue[qi - 1]
            follower = queue[qi]
            gap = car_y[leader] - car_y[follower]
            if gap < MIN_GAP:
                car_y[follower] = car_y[leader] - MIN_GAP
                car_vy[follower] = min(car_vy[follower], car_vy[leader])

    for el in range(ENTRANCE_LANES):
        queue = [i for i in alive_idx if car_alive[i] and not car_has_toll_lane[i] and car_lane[i] == el]
        queue.sort(key=lambda i: -car_y[i])
        for qi in range(1, len(queue)):
            leader = queue[qi - 1]
            follower = queue[qi]
            gap = car_y[leader] - car_y[follower]
            if gap < MIN_GAP:
                car_y[follower] = car_y[leader] - MIN_GAP
                car_vy[follower] = min(car_vy[follower], car_vy[leader])

    for el in range(ENTRANCE_LANES):
        queue = [i for i in alive_idx if car_alive[i] and car_passed_toll[i] and EXIT_MAP.get(car_toll_lane[i], -1) == el]
        queue.sort(key=lambda i: -car_y[i])
        for qi in range(1, len(queue)):
            leader = queue[qi - 1]
            follower = queue[qi]
            gap = car_y[leader] - car_y[follower]
            if gap < MIN_GAP:
                car_y[follower] = car_y[leader] - MIN_GAP
                car_vy[follower] = min(car_vy[follower], car_vy[leader])

    for i in alive_idx:
        if car_merge_target[i] >= 0:
            t = smoothstep(car_merge_progress[i])
            src_x = get_lane_x(car_toll_lane[i], car_y[i], is_toll_lane=True)
            dst_x = get_lane_x(car_merge_target[i], car_y[i], is_toll_lane=True)
            car_x[i] = src_x + (dst_x - src_x) * t
        elif car_has_toll_lane[i]:
            car_x[i] = get_lane_x(car_toll_lane[i], car_y[i], is_toll_lane=True)
        else:
            car_x[i] = entrance_lane_x(car_lane[i])
        max_bound = (get_plaza_width(car_y[i]) / 2.0) - 0.2
        car_x[i] = np.clip(car_x[i], -max_bound, max_bound)

# --- RENDERING ---
print("Interactive Toll Plaza Simulator")
print("Use gate buttons to toggle failures. Use sliders to adjust speed & density.")

fig = plt.figure(figsize=(6, 10))
fig.patch.set_facecolor('#0a0a0a')

ax = fig.add_axes([0.05, 0.22, 0.9, 0.74])
ax.set_facecolor('#0a0a0a')
ax.set_xlim(-7, 7)
ax.set_ylim(-5, 105)
ax.set_xticks([])
ax.set_yticks([])

y_wall = np.linspace(0, 100, 300)
x_wall_r = np.array([get_plaza_width(y) / 2 for y in y_wall])
ax.plot(x_wall_r, y_wall, color='#555566', lw=3, solid_capstyle='round')
ax.plot(-x_wall_r, y_wall, color='#555566', lw=3, solid_capstyle='round')

for tl in range(TOLL_LANES):
    lane_y = np.linspace(22, 78, 100)
    lane_x_pts = [get_lane_x(tl, y, is_toll_lane=True) for y in lane_y]
    ax.plot(lane_x_pts, lane_y, color='#222233', lw=0.8, linestyle=':', alpha=0.6)

gate_rects = []
for tl in range(TOLL_LANES):
    gx = toll_lane_x(tl)
    rect = patches.FancyBboxPatch(
        (gx - 0.7, TOLL_Y - 1.5), 1.4, 3.0,
        boxstyle="round,pad=0.2",
        facecolor='#00CC44', edgecolor='#00FF55',
        alpha=0.8, linewidth=1.5, zorder=8
    )
    ax.add_patch(rect)
    gate_rects.append(rect)
    ax.text(gx, TOLL_Y + 2.8, f"G{tl+1}", color='#aaaaaa',
            fontsize=7, ha='center', va='bottom', zorder=9)

cmap = LinearSegmentedColormap.from_list('traffic', ['#FF0044', '#FFAA00', '#00FFCC'], N=256)
scat = ax.scatter([], [], s=35, c=[], cmap=cmap, vmin=0, vmax=1, zorder=5, edgecolors='none')

status_text = ax.text(-6.5, 103, '', color='#888899', fontsize=7,
                      fontfamily='monospace', va='top', zorder=10)
info_text = ax.text(0, -3, 'Use buttons below to toggle gate failures', color='#555566',
                    fontsize=7, ha='center', va='top', zorder=10)
throughput_text = ax.text(6.5, 103, '', color='#888899', fontsize=7,
                         fontfamily='monospace', va='top', ha='right', zorder=10)

# --- WIDGET: GATE BUTTONS ---
gate_buttons = []
gate_button_axes = []

for tl in range(TOLL_LANES):
    bx = 0.08 + tl * 0.145
    btn_ax = fig.add_axes([bx, 0.13, 0.12, 0.045])
    btn_ax.set_facecolor('#0a0a0a')
    btn = Button(btn_ax, f'Gate {tl+1}: ON',
                 color='#114411', hovercolor='#226622')
    btn_ax.set_navigate(False)

    def make_toggle(idx):
        def toggle(event):
            gate_active[idx] = not gate_active[idx]
            if gate_active[idx]:
                gate_rects[idx].set_facecolor('#00CC44')
                gate_rects[idx].set_edgecolor('#00FF55')
                gate_buttons[idx].label.set_text(f'Gate {idx+1}: ON')
                gate_buttons[idx].ax.set_facecolor('#114411')
                gate_buttons[idx].color = '#114411'
                gate_buttons[idx].hovercolor = '#226622'
                for k in range(MAX_CARS):
                    if car_alive[k] and car_toll_lane[k] == idx and car_wait[k] > 0:
                        car_wait[k] = 0
                        car_merge_target[k] = -1
                        car_merge_progress[k] = 0
            else:
                gate_rects[idx].set_facecolor('#FF0044')
                gate_rects[idx].set_edgecolor('#FF2255')
                gate_buttons[idx].label.set_text(f'Gate {idx+1}: OFF')
                gate_buttons[idx].ax.set_facecolor('#441111')
                gate_buttons[idx].color = '#441111'
                gate_buttons[idx].hovercolor = '#662222'
            fig.canvas.draw_idle()
        return toggle

    btn.on_clicked(make_toggle(tl))
    btn.label.set_color('white')
    btn.label.set_fontsize(8)
    gate_buttons.append(btn)
    gate_button_axes.append(btn_ax)

# --- WIDGET: SLIDERS ---
speed_ax = fig.add_axes([0.2, 0.07, 0.65, 0.025])
speed_ax.set_facecolor('#1a1a2a')
speed_slider = Slider(speed_ax, 'Speed', 0.5, 4.0, valinit=V_MAX,
                      valstep=0.1, color='#00AACC')
speed_slider.label.set_color('white')
speed_slider.valtext.set_color('white')

density_ax = fig.add_axes([0.2, 0.035, 0.65, 0.025])
density_ax.set_facecolor('#1a1a2a')
density_slider = Slider(density_ax, 'Cars', 30, 250, valinit=N_CARS,
                        valstep=10, color='#CC8800')
density_slider.label.set_color('white')
density_slider.valtext.set_color('white')

def on_speed(val):
    sim_params['v_max'] = val

def on_density(val):
    sim_params['n_active'] = int(val)

speed_slider.on_changed(on_speed)
density_slider.on_changed(on_density)

# --- ANIMATION ---

def animate(frame):
    update_physics()

    alive = np.where(car_alive)[0]
    if len(alive) == 0:
        return scat, status_text, info_text, throughput_text

    v_max = sim_params['v_max']
    colors = np.clip(car_vy[alive] / v_max, 0, 1)
    scat.set_offsets(np.c_[car_x[alive], car_y[alive]])
    scat.set_array(colors)

    failed = TOLL_LANES - sum(gate_active)
    gate_str = ' '.join(f"G{i+1}:{'ON' if gate_active[i] else 'XX'}" for i in range(TOLL_LANES))
    status_text.set_text(f"Gates: {gate_str}")
    throughput_text.set_text(f"Flow: {throughput_display[0]:.0f} cars/sec")

    if failed > 0:
        info_text.set_text(f'{failed} gate(s) failed  —  watch congestion propagate backward')
        info_text.set_color('#FF6644')
    else:
        info_text.set_text('All gates open  —  toggle gates below to simulate failure')
        info_text.set_color('#555566')

    return scat, status_text, info_text, throughput_text

ani = animation.FuncAnimation(fig, animate, interval=33, blit=False, cache_frame_data=False)

plt.show()
