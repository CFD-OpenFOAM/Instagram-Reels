import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import Button, Slider

# --- CONSTANTS ---
ROAD_X_MIN, ROAD_X_MAX = 0.0, 100.0
ROAD_LENGTH = ROAD_X_MAX - ROAD_X_MIN
N_LANES = 3
MAX_LANES = 6
LANE_WIDTH = 1.8
LANE_Y_CENTER = 0.0

N_LIGHTS = 3
LIGHT_SPACING = ROAD_LENGTH / (N_LIGHTS + 1)

N_CARS = 140
MAX_CARS = 300
V_MAX = 1.0
ACCEL = 0.06
DECEL = 0.35
SAFE_DIST = 3.2
MIN_GAP = 1.4
STOP_DIST = 1.2
APPROACH_DIST = 14.0

SPAWN_MARGIN = 5
DESPAWN_MARGIN = 5

DEFAULT_CYCLE_PERIOD = 150
GREEN_FRACTION = 0.5

# --- MUTABLE SIM PARAMETERS ---
sim_params = {'v_max': V_MAX, 'n_active': N_CARS,
              'cycle_period': DEFAULT_CYCLE_PERIOD, 'green_wave': True,
              'n_lanes': N_LANES}

# --- GEOMETRY ---

def lane_y(lane_idx):
    n = sim_params['n_lanes']
    return LANE_Y_CENTER + (lane_idx - (n - 1) / 2.0) * LANE_WIDTH

def road_bounds():
    n = sim_params['n_lanes']
    half = (n / 2.0) * LANE_WIDTH
    return LANE_Y_CENTER - half, LANE_Y_CENTER + half

light_x = np.array([LIGHT_SPACING * (i + 1) for i in range(N_LIGHTS)])

light_offset = np.zeros(N_LIGHTS)
light_manual_override = np.full(N_LIGHTS, -1, dtype=int)
_unsynced_offsets = np.random.uniform(0, DEFAULT_CYCLE_PERIOD, N_LIGHTS)

def compute_green_wave_offsets(speed, cycle_period):
    offsets = np.zeros(N_LIGHTS)
    if speed < 0.01:
        return offsets
    for i in range(N_LIGHTS):
        travel_time = (light_x[i] - light_x[0]) / speed
        offsets[i] = travel_time % cycle_period
    return offsets

def compute_unsynced_offsets():
    return _unsynced_offsets.copy()

def apply_offsets():
    if sim_params['green_wave']:
        light_offset[:] = compute_green_wave_offsets(
            sim_params['v_max'], sim_params['cycle_period'])
    else:
        light_offset[:] = compute_unsynced_offsets()

def get_light_state(light_idx, t):
    if light_manual_override[light_idx] == 0:
        return False
    if light_manual_override[light_idx] == 1:
        return True
    period = sim_params['cycle_period']
    phase = (t - light_offset[light_idx]) % period
    return phase < period * GREEN_FRACTION

apply_offsets()

# --- SIMULATION STATE ---
car_x = np.zeros(MAX_CARS)
car_vx = np.zeros(MAX_CARS)
car_lane = np.zeros(MAX_CARS, dtype=int)
car_alive = np.zeros(MAX_CARS, dtype=bool)

throughput_count = [0]
throughput_display = [0.0]
frame_counter = [0]
sim_time = [0]

def spawn_car(i):
    car_lane[i] = np.random.randint(0, sim_params['n_lanes'])
    car_x[i] = np.random.uniform(-7, -5)
    car_vx[i] = sim_params['v_max'] * np.random.uniform(0.92, 1.0)
    car_alive[i] = True

for i in range(N_CARS):
    spawn_car(i)
    car_x[i] = np.random.uniform(ROAD_X_MIN - SPAWN_MARGIN, ROAD_X_MAX + 2)
    car_vx[i] = sim_params['v_max'] * np.random.uniform(0.9, 1.0)

# --- PHYSICS ---

