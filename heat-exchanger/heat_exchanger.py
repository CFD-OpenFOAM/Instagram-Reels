import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

# --- Physics Setup ---
# T_h: Hot Fluid (Entering at 100°C)
# T_c: Cold Fluid (Entering at 20°C)
T_h_in = 100.0
T_c_in = 20.0
x = np.linspace(0, 1, 100) # Pipe length from 0 to 100%

# State variable
is_parallel = True 

# --- Figure Setup (MOBILE PORTRAIT 9:16 RATIO) ---
fig, ax = plt.subplots(figsize=(4.5, 8))
plt.subplots_adjust(bottom=0.35) # Room for controls

ax.set_xlim(0, 1)
ax.set_ylim(10, 110)
ax.set_title("Heat Exchanger Thermal Profile")
ax.set_ylabel("Temperature (°C)")
ax.set_xlabel("Position Along Pipe")
ax.set_xticks([0, 0.5, 1.0])
ax.set_xticklabels(['Start', 'Middle', 'End'])

# The Fluid Temperature Lines
line_h, = ax.plot(x, np.zeros_like(x), color='#E74C3C', lw=5, label='Hot Fluid')
line_c, = ax.plot(x, np.zeros_like(x), color='#0047AB', lw=5, label='Cold Fluid')

ax.legend(loc='upper right', fontsize='small')

# --- Interactive Controls ---
axcolor = 'lightgoldenrodyellow'
ax_ntu = plt.axes([0.25, 0.20, 0.6, 0.03], facecolor=axcolor)
ax_btn = plt.axes([0.25, 0.08, 0.6, 0.06])

# NTU represents the "Number of Transfer Units" (Pipe Length / Area)
s_ntu = Slider(ax_ntu, 'Pipe Length', 0.1, 10.0, valinit=2.0)
btn_flow = Button(ax_btn, 'Mode: Parallel Flow', hovercolor='0.975')

def update(val):
    ntu = s_ntu.val
    
    if is_parallel:
        # Parallel Flow Math: Exponential decay towards the average temperature
        Th = T_h_in - (T_h_in - T_c_in) * (1 - np.exp(-2 * ntu * x)) / 2
        Tc = T_c_in + (T_h_in - T_c_in) * (1 - np.exp(-2 * ntu * x)) / 2
    else:
        # Counter-Flow Math: Constant temperature gradient
        Th = T_h_in - (T_h_in - T_c_in) * (ntu / (1 + ntu)) * x
        # Cold fluid enters at x=1 (End of pipe) at 20°C
        Tc = Th - (T_h_in - T_c_in) / (1 + ntu)

    line_h.set_ydata(Th)
    line_c.set_ydata(Tc)
    fig.canvas.draw_idle()

def toggle_flow(event):
    global is_parallel
    is_parallel = not is_parallel
    btn_flow.label.set_text('Mode: Parallel Flow' if is_parallel else 'Mode: Counter-Flow')
    
    # Change colors slightly to indicate direction change in counter flow
    if is_parallel:
        line_c.set_linestyle('-')
    else:
        line_c.set_linestyle('--') # Dashed visually implies reverse direction
        
    update(None)

s_ntu.on_changed(update)
btn_flow.on_clicked(toggle_flow)

# Initialize the plot
update(None)
plt.show()