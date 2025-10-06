# pip install simpy
# coded by zainuddin@codemaster.my
# for educational purposes only

import simpy
from collections import deque

# ======================
# Round Robin Simulation
# ======================

class Process:
    def __init__(self, name, arrival, burst):
        self.name = name
        self.arrival = arrival
        self.burst = burst
        self.remaining = burst
        self.start_time = None
        self.completion_time = None
        self.response_time = None


# ======================
# Parameter (boleh ubah)
# ======================

env = simpy.Environment()
quantum = 3  # ubah nilai quantum di sini
procs = [
    Process("P1", 0, 10),
    Process("P2", 2, 6),
    Process("P3", 4, 8)
]


# ======================
# Round Robin Function
# ======================

def round_robin(env, processes, quantum):
    queue = deque()
    time_log = []
    processes = sorted(processes, key=lambda p: p.arrival)
    i = 0
    n = len(processes)

    while i < n or queue:
        while i < n and processes[i].arrival <= env.now:
            queue.append(processes[i])
            i += 1

        if not queue:
            next_arrival = processes[i].arrival
            yield env.timeout(next_arrival - env.now)
            continue

        current = queue.popleft()

        if current.start_time is None:
            current.start_time = env.now
            current.response_time = current.start_time - current.arrival

        exec_time = min(quantum, current.remaining)
        start = env.now
        end = env.now + exec_time
        print(f"{current.name} running from {start} to {end} (remaining {current.remaining - exec_time})")

        time_log.append((start, end, current.name))
        yield env.timeout(exec_time)

        current.remaining -= exec_time

        while i < n and processes[i].arrival <= env.now:
            queue.append(processes[i])
            i += 1

        if current.remaining > 0:
            queue.append(current)
        else:
            current.completion_time = env.now

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
timeline = env.process(round_robin(env, procs, quantum))
env.run()

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
