# pip install simpy
# coded by zainuddin@codemaster.my
# for educational purposes only

import simpy

# ======================
# FCFS Simulation Setup
# ======================

class Process:
    def __init__(self, name, arrival, burst):
        self.name = name
        self.arrival = arrival
        self.burst = burst
        self.start_time = None
        self.completion_time = None
        self.response_time = None


# ======================
# Parameter (boleh ubah)
# ======================

env = simpy.Environment()

# Senarai proses: (Nama, Masa Tiba, Burst Time)
procs = [
    Process("P1", 0, 5),
    Process("P2", 2, 3),
    Process("P3", 4, 8),
    Process("P4", 10, 6)
]


# ======================
# FCFS Function
# ======================

def fcfs(env, processes):
    # Sort proses ikut masa tiba
    processes = sorted(processes, key=lambda p: p.arrival)
    time_log = []

    time = 0
    for p in processes:
        # Jika CPU idle sebelum proses tiba
        if time < p.arrival:
            print(f"CPU idle from {time} to {p.arrival}")
            yield env.timeout(p.arrival - time)
            time = p.arrival

        p.start_time = time
        p.response_time = p.start_time - p.arrival

        start = time
        end = time + p.burst
        print(f"{p.name} running from {start} to {end}")

        time_log.append((start, end, p.name))

        yield env.timeout(p.burst)
        time = end
        p.completion_time = time

    return time_log


def gantt_chart(timeline):
    print("\n=== Gantt Chart ===")
    for (st, en, name) in timeline:
        print(f"{name}: {st} → {en}")


# ======================
# Run Simulation
# ======================

# Paparkan semua input proses sebelum sebarang output simulasi
print("=== Input Processes ===")
for p in procs:
    print(f"{p.name} | Arrival={p.arrival}, Burst={p.burst}")

print()
timeline = env.process(fcfs(env, procs))
env.run()

# ======================
# Compute Metrics
# ======================

print("\n=== Metrics ===")
total_tat = total_wt = total_rt = 0
for p in procs:
    tat = p.completion_time - p.arrival
    wt = tat - p.burst
    rt = p.response_time
    total_tat += tat
    total_wt += wt
    total_rt += rt
    print(f"{p.name} | Arrival={p.arrival}, Burst={p.burst}, "
          f"Start={p.start_time}, Completion={p.completion_time}, "
          f"TAT={tat}, WT={wt}, RT={rt}")

n = len(procs)
print(f"\nAverage Turnaround Time: {total_tat/n:.2f}")
print(f"Average Waiting Time: {total_wt/n:.2f}")
print(f"Average Response Time: {total_rt/n:.2f}")

gantt_chart(timeline.value)
