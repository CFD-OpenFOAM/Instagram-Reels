import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import Slider, Button

print("Initializing Live EV Battery Thermal Dashboard...")

# --- 1. SIMULATION GRID & GEOMETRY ---
nx, ny = 90, 120
T = np.full((ny, nx), 25.0)

battery_mask = np.zeros((ny, nx), dtype=bool)
cooling_mask = np.zeros((ny, nx), dtype=bool)

cell_w, cool_w, space = 20, 6, 12
c1_x = space
c2_x = space + cell_w + cool_w
c3_x = space + 2 * cell_w + 2 * cool_w

battery_mask[15:105, c1_x : c1_x + cell_w] = True
cooling_mask[15:105, c1_x + cell_w : c1_x + cell_w + cool_w] = True
battery_mask[15:105, c2_x : c2_x + cell_w] = True
cooling_mask[15:105, c2_x + cell_w : c2_x + cell_w + cool_w] = True
battery_mask[15:105, c3_x : c3_x + cell_w] = True

# --- 2. THERMAL PHYSICS STATE ---
# alpha_bat MUST be <= 0.25 for 2D explicit Euler stability (CFL condition).
alpha_bat = 0.2
ambient = 25.0
SUBSTEPS = 4  # Run physics N times per visual frame for stronger effective diffusion.
Q_SCALE = 0.030  # Heat generation factor per frame (tuned for reasonable steady states).
COOL_SCALE = 0.10  # Convective cooling factor per frame (tuned for visible response).
AMB_BLEED = 0.0005  # Weak ambient bleed so cooling channels do the real work.

sim_state = {
    'power_kw': 150.0,
    'flow_lpm': 10.0,
    'coolant_temp': 20.0,
    'efficiency': 0.95,
    'max_temp': 25.0,
}

max_temp_history = []
HISTORY_LEN = 600


def update_physics():
    global T

    waste_heat_kw = sim_state['power_kw'] * (1.0 - sim_state['efficiency'])
    q_step = (waste_heat_kw * Q_SCALE) / SUBSTEPS
    cs_step = (sim_state['flow_lpm'] * COOL_SCALE) / SUBSTEPS
    amb_step = AMB_BLEED / SUBSTEPS
    T_cool = sim_state['coolant_temp']

    for _ in range(SUBSTEPS):
        T_up = np.roll(T, 1, axis=0)
        T_down = np.roll(T, -1, axis=0)
        T_left = np.roll(T, 1, axis=1)
        T_right = np.roll(T, -1, axis=1)

        T_up[0, :] = T[0, :]
        T_down[-1, :] = T[-1, :]
        T_left[:, 0] = T[:, 0]
        T_right[:, -1] = T[:, -1]

        laplacian = T_up + T_down + T_left + T_right - 4 * T

        T_new = T.copy()
        T_new[battery_mask] += alpha_bat * laplacian[battery_mask] + q_step
        T_new[cooling_mask] += alpha_bat * laplacian[cooling_mask]

        # Implicit Newton cooling: unconditionally stable for any cs_step >= 0.
        T_new[cooling_mask] = (T_new[cooling_mask] + cs_step * T_cool) / (1.0 + cs_step)

        T_new -= amb_step * (T_new - ambient)

        T_new = np.clip(T_new, 0.0, 150.0)
        T = T_new

    sim_state['max_temp'] = float(np.max(T[battery_mask]))
    max_temp_history.append(sim_state['max_temp'])
    if len(max_temp_history) > HISTORY_LEN:
        max_temp_history.pop(0)


# --- 3. UI & RENDERING ---
fig = plt.figure(figsize=(14, 9))
fig.patch.set_facecolor('#0a0a0a')
fig.canvas.manager.set_window_title('EV Battery Thermal Management Simulator')

# -- Heatmap --
ax_main = fig.add_axes([0.04, 0.32, 0.38, 0.58])
ax_main.set_facecolor('#0a0a0a')
ax_main.set_xticks([])
ax_main.set_yticks([])
ax_main.set_title('Cell Cross-Section', color='#888888', fontsize=10, fontfamily='monospace', pad=4)

colors = ['#001133', '#00AACC', '#11AA44', '#FFCC00', '#FF0044', '#FFFFFF']
cmap = LinearSegmentedColormap.from_list('thermal', colors, N=256)
img = ax_main.imshow(T, cmap=cmap, vmin=20, vmax=90, interpolation='bilinear')

