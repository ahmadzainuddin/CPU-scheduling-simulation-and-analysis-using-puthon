# pip install simpy
# coded by zainuddin@codemaster.my
# for educational purposes only

import simpy
from typing import List, Tuple, Optional

# ======================
# Priority Non-Preemptive Setup
# ======================

class Process:
    def __init__(self, name: str, arrival: int, burst: int, priority: int):
        self.name = name
        self.arrival = arrival
        self.burst = burst
        self.priority = priority  # lower = higher priority
        self.start_time: Optional[int] = None
        self.completion_time: Optional[int] = None
        self.response_time: Optional[int] = None

    def __repr__(self):
        return f"{self.name}(A={self.arrival},B={self.burst},P={self.priority})"


# ======================
# Parameter (boleh ubah)
# ======================
env = simpy.Environment()

# Senarai proses: (Nama, Arrival, Burst, Priority)
# *nombor kecil = keutamaan tinggi*
procs: List[Process] = [
    Process("P1", 0, 5, 2),
    Process("P2", 1, 3, 1),
    Process("P3", 2, 8, 3),
    Process("P4", 3, 6, 2),
]

# Context switch delay (unit masa) jika perlu
CTX = 0


# ======================
# Priority Non-Preemptive Function
# ======================
def priority_non_preemptive(env: simpy.Environment, processes: List[Process], ctx_overhead: int = 0):
    """
    Priority scheduling (non-preemptive)
    lower number = higher priority
    """
    timeline: List[Tuple[int, int, str]] = []
    processes = sorted(processes, key=lambda p: (p.arrival, p.priority, p.name))
    ready: List[Process] = []
    i = 0
    n = len(processes)
    time = 0

    while i < n or ready:
        # Masukkan proses yang sudah tiba
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

        # Pilih proses dengan priority tertinggi (nombor kecil)
        ready.sort(key=lambda p: (p.priority, p.arrival, p.name))
        current = ready.pop(0)

        # Mula proses
        current.start_time = time
        current.response_time = current.start_time - current.arrival

        start = time
        end = time + current.burst
        print(f"{current.name} running from {start} to {end} (Priority {current.priority})")

        timeline.append((start, end, current.name))
        yield env.timeout(current.burst)
        time = end
        current.completion_time = time

        # Context switch delay jika ada
        if ctx_overhead > 0 and (ready or i < n):
            timeline.append((time, time + ctx_overhead, "CTX"))
            yield env.timeout(ctx_overhead)
            time += ctx_overhead

    return timeline


def gantt_chart(timeline: List[Tuple[int, int, str]]):
    print("\n=== Gantt Chart ===")
    for (st, en, name) in timeline:
        print(f"{name}: {st} → {en}")


# ======================
# Run Simulation
# ======================

# Paparkan semua input proses sebelum sebarang output simulasi
print("=== Input Processes ===")
for p in procs:
    print(f"{p.name} | Arrival={p.arrival}, Burst={p.burst}, Priority={p.priority}")

print()
timeline = env.process(priority_non_preemptive(env, procs, ctx_overhead=CTX))
env.run()

# ======================
# Compute Metrics
# ======================
print("\n=== Metrics ===")
tot_tat = tot_wt = tot_rt = 0.0
for p in procs:
    tat = p.completion_time - p.arrival
    wt = tat - p.burst
    rt = p.response_time
    tot_tat += tat
    tot_wt += wt
    tot_rt += rt
    print(f"{p.name} | A={p.arrival}, B={p.burst}, P={p.priority}, "
          f"Start={p.start_time}, Complete={p.completion_time}, "
          f"TAT={tat}, WT={wt}, RT={rt}")

n = len(procs)
print(f"\nAverage Turnaround Time: {tot_tat/n:.2f}")
print(f"Average Waiting Time:    {tot_wt/n:.2f}")
print(f"Average Response Time:   {tot_rt/n:.2f}")

gantt_chart(timeline.value)