def update_physics():
    sim_time[0] += 1
    frame_counter[0] += 1
    v_max = sim_params['v_max']
    n_target = int(sim_params['n_active'])

    if frame_counter[0] % 30 == 0:
        throughput_display[0] = throughput_count[0]
        throughput_count[0] = 0

    n_alive = int(np.sum(car_alive))
    if n_alive < n_target:
        for i in range(MAX_CARS):
            if not car_alive[i]:
                spawn_car(i)
                n_alive += 1
                if n_alive >= n_target:
                    break
    elif n_alive > n_target:
        kill = n_alive - n_target
        for i in range(MAX_CARS - 1, -1, -1):
            if car_alive[i] and kill > 0:
                car_alive[i] = False
                kill -= 1

    alive_idx = np.where(car_alive)[0]
    to_respawn = []

    light_is_green = np.array([get_light_state(li, sim_time[0]) for li in range(N_LIGHTS)])

    lane_cars = {}
    for ln in range(sim_params['n_lanes']):
        indices = [i for i in alive_idx if car_lane[i] == ln]
        indices.sort(key=lambda i: -car_x[i])
        lane_cars[ln] = indices

    for i in alive_idx:
        x = car_x[i]
        v_desired = v_max

        for li in range(N_LIGHTS):
            if light_is_green[li]:
                continue
            dist_to_light = light_x[li] - x
            if dist_to_light < -0.5:
                continue
            if dist_to_light <= STOP_DIST:
                v_desired = 0.0
                break
            elif dist_to_light < APPROACH_DIST:
                frac = (dist_to_light - STOP_DIST) / (APPROACH_DIST - STOP_DIST)
                v_desired = min(v_desired, max(0.0, v_max * frac * frac))
                break

        ln = car_lane[i]
        queue = lane_cars[ln]
        my_pos = None
        for qi, qidx in enumerate(queue):
            if qidx == i:
                my_pos = qi
                break
        if my_pos is not None and my_pos > 0:
            leader = queue[my_pos - 1]
            gap = car_x[leader] - x
            if 0 < gap < SAFE_DIST * 2.5:
                if gap < SAFE_DIST:
                    v_desired = min(v_desired, car_vx[leader] * (gap / SAFE_DIST))
                elif gap < SAFE_DIST * 1.5:
                    v_desired = min(v_desired, car_vx[leader] + 0.1)

        v_desired = max(0.0, v_desired)
        diff = v_desired - car_vx[i]
        if diff > 0:
            car_vx[i] += ACCEL * diff
        else:
            car_vx[i] += DECEL * diff

        car_vx[i] = np.clip(car_vx[i], 0.0, v_max * 1.15)
        car_x[i] += car_vx[i]

        if car_x[i] > 107:
            throughput_count[0] += 1
            to_respawn.append(i)

    for ln in range(sim_params['n_lanes']):
        queue = lane_cars[ln]
        for qi in range(1, len(queue)):
            leader = queue[qi - 1]
            follower = queue[qi]
            if leader in to_respawn or follower in to_respawn:
                continue
            gap = car_x[leader] - car_x[follower]
            if gap < MIN_GAP:
                car_x[follower] = car_x[leader] - MIN_GAP
                car_vx[follower] = min(car_vx[follower], car_vx[leader])

    for i in to_respawn:
        spawn_car(i)

# --- RENDERING ---
print("Shockwave Traffic Light Simulator")
print("Watch how stopping at a red light sends a shockwave backward through traffic.")
print("Toggle green wave, override lights, adjust speed & density.")

fig = plt.figure(figsize=(13, 7))
fig.patch.set_facecolor('#0a0a0a')

ax = fig.add_axes([0.03, 0.40, 0.94, 0.55])
ax.set_facecolor('#0a0a0a')
ax.set_xlim(-8, 108)
max_top = LANE_Y_CENTER + (MAX_LANES / 2.0) * LANE_WIDTH + 4.0
max_bot = LANE_Y_CENTER - (MAX_LANES / 2.0) * LANE_WIDTH - 2.0
ax.set_ylim(max_bot, max_top)
ax.set_xticks([])
ax.set_yticks([])

