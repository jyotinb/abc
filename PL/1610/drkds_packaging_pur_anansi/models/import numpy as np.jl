import numpy as np
import matplotlib.pyplot as plt

# --- Parameters ---
arch_height = 5.0
arch_width = 20

# Control start fractions for vertical positions
start_fracs = [0.75]   # multiple lines possible
end_frac    = 0.72     # where reference straight line meets outer arch

# --- Geometry ---
mid = arch_width / 2.0

# Outer arch (parabola)
x_outer = np.linspace(0, arch_width, 600)
y_outer = arch_height * (1 - ((x_outer - mid) / mid) ** 2)

# Base line
x_base = [0, arch_width]
y_base = [0, 0]

# Vertical center line
x_vertical = [mid, mid]
y_vertical = [0, arch_height]

# --- Reference slope from first line ---
x1_start = mid
y1_start = arch_height * 0.55
x1_end   = arch_width * end_frac
y1_end   = arch_height * (1 - ((x1_end - mid) / mid) ** 2)

# Slope
m = (y1_end - y1_start) / (x1_end - x1_start)

# Function to get line end given start
def line_end(x_start, y_start, slope):
    x_candidates = np.linspace(mid, arch_width, 500)
    y_candidates = slope * (x_candidates - x_start) + y_start
    y_outer_candidates = arch_height * (1 - ((x_candidates - mid) / mid) ** 2)
    idx = np.argmin(np.abs(y_candidates - y_outer_candidates))
    return x_candidates[idx], y_candidates[idx]

# Collect lines + curves
lines = []
curves = []
for frac in start_fracs:
    # Start point
    x_s = mid
    y_s = arch_height * frac
    # End point (straight line)
    x_e, y_e = line_end(x_s, y_s, m)
    lines.append(([x_s, x_e], [y_s, y_e]))
    
    # --- Sub-arch: must end at same outer arch point (x_e, y_e) ---
    x_curve = np.linspace(x_s, x_e, 200)
    span = (x_e - x_s) / 2
    center = (x_s + x_e) / 2
    # Shape: rising parabola normalized to start=y_s and end=y_e
    base_curve = (1 - ((x_curve - center) / span) ** 2)
    y_curve = (base_curve - base_curve.min()) / (base_curve.max() - base_curve.min())  # normalize 0..1
    y_curve = y_s + (y_e - y_s) * y_curve 
    curves.append((x_curve, y_curve))

# --- Plot ---
plt.figure(figsize=(11,6))

# Outer arch
plt.plot(x_outer, y_outer, 'k-', linewidth=5)

# Base line
plt.plot(x_base, y_base, 'k-', linewidth=5)

# Vertical center
plt.plot(x_vertical, y_vertical, 'k-', linewidth=5)

# Inner straight lines
for (xs, ys) in lines:
    plt.plot(xs, ys, 'k-', linewidth=5)

# Inner curved arches (end exactly on outer arch)
for (xs, ys) in curves:
    plt.plot(xs, ys, 'k-', linewidth=5)

plt.title("Khachi Vadi Arch — Sub-Arch Ending on Main Arch", fontsize=16)
plt.axis("equal")
plt.axis("off")
plt.show()
