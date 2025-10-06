# pip install simpy
# coded by zainuddin@codemaster.my
# for educational purposes only

import simpy
from typing import List, Tuple, Optional

# ======================
# SRTF Simulation Setup
# ======================

class Process:
    def __init__(self, name: str, arrival: int, burst: int):
        self.name = name
        self.arrival = arrival
        self.burst = burst
        self.remaining = burst
        self.start_time: Optional[int] = None
        self.completion_time: Optional[int] = None
        self.response_time: Optional[int] = None

    def __repr__(self):
        return f"{self.name}(A={self.arrival}, B={self.burst}, R={self.remaining})"


# ======================
# Parameter (boleh ubah)
# ======================
env = simpy.Environment()

# Senarai proses: (Nama, Arrival, Burst)
procs: List[Process] = [
    Process("P1", 0, 7),
    Process("P2", 2, 4),
    Process("P3", 4, 1),
    #Process("P4", 5, 3),
]

# context switch overhead (unit masa), tetapkan 0 jika tak mahu
CTX = 0


# ======================
# SRTF Function (Preemptive)
# ======================
def srtf(env: simpy.Environment, processes: List[Process], ctx_overhead: int = 0):
    """
    Jalankan SRTF secara 'tick-by-tick' (1 unit masa setiap kitaran).
    Preempt bila terdapat proses dengan remaining lebih kecil daripada proses semasa.
    Tie-break: remaining, arrival, name.
    """
    time_log: List[Tuple[int, int, str]] = []   # (start, end, name)
    processes = sorted(processes, key=lambda p: (p.arrival, p.name))
    ready: List[Process] = []
    i = 0
    n = len(processes)

    current: Optional[Process] = None
    slice_start: Optional[int] = None

    def pick_shortest() -> Optional[Process]:
        if not ready:
            return None
        ready.sort(key=lambda p: (p.remaining, p.arrival, p.name))
        return ready.pop(0)

    def close_slice(until_time: int, pid: str):
        # Tutup segmen Gantt untuk proses semasa
        if slice_start is not None and until_time > slice_start:
            time_log.append((slice_start, until_time, pid))

    while i < n or ready or current:
        # Masukkan proses yang sudah tiba pada env.now
        while i < n and processes[i].arrival <= env.now:
            p = processes[i]
            ready.append(p)
            i += 1

            # Preempt check (jika ada current dan pendatang baru lebih pendek)
            if current and p.remaining < current.remaining:
                # Tutup segmen semasa
                close_slice(env.now, current.name)
                # Context switch (jika ada)
                if ctx_overhead > 0:
                    time_log.append((env.now, env.now + ctx_overhead, "CTX"))
                    yield env.timeout(ctx_overhead)
                # Letak balik current dalam ready
                ready.append(current)
                current = None
                slice_start = None

        # Jika tiada proses sedia & ada proses akan datang → IDLE lompat masa
        if not current and not ready and i < n:
            next_arrival = processes[i].arrival
            # Jadikan segmen IDLE (pilihan: paparkan atau tidak)
            if env.now < next_arrival:
                time_log.append((env.now, next_arrival, "IDLE"))
                yield env.timeout(next_arrival - env.now)
            continue

        # Ambil proses jika tiada current
        if not current:
            current = pick_shortest()
            if current is None and i >= n:
                break  # tiada lagi proses
            if current:
                if current.start_time is None:
                    current.start_time = env.now
                    current.response_time = current.start_time - current.arrival
                slice_start = env.now

        # Jalankan current selama 1 unit masa (tick)
        if current:
            yield env.timeout(1)
            current.remaining -= 1

            # Jika siap, tutup segmen dan rekod completion
            if current.remaining == 0:
                close_slice(env.now, current.name)
                current.completion_time = env.now
                current = None
                slice_start = None
                # Optional: context switch sebelum proses seterusnya
                if ctx_overhead > 0 and (ready or i < n):
                    time_log.append((env.now, env.now + ctx_overhead, "CTX"))
                    yield env.timeout(ctx_overhead)
            else:
                # Sebelum next tick, masukkan proses yang tiba tepat pada masa ini (untuk peluang preempt)
                while i < n and processes[i].arrival <= env.now:
                    ready.append(processes[i])
                    i += 1
                    # Preempt jika perlu (ikut remaining)
                    if current and ready:
                        ready.sort(key=lambda p: (p.remaining, p.arrival, p.name))
                        candidate = ready[0]
                        if candidate.remaining < current.remaining:
                            # tutup segmen semasa
                            close_slice(env.now, current.name)
                            if ctx_overhead > 0:
                                time_log.append((env.now, env.now + ctx_overhead, "CTX"))
                                yield env.timeout(ctx_overhead)
                            # gantikan current
                            ready.append(current)
                            current = ready.pop(0)
                            if current.start_time is None:
                                current.start_time = env.now
                                current.response_time = current.start_time - current.arrival
                            slice_start = env.now

    return time_log


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
    print(f"{p.name} | Arrival={p.arrival}, Burst={p.burst}")

print()
timeline = env.process(srtf(env, procs, ctx_overhead=CTX))
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
    print(f"{p.name} | A={p.arrival}, B={p.burst}, "
          f"Start={p.start_time}, Complete={p.completion_time}, "
          f"TAT={tat}, WT={wt}, RT={rt}")

n = len(procs)
print(f"\nAverage Turnaround Time: {tot_tat/n:.2f}")
print(f"Average Waiting Time:    {tot_wt/n:.2f}")
print(f"Average Response Time:   {tot_rt/n:.2f}")

gantt_chart(timeline.value)