road_artists = []
light_circles = []
light_labels = []

def rebuild_road():
    for artist in road_artists:
        artist.remove()
    road_artists.clear()

    road_bot, road_top = road_bounds()
    rr = patches.Rectangle(
        (-10, road_bot), ROAD_LENGTH + 20, road_top - road_bot,
        facecolor='#1a1a24', edgecolor='none', zorder=1
    )
    ax.add_patch(rr)
    road_artists.append(rr)

    ret = patches.Rectangle(
        (-10, road_top - 0.08), ROAD_LENGTH + 20, 0.16,
        facecolor='#333344', edgecolor='none', zorder=2
    )
    reb = patches.Rectangle(
        (-10, road_bot - 0.08), ROAD_LENGTH + 20, 0.16,
        facecolor='#333344', edgecolor='none', zorder=2
    )
    ax.add_patch(ret); ax.add_patch(reb)
    road_artists.extend([ret, reb])

    n = sim_params['n_lanes']
    for ln in range(1, n):
        y_line = (lane_y(ln) + lane_y(ln - 1)) / 2
        for dash_start in np.arange(-10, ROAD_X_MAX + 10, 4):
            ln_a, = ax.plot([dash_start, min(dash_start + 2, ROAD_X_MAX + 10)],
                            [y_line, y_line],
                            color='#444455', lw=0.8, alpha=0.5, zorder=2)
            road_artists.append(ln_a)

    light_y_pos = road_top + 1.8
    for li in range(N_LIGHTS):
        pole, = ax.plot([light_x[li], light_x[li]],
                        [road_top + 0.1, light_y_pos - 0.9],
                        color='#444444', lw=2.5, zorder=7)
        road_artists.append(pole)
        white_line, = ax.plot([light_x[li], light_x[li]],
                              [road_bot + 0.15, road_top - 0.15],
                              color='#ffffff', lw=1.2, alpha=0.15, zorder=2)
        road_artists.append(white_line)
        light_circles[li].center = (light_x[li], light_y_pos)
        light_labels[li].set_position((light_x[li], light_y_pos + 1.8))

for li in range(N_LIGHTS):
    circle = plt.Circle((light_x[li], 0), 1.0,
                        facecolor='#00CC44', edgecolor='#555555',
                        linewidth=2, zorder=8)
    ax.add_patch(circle)
    light_circles.append(circle)
    label = ax.text(light_x[li], 0, f"L{li+1}", color='#666677',
                    fontsize=8, ha='center', va='bottom', zorder=9,
                    fontweight='bold')
    light_labels.append(label)

rebuild_road()

cmap = LinearSegmentedColormap.from_list('traffic', ['#FF0044', '#FFAA00', '#00FFCC'], N=256)
scat = ax.scatter([], [], s=40, c=[], cmap=cmap, vmin=0, vmax=1,
                  zorder=5, edgecolors='none')

mode_text = ax.text(104, max_top - 0.5, '', color='#00FFCC', fontsize=10,
                    fontfamily='monospace', va='top', ha='right', zorder=10,
                    fontweight='bold')
status_text = ax.text(-4, max_top - 0.5, '', color='#888899', fontsize=8,
                      fontfamily='monospace', va='top', zorder=10)
info_text = ax.text(50, max_bot + 0.4, '', color='#555566', fontsize=8,
                    ha='center', va='bottom', zorder=10)

shockwave_label = ax.text(50, max_bot + 1.3, '', color='#FF6644', fontsize=9,
                          ha='center', va='bottom', zorder=10, fontweight='bold',
                          fontfamily='monospace', alpha=0.0)

# --- WIDGET: GREEN WAVE TOGGLE ---
wave_ax = fig.add_axes([0.15, 0.33, 0.70, 0.045])
wave_ax.set_facecolor('#003333')
wave_btn = Button(wave_ax, 'GREEN WAVE: ON', color='#003333', hovercolor='#005555')
wave_btn.label.set_color('#00FFCC')
wave_btn.label.set_fontsize(11)
wave_btn.label.set_fontfamily('monospace')
wave_btn.label.set_fontweight('bold')

