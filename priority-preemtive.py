# pip install simpy
# coded by zainuddin@codemaster.my
# for educational purposes only

import simpy
from typing import List, Tuple, Optional

# ======================
# Priority Preemptive Setup
# ======================

class Process:
    def __init__(self, name: str, arrival: int, burst: int, priority: int):
        self.name = name
        self.arrival = arrival
        self.burst = burst
        self.priority = priority  # lower = higher priority
        self.remaining = burst
        self.start_time: Optional[int] = None
        self.completion_time: Optional[int] = None
        self.response_time: Optional[int] = None
        self.last_enqueued_at: Optional[int] = None  # for simple aging

    def __repr__(self):
        return f"{self.name}(A={self.arrival},B={self.burst},P={self.priority},R={self.remaining})"


# ======================
# Parameter (boleh ubah)
# ======================
env = simpy.Environment()

# Senarai proses: (Nama, Arrival, Burst, Priority)
# *lower number = higher priority*
procs: List[Process] = [
    Process("P1", 0, 6, 3),
    Process("P2", 1, 4, 2),
    Process("P3", 2, 5, 1),
    # Process("P4", 6, 2, 1),
]

# Context switch overhead (unit masa). Tetapkan 0 jika tak perlu.
CTX = 0

# Pilihan aging untuk kurangkan starvation (False untuk matikan).
AGING = False
AGING_INTERVAL = 5      # setiap 5 unit masa menunggu
AGING_STEP = 1          # kurangkan nilai priority sebanyak 1 (menaikkan priority)


# ======================
# Priority Preemptive Function
# ======================
def priority_preemptive(env: simpy.Environment, processes: List[Process],
                        ctx_overhead: int = 0, aging: bool = False,
                        aging_interval: int = 5, aging_step: int = 1):
    """
    Priority (preemptive): lower number = higher priority.
    Preempt jika ada proses ready dengan priority < priority proses semasa.
    Tie-break: priority, arrival, name.
    Aging (optional): setiap 'aging_interval' masa menunggu, kurangkan nilai priority (min 1).
    """
    timeline: List[Tuple[int, int, str]] = []   # (start, end, name/CTX/IDLE)
    processes = sorted(processes, key=lambda p: (p.arrival, p.name))
    ready: List[Process] = []
    i = 0
    n = len(processes)

    current: Optional[Process] = None
    slice_start: Optional[int] = None

    def enqueue(p: Process, now: int):
        p.last_enqueued_at = now
        ready.append(p)

    def apply_aging(now: int):
        if not aging:
            return
        for p in ready:
            waited = now - (p.last_enqueued_at or now)
            # Naikkan keutamaan bila cukup tempoh menunggu
            if waited >= aging_interval and p.priority > 1:
                steps = waited // aging_interval
                new_prio = max(1, p.priority - steps * aging_step)
                if new_prio != p.priority:
                    p.priority = new_prio
                    p.last_enqueued_at = now  # reset anchor

    def pick_highest() -> Optional[Process]:
        if not ready:
            return None
        # priority asc (kecil -> tinggi), then arrival asc, then name asc
        ready.sort(key=lambda p: (p.priority, p.arrival, p.name))
        return ready.pop(0)

    def is_higher(a: Process, b: Process) -> bool:
        """Return True if a has higher priority than b."""
        if a.priority < b.priority:
            return True
        if a.priority == b.priority:
            if a.arrival < b.arrival:
                return True
            if a.arrival == b.arrival and a.name < b.name:
                return True
        return False

    def close_slice(until_time: int, pid: str):
        if slice_start is not None and until_time > slice_start:
            timeline.append((slice_start, until_time, pid))

    while i < n or ready or current:
        # Masukkan proses yang sudah tiba pada masa sekarang
        while i < n and processes[i].arrival <= env.now:
            enqueue(processes[i], env.now)
            i += 1

        # Aging on ready queue
        apply_aging(env.now)

        # Preempt check bila ada current dan ada calon lebih tinggi
        if current and ready:
            ready.sort(key=lambda p: (p.priority, p.arrival, p.name))
            cand = ready[0]
            if is_higher(cand, current):
                # tutup segmen semasa
                close_slice(env.now, current.name)
                # context switch jika ada
                if ctx_overhead > 0:
                    timeline.append((env.now, env.now + ctx_overhead, "CTX"))
                    yield env.timeout(ctx_overhead)
                # letak current kembali ke ready
                enqueue(current, env.now)
                current = None
                slice_start = None

        # Jika tiada current dan ready kosong tapi ada proses akan datang → idle
        if not current and not ready and i < n:
            next_arrival = processes[i].arrival
            if env.now < next_arrival:
                timeline.append((env.now, next_arrival, "IDLE"))
                yield env.timeout(next_arrival - env.now)
            continue

        # Ambil proses jika tiada current
        if not current:
            current = pick_highest()
            if current is None and i >= n:
                break
            if current:
                if current.start_time is None:
                    current.start_time = env.now
                    current.response_time = current.start_time - current.arrival
                slice_start = env.now

        # Jalan 1 unit masa
        if current:
            yield env.timeout(1)
            current.remaining -= 1

            if current.remaining == 0:
                # tamatkan proses semasa
                close_slice(env.now, current.name)
                current.completion_time = env.now
                current = None
                slice_start = None
                # context switch selepas tamat proses (jika masih ada kerja)
                if ctx_overhead > 0 and (ready or i < n):
                    timeline.append((env.now, env.now + ctx_overhead, "CTX"))
                    yield env.timeout(ctx_overhead)
            else:
                # semak arrival baru (untuk peluang preempt segera)
                while i < n and processes[i].arrival <= env.now:
                    enqueue(processes[i], env.now)
                    i += 1
                apply_aging(env.now)
                if ready:
                    ready.sort(key=lambda p: (p.priority, p.arrival, p.name))
                    cand = ready[0]
                    if is_higher(cand, current):
                        close_slice(env.now, current.name)
                        if ctx_overhead > 0:
                            timeline.append((env.now, env.now + ctx_overhead, "CTX"))
                            yield env.timeout(ctx_overhead)
                        enqueue(current, env.now)
                        current = ready.pop(0)
                        if current.start_time is None:
                            current.start_time = env.now
                            current.response_time = current.start_time - current.arrival
                        slice_start = env.now

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
timeline = env.process(
    priority_preemptive(env, procs, ctx_overhead=CTX, aging=AGING,
                        aging_interval=AGING_INTERVAL, aging_step=AGING_STEP)
)
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