ax_cbar = fig.add_axes([0.43, 0.32, 0.012, 0.58])
cbar = fig.colorbar(img, cax=ax_cbar)
cbar.set_label('Temperature (°C)', color='#888888', fontsize=9)
cbar.ax.yaxis.set_tick_params(color='#888888')
plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#888888', fontsize=8)

# -- Dashboard Text --
ax_text = fig.add_axes([0.50, 0.32, 0.22, 0.58])
ax_text.set_facecolor('#0a0a0a')
ax_text.axis('off')

ax_text.text(0, 0.95, 'EV THERMAL', color='#00FFFF', fontsize=15, fontweight='bold', fontfamily='monospace')
ax_text.text(0, 0.88, 'MANAGEMENT', color='#00FFFF', fontsize=15, fontweight='bold', fontfamily='monospace')

txt_power = ax_text.text(0, 0.72, '', color='#FFFFFF', fontsize=11, fontfamily='monospace')
txt_waste = ax_text.text(0, 0.63, '', color='#FF4444', fontsize=11, fontfamily='monospace', fontweight='bold')
txt_flow = ax_text.text(0, 0.50, '', color='#00AACC', fontsize=11, fontfamily='monospace')
txt_cool = ax_text.text(0, 0.41, '', color='#4488FF', fontsize=11, fontfamily='monospace')
txt_temp = ax_text.text(0, 0.24, '', color='#FFFFFF', fontsize=15, fontfamily='monospace', fontweight='bold')
txt_warn = ax_text.text(0, 0.10, '', color='#FF0044', fontsize=11, fontfamily='monospace', fontweight='bold')

# -- Temperature History Plot --
ax_hist = fig.add_axes([0.74, 0.32, 0.24, 0.58])
ax_hist.set_facecolor('#0a0a0a')
ax_hist.set_title('Max Cell Temp History', color='#888888', fontsize=10, fontfamily='monospace', pad=4)
ax_hist.set_ylabel('°C', color='#888888', fontsize=9)
ax_hist.set_xlabel('Time Steps', color='#888888', fontsize=9)
ax_hist.tick_params(colors='#555555', labelsize=8)
for spine in ax_hist.spines.values():
    spine.set_color('#333333')
ax_hist.set_ylim(15, 100)
ax_hist.set_xlim(0, HISTORY_LEN)

ax_hist.axhline(y=45, color='#FFCC00', linestyle='--', linewidth=0.8, alpha=0.7)
ax_hist.axhline(y=60, color='#FF0044', linestyle='--', linewidth=0.8, alpha=0.7)
ax_hist.text(HISTORY_LEN * 0.01, 46, 'Degradation', color='#FFCC00', fontsize=7, fontfamily='monospace', alpha=0.8)
ax_hist.text(HISTORY_LEN * 0.01, 61, 'Runaway', color='#FF0044', fontsize=7, fontfamily='monospace', alpha=0.8)

(line_hist,) = ax_hist.plot([], [], color='#00FFCC', linewidth=1.5)

# -- Sliders --
ax_power = fig.add_axes([0.12, 0.20, 0.55, 0.025])
ax_power.set_facecolor('#1a1a2a')
sl_power = Slider(ax_power, 'Charge (kW)', 50.0, 350.0, valinit=150.0, color='#FFCC00')
sl_power.label.set_color('white')
sl_power.valtext.set_color('white')

ax_flow = fig.add_axes([0.12, 0.155, 0.55, 0.025])
ax_flow.set_facecolor('#1a1a2a')
sl_flow = Slider(ax_flow, 'Coolant (L/min)', 0.0, 100.0, valinit=10.0, color='#00AACC')
sl_flow.label.set_color('white')
sl_flow.valtext.set_color('white')

ax_cooltemp = fig.add_axes([0.12, 0.11, 0.55, 0.025])
ax_cooltemp.set_facecolor('#1a1a2a')
sl_cooltemp = Slider(ax_cooltemp, 'Coolant Temp (°C)', 5.0, 40.0, valinit=20.0, color='#4488FF')
sl_cooltemp.label.set_color('white')
sl_cooltemp.valtext.set_color('white')


def on_power(val):
    sim_state['power_kw'] = val


def on_flow(val):
    sim_state['flow_lpm'] = val


