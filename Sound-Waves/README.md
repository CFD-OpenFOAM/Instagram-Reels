#️ The Physical Battering Ram: Sound Wave Visualizer

Welcome to the digital wind tunnel. This repository contains a high-performance, parallelized Python rendering engine built to visualize the physical reality of human speech.

Most people think of sound as invisible magic or a squiggly line on a screen. This script proves that sound is actually a longitudinal wave—a physical battering ram of air molecules.

This tool is part of the **Wrench-Wise** educational series and the **Physics By Design** curriculum. 

## The Physics: What are you looking at?

When you run an audio file through this engine, it generates a two-part visualization:

1. **Top - The Frequency Fingerprint (Spectrogram):** You are using your lungs as a meat-bellows to push air past your vocal cords. The top graph uses a Fast Fourier Transform (FFT) to map the exact frequencies those cords are producing in real-time. 
2. **Bottom - The Digital Wind Tunnel:** Sound is a longitudinal wave. Those pressure fluctuations act like a piston, violently shoving actual, physical air molecules into the molecules next to them. The bottom graph simulates 1,500 digital air molecules being physically compressed and pushed across the screen by the amplitude of your voice.

## The Architecture: Why is the code built like this?

Visualizing millions of data points from an uncompressed `.wav` file is computationally heavy. If you run this on a single processor core, it will take hours and eventually crash your computer. 

To fix this, this script uses **"Insane Engineering" for Computer Science:**
* **Multiprocessing Swarm:** It bypasses the Python Global Interpreter Lock (GIL) by spawning completely isolated worker processes across 4 of your CPU cores.
* **Batch Processing & RAM Flushing:** Matplotlib is notorious for memory leaks. This engine processes exactly 100 frames at a time. After each batch, it shuts down the CPU pool, violently flushes the orphaned data from your RAM using Python's internal Garbage Collector (`gc.collect()`), and spins the cores back up for the next round.
* **Vectorized Physics:** The particle math is written in NumPy to calculate the trajectories of all 1,500 particles simultaneously, rather than one by one.

## How to Run the Render Engine

### 1. Prerequisites
You need standard Python scientific libraries and the FFmpeg media encoder.
```bash
# Install Python libraries
pip install numpy matplotlib scipy

# Install FFmpeg (Mac users via Homebrew)
brew install ffmpeg

```

### 2. Prepare Your Audio

Drop your uncompressed audio file into the exact same folder as the Python script.
**Crucial:** The file must be named exactly `sound-waves.wav`.

### 3. Unleash the Swarm

Run the script from your terminal.

```bash
python sound_waves_parallel.py

```

*What happens next:* The script will analyze your audio, divide the timeline into 100-frame chunks, and unleash your CPU cores to draw the frames. You will see live progress updates in the terminal. The frames will be dumped into a new folder called `/render_frames`.

### 4. The Final Stitch

Python is only rendering the *visuals*. Once the script finishes, run this exact FFmpeg command in your terminal to instantly stitch the hundreds of images together and lay your original `.wav` audio track flawlessly over the top:

```bash
ffmpeg -framerate 30 -i render_frames/frame_%04d.png -i sound-waves.wav -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest final_broll.mp4

```

Boom. You now have a buttery-smooth, perfectly synced `.mp4` visualization ready for your video editor.

## Sandbox Mode

Open the script and tweak these variables to change the physics:

* `N_PARTICLES = 1500`: Increase this for a denser air cloud (Warning: heavier compute!).
* `wave_speed = 0.5`: Change how fast the longitudinal compression travels across the screen.
* `displacement[...] = audio[...] * 0.15`: Change the `0.15` multiplier to make the molecules react more or less violently to the volume of the audio.