def toggle_wave(event):
    sim_params['green_wave'] = not sim_params['green_wave']
    if sim_params['green_wave']:
        wave_btn.label.set_text('GREEN WAVE: ON')
        wave_btn.label.set_color('#00FFCC')
        wave_ax.set_facecolor('#003333')
        wave_btn.color = '#003333'
        wave_btn.hovercolor = '#005555'
    else:
        wave_btn.label.set_text('GREEN WAVE: OFF  —  Random Timing')
        wave_btn.label.set_color('#FF6644')
        wave_ax.set_facecolor('#331100')
        wave_btn.color = '#331100'
        wave_btn.hovercolor = '#552200'
    apply_offsets()
    fig.canvas.draw_idle()

wave_btn.on_clicked(toggle_wave)

# --- WIDGET: LIGHT BUTTONS ---
light_buttons = []
btn_width = 0.18
total_btns_width = N_LIGHTS * btn_width + (N_LIGHTS - 1) * 0.02
btn_start_x = 0.5 - total_btns_width / 2

for li in range(N_LIGHTS):
    bx = btn_start_x + li * (btn_width + 0.02)
    btn_ax = fig.add_axes([bx, 0.28, btn_width, 0.035])
    btn_ax.set_facecolor('#112211')
    btn = Button(btn_ax, f'Light {li+1}: Auto', color='#112211', hovercolor='#224422')
    btn_ax.set_navigate(False)

    def make_light_toggle(idx):
        def toggle(event):
            current = light_manual_override[idx]
            light_manual_override[idx] = {-1: 0, 0: 1, 1: -1}[current]
            labels = {-1: f'Light {idx+1}: Auto', 0: f'Light {idx+1}: RED', 1: f'Light {idx+1}: GRN'}
            colors_map = {-1: '#112211', 0: '#441111', 1: '#114411'}
            hover_map = {-1: '#224422', 0: '#662222', 1: '#226622'}
            ov = light_manual_override[idx]
            light_buttons[idx].label.set_text(labels[ov])
            light_buttons[idx].ax.set_facecolor(colors_map[ov])
            light_buttons[idx].color = colors_map[ov]
            light_buttons[idx].hovercolor = hover_map[ov]
            fig.canvas.draw_idle()
        return toggle

    btn.on_clicked(make_light_toggle(li))
    btn.label.set_color('white')
    btn.label.set_fontsize(8)
    light_buttons.append(btn)

# --- WIDGET: SLIDERS ---
speed_ax = fig.add_axes([0.20, 0.22, 0.65, 0.022])
speed_ax.set_facecolor('#1a1a2a')
speed_slider = Slider(speed_ax, 'Speed', 0.3, 2.0, valinit=V_MAX,
                      valstep=0.1, color='#00AACC')
speed_slider.label.set_color('white')
speed_slider.valtext.set_color('white')

cycle_ax = fig.add_axes([0.20, 0.17, 0.65, 0.022])
cycle_ax.set_facecolor('#1a1a2a')
cycle_slider = Slider(cycle_ax, 'Period', 60, 300, valinit=DEFAULT_CYCLE_PERIOD,
                      valstep=10, color='#CCAA00')
cycle_slider.label.set_color('white')
cycle_slider.valtext.set_color('white')

density_ax = fig.add_axes([0.20, 0.12, 0.65, 0.022])
density_ax.set_facecolor('#1a1a2a')
density_slider = Slider(density_ax, 'Cars', 30, 250, valinit=N_CARS,
                        valstep=10, color='#CC8800')
density_slider.label.set_color('white')
density_slider.valtext.set_color('white')

lanes_ax = fig.add_axes([0.20, 0.07, 0.65, 0.022])
lanes_ax.set_facecolor('#1a1a2a')
lanes_slider = Slider(lanes_ax, 'Lanes', 1, MAX_LANES, valinit=N_LANES,
                      valstep=1, color='#AA44CC')