def on_cooltemp(val):
    sim_state['coolant_temp'] = val


sl_power.on_changed(on_power)
sl_flow.on_changed(on_flow)
sl_cooltemp.on_changed(on_cooltemp)

# -- Scenario Buttons --
btn_color = '#1a1a2a'
btn_hover = '#2a2a4a'

ax_btn_reset = fig.add_axes([0.74, 0.20, 0.10, 0.035])
btn_reset = Button(ax_btn_reset, 'Reset', color=btn_color, hovercolor=btn_hover)
btn_reset.label.set_color('#00FF88')
btn_reset.label.set_fontsize(9)

ax_btn_maxchg = fig.add_axes([0.86, 0.20, 0.12, 0.035])
btn_maxchg = Button(ax_btn_maxchg, 'Max Charge', color=btn_color, hovercolor=btn_hover)
btn_maxchg.label.set_color('#FFCC00')
btn_maxchg.label.set_fontsize(9)

ax_btn_coolfail = fig.add_axes([0.74, 0.155, 0.10, 0.035])
btn_coolfail = Button(ax_btn_coolfail, 'Cool Fail', color=btn_color, hovercolor=btn_hover)
btn_coolfail.label.set_color('#FF4444')
btn_coolfail.label.set_fontsize(9)

ax_btn_normal = fig.add_axes([0.86, 0.155, 0.12, 0.035])
btn_normal = Button(ax_btn_normal, 'Normal', color=btn_color, hovercolor=btn_hover)
btn_normal.label.set_color('#00AACC')
btn_normal.label.set_fontsize(9)


def reset_sim(_event):
    global T
    T = np.full((ny, nx), 25.0)
    max_temp_history.clear()
    sim_state['max_temp'] = 25.0


def set_max_charge(_event):
    sl_power.set_val(350.0)
    sl_flow.set_val(10.0)


def set_cooling_fail(_event):
    sl_flow.set_val(0.0)


def set_normal(_event):
    sl_power.set_val(150.0)
    sl_flow.set_val(10.0)
    sl_cooltemp.set_val(20.0)


btn_reset.on_clicked(reset_sim)
btn_maxchg.on_clicked(set_max_charge)
btn_coolfail.on_clicked(set_cooling_fail)
btn_normal.on_clicked(set_normal)

# -- Footer --
fig.text(0.5, 0.04, 'Drag sliders to explore thermal behavior  |  Watch the history plot to see trends',
         color='#555555', fontsize=9, fontfamily='monospace', ha='center')


# --- 4. ANIMATION LOOP ---
def animate(_frame):
    update_physics()

    img.set_data(T)

    waste_kw = sim_state['power_kw'] * (1.0 - sim_state['efficiency'])
    txt_power.set_text(f"DC Fast Charge : {sim_state['power_kw']:>5.0f} kW")
    txt_waste.set_text(f"Waste Heat     : {waste_kw:>5.1f} kW")
    txt_flow.set_text(f"Pump Flow Rate : {sim_state['flow_lpm']:>5.1f} L/min")
    txt_cool.set_text(f"Coolant Temp   : {sim_state['coolant_temp']:>5.1f} °C")

    t_max = sim_state['max_temp']
    txt_temp.set_text(f"Core Temp: {t_max:.1f} °C")

    if t_max > 60.0:
        txt_temp.set_color('#FF0044')
        txt_warn.set_text("⚠ CRITICAL: THERMAL RUNAWAY RISK")
    elif t_max > 45.0:
        txt_temp.set_color('#FFCC00')
        txt_warn.set_text("⚠ WARNING: CELL DEGRADATION")
    else:
        txt_temp.set_color('#11AA44')
        txt_warn.set_text("✓ SYSTEM STABLE")

    hist_len = len(max_temp_history)
    if hist_len > 0:
        line_hist.set_data(range(hist_len), max_temp_history)
        ax_hist.set_xlim(0, max(HISTORY_LEN, hist_len))
        y_max = max(100, max(max_temp_history) + 10)
        ax_hist.set_ylim(15, y_max)

    return [img, txt_power, txt_waste, txt_flow, txt_cool, txt_temp, txt_warn, line_hist]


print("Running Live Interactive Dashboard...")
ani = animation.FuncAnimation(fig, animate, interval=30, blit=False, cache_frame_data=False)
plt.show()
