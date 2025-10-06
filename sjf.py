# pip install simpy
# coded by zainuddin@codemaster.my
# for educational purposes only

import simpy

# ======================
# SJF Simulation Setup
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

procs = [
    Process("P1", 0, 6),
    Process("P2", 2, 2),
    Process("P3", 3, 1),
    Process("P4", 5, 3)
]


# ======================
# SJF Non-Preemptive Function
# ======================

def sjf_non_preemptive(env, processes):
    time_log = []
    processes = sorted(processes, key=lambda p: p.arrival)
    ready = []
    i = 0
    n = len(processes)
    time = 0

    while i < n or ready:
        # Tambah proses ke ready queue bila sudah tiba
        while i < n and processes[i].arrival <= time:
            ready.append(processes[i])
            i += 1

        if not ready:
            # Tiada proses — CPU idle
            next_arrival = processes[i].arrival
            print(f"CPU idle from {time} to {next_arrival}")
            yield env.timeout(next_arrival - time)
            time = next_arrival
            continue

        # Pilih proses dengan burst time paling kecil
        ready.sort(key=lambda p: p.burst)
        current = ready.pop(0)

        # Kira masa mula & response
        current.start_time = time
        current.response_time = current.start_time - current.arrival

        start = time
        end = time + current.burst
        print(f"{current.name} running from {start} to {end}")

        time_log.append((start, end, current.name))
        yield env.timeout(current.burst)
        time = end
        current.completion_time = time

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
timeline = env.process(sjf_non_preemptive(env, procs))
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
