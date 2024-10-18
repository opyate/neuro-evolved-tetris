import glob

import matplotlib.pyplot as plt
import numpy as np

# Get the list of log files from the "logs" directory
log_files = glob.glob("logs/*.log")

# Initialize variables for fitness values from the first log
min_fitness = []
mean_fitness = []
max_fitness = []

# Initialize variables for loop counts from all logs
loop_counts = {}

# Read the first log for fitness values
with open(log_files[0], "r") as f:
    for line in f:
        if "max_fitness" in line:
            parts = line.split(",")
            max_fitness.append(float(parts[0].split(":")[3].strip()))
            min_fitness.append(float(parts[1].split(":")[1].strip()))
            mean_fitness.append(float(parts[2].split(":")[1].strip()))

# Read all logs for loop counts
for log_file in log_files:
    with open(log_file, "r") as f:
        for line in f:
            if "loop_count" in line:
                loop_count = int(line.split(",")[0].split("=")[1])
                loop_counts.setdefault(log_file, []).append(loop_count)

# Calculate statistics for loop counts
max_loop_counts = []
min_loop_counts = []
mean_loop_counts = []

for i in range(len(loop_counts[log_files[0]])):
    _loop_counts = []

    for k, v in loop_counts.items():
        # check if v is long enough
        if len(v) > i:
            _loop_counts.append(v[i])
        else:
            _loop_counts.append(v[i - 1])

    max_loop_counts.append(max(_loop_counts))
    min_loop_counts.append(min(_loop_counts))
    mean_loop_counts.append(sum(_loop_counts) / len(_loop_counts))

# Plot the values
plt.figure(figsize=(19.2, 10.8), dpi=100)

# Plot fitness values

max_fitness_moving_avg = np.convolve(max_fitness, np.ones(20) / 20, mode="valid")
# plt.plot(max_fitness, label="Max Fitness", color="tab:blue")
plt.plot(
    range(len(max_fitness_moving_avg)),
    max_fitness_moving_avg,
    label="Max Fitness",
    color="tab:blue",
)

mean_fitness_moving_avg = np.convolve(mean_fitness, np.ones(20) / 20, mode="valid")
# plt.plot(mean_fitness, label="Mean Fitness", color="tab:cyan")
plt.plot(
    range(len(mean_fitness_moving_avg)),
    mean_fitness_moving_avg,
    label="Mean Fitness",
    color="tab:cyan",
)

min_fitness_moving_avg = np.convolve(min_fitness, np.ones(20) / 20, mode="valid")
# plt.plot(min_fitness, label="Min Fitness", color="tab:purple")
plt.plot(
    range(len(min_fitness_moving_avg)),
    min_fitness_moving_avg,
    label="Min Fitness",
    color="tab:purple",
)

# Plot loop counts
max_loop_counts_moving_avg = np.convolve(
    max_loop_counts, np.ones(20) / 20, mode="valid"
)
# plt.plot(max_loop_counts, label="Max Loop Count", color="tab:pink")
plt.plot(
    range(len(max_loop_counts_moving_avg)),
    max_loop_counts_moving_avg,
    label="Max Loop Count",
    color="tab:pink",
)

# Add legend and labels
plt.legend()
plt.title("Fitness and Loop Count Statistics")
plt.xlabel("Iterations")
plt.ylabel("Values")

# Save and show the plot
plt.savefig("plot.png")
plt.show()