lanes_slider.label.set_color('white')
lanes_slider.valtext.set_color('white')

def on_speed(val):
    sim_params['v_max'] = val
    apply_offsets()

def on_cycle(val):
    sim_params['cycle_period'] = int(val)
    apply_offsets()

def on_density(val):
    sim_params['n_active'] = int(val)

def on_lanes(val):
    new_n = int(val)
    if new_n == sim_params['n_lanes']:
        return
    sim_params['n_lanes'] = new_n
    for i in range(MAX_CARS):
        if car_alive[i] and car_lane[i] >= new_n:
            car_lane[i] = np.random.randint(0, new_n)
    rebuild_road()
    fig.canvas.draw_idle()

speed_slider.on_changed(on_speed)
cycle_slider.on_changed(on_cycle)
density_slider.on_changed(on_density)
lanes_slider.on_changed(on_lanes)

# --- SHOCKWAVE DETECTION ---

def count_stopped_cars():
    alive = np.where(car_alive)[0]
    return int(np.sum(car_vx[alive] < 0.05))

# --- ANIMATION ---

def animate(frame):
    update_physics()

    alive = np.where(car_alive)[0]
    if len(alive) == 0:
        return (scat, status_text, mode_text, info_text, shockwave_label) + tuple(light_circles)

    v_max = sim_params['v_max']
    xs = car_x[alive]
    ys = np.array([lane_y(car_lane[i]) for i in alive])
    colors = np.clip(car_vx[alive] / v_max, 0, 1)

    scat.set_offsets(np.c_[xs, ys])
    scat.set_array(colors)

    for li in range(N_LIGHTS):
        is_green = get_light_state(li, sim_time[0])
        if is_green:
            light_circles[li].set_facecolor('#00CC44')
            light_circles[li].set_edgecolor('#00FF55')
        else:
            light_circles[li].set_facecolor('#FF0044')
            light_circles[li].set_edgecolor('#FF2255')

    if sim_params['green_wave']:
        mode_text.set_text('GREEN WAVE')
        mode_text.set_color('#00FFCC')
    else:
        mode_text.set_text('UNSYNCED')
        mode_text.set_color('#FF6644')

    status_text.set_text(f"Flow: {throughput_display[0]:.0f} cars/sec  |  Lanes: {sim_params['n_lanes']}  Cars: {int(sim_params['n_active'])}")

    stopped_now = count_stopped_cars()
    if stopped_now > 8:
        shockwave_label.set_alpha(min(1.0, stopped_now / 20.0))
        shockwave_label.set_text(f'Shockwave: {stopped_now} cars stopped — wave propagating backward')
    elif stopped_now > 3:
        shockwave_label.set_alpha(0.5)
        shockwave_label.set_text(f'Queue building: {stopped_now} cars slowing')
    else:
        shockwave_label.set_alpha(0.0)

    override_count = sum(1 for o in light_manual_override if o >= 0)
    cars_per_lane = sim_params['n_active'] / max(1, sim_params['n_lanes'])
    if override_count > 0:
        info_text.set_text(f'{override_count} light(s) overridden — observe shockwave propagation')
        info_text.set_color('#FF6644')
    elif cars_per_lane > 55:
        info_text.set_text('More lanes ≠ less congestion — lights are the bottleneck, not lane count')
        info_text.set_color('#FF8855')
    elif sim_params['green_wave']:
        info_text.set_text('Cars surf through all greens at the speed limit — no shockwave')
        info_text.set_color('#00BBAA')
    else:
        info_text.set_text('Random timing — shockwaves form and ripple backward through traffic')
        info_text.set_color('#FF8855')

    return (scat, status_text, mode_text, info_text, shockwave_label) + tuple(light_circles)

ani = animation.FuncAnimation(fig, animate, interval=33, blit=False, cache_frame_data=False)
plt.show()
