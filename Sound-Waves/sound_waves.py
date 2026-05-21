import numpy as np
import matplotlib.pyplot as plt
import multiprocessing as mp
import os
import shutil
import gc # The Garbage Collector for RAM flushing

# --- Audio Imports ---
from scipy.io import wavfile
from scipy.signal import spectrogram

# --- 1. THE ISOLATED WORKER FUNCTION ---
def render_single_frame(args):
    frame, fps, audio, fs, duration, f, t_spec, Sxx = args
    current_time = frame / fps

    # Setup a NEW figure
    fig, (ax_spec, ax_part) = plt.subplots(2, 1, figsize=(4.5, 8), 
                                           gridspec_kw={'height_ratios': [1, 1]})
    fig.tight_layout(pad=3.0)
    fig.patch.set_facecolor('#000000') 

    # --- Top: Spectrogram ---
    ax_spec.set_facecolor('#000000')
    ax_spec.set_title("Vocal Cord Frequencies (Spectrogram)", color='white')
    ax_spec.set_ylabel("Frequency (Hz)", color='white')
    ax_spec.tick_params(colors='white')
    ax_spec.set_xlim(0, duration)
    ax_spec.set_ylim(0, 4000) 
    
    # Rasterized drawing is much faster for massive .wav arrays
    ax_spec.pcolormesh(t_spec, f, 10 * np.log10(Sxx + 1e-10), cmap='magma', shading='auto', rasterized=True)
    ax_spec.axvline(x=current_time, color='#00FFFF', lw=3)

    # --- Bottom: Digital Wind Tunnel ---
    ax_part.set_facecolor('#000000')
    ax_part.set_title("Air Molecule Compression (Longitudinal Wave)", color='white')
    ax_part.set_xticks([])
    ax_part.set_yticks([])
    ax_part.set_xlim(0, 1)
    ax_part.set_ylim(0, 1)

    np.random.seed(42)
    N_PARTICLES = 1500
    x_base = np.random.rand(N_PARTICLES)
    y_base = np.random.rand(N_PARTICLES)

    # Vectorized Physics
    wave_speed = 0.5 
    particle_times = current_time - (x_base / wave_speed)
    idxs = (particle_times * fs).astype(int)
    valid_mask = (particle_times >= 0) & (particle_times <= duration) & (idxs < len(audio))
    
    displacement = np.zeros_like(x_base)
    displacement[valid_mask] = audio[idxs[valid_mask]] * 0.15 
    x_new = (x_base + displacement) % 1.0
    
    ax_part.scatter(x_new, y_base, s=8, color='#0047AB', alpha=0.8)

    # --- Save and Aggressive Cleanup ---
    filename = f"render_frames/frame_{frame:04d}.png"
    plt.savefig(filename, facecolor=fig.get_facecolor(), edgecolor='none')
    
    # Violently destroy the figure in RAM
    fig.clf() 
    plt.close('all') 
    
    return frame

# --- 2. THE BATCHED ORCHESTRATOR ---
if __name__ == '__main__':
    
    print("Initializing Wrench-Wise Batch Render Engine...")
    
    if os.path.exists("render_frames"):
        shutil.rmtree("render_frames") 
    os.makedirs("render_frames")

    AUDIO_FILE = "sound-waves.wav" 

    if os.path.exists(AUDIO_FILE):
        print(f"Loading large .wav file natively...")
        fs, data = wavfile.read(AUDIO_FILE)
        
        if data.ndim > 1:
            data = data.mean(axis=1)
            
        audio = data / np.max(np.abs(data))
        duration = len(audio) / fs
    else:
        print(f"Error: Could not find {AUDIO_FILE}.")
        exit()

    print("Calculating Spectrogram Frequencies...")
    f, t_spec, Sxx = spectrogram(audio, fs, nperseg=1024, noverlap=512)

    fps = 30
    total_frames = int(duration * fps)
    
    # --- BATCH CONFIGURATION ---
    # Process exactly 100 frames at a time to save RAM
    BATCH_SIZE = 100 
    cores = 4

    print(f"\nTotal frames to render: {total_frames}")
    print(f"Batch size: {BATCH_SIZE} frames per chunk.")
    print("Unleashing the swarm...\n")

    # The Outer Loop: Process in chunks
    for batch_start in range(0, total_frames, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_frames)
        print(f"🚀 Initiating Batch: Frames {batch_start} to {batch_end - 1}...")

        # Package only the tasks for THIS specific batch
        batch_tasks = [(i, fps, audio, fs, duration, f, t_spec, Sxx) for i in range(batch_start, batch_end)]

        # Spin up the CPU pool for just these frames
        with mp.Pool(processes=cores) as pool:
            for i, _ in enumerate(pool.imap_unordered(render_single_frame, batch_tasks), 1):
                if i % 25 == 0:
                    print(f"  -> Batch Progress: {i} / {len(batch_tasks)} complete.")

        # --- THE MAGIC RAM FLUSH ---
        print("🧹 Batch complete. Flushing RAM...")
        del batch_tasks
        gc.collect() # Force Python to dump all orphaned memory

    print("\n--- RENDER COMPLETE ---")
    print("Your images are waiting in the 'render_frames' folder.")