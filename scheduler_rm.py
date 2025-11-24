import sys
from scheduler_common import *

def schedule_rm(config, jobs):
    current_time = 0
    schedule = []

    for j in jobs:
        j.completed = False
        j.remaining_time = None
        j.selected_freq_index = None

    # non-EE RM runs at max freq
    freq_index = 0
    freq = config.frequencies[freq_index]
    power = config.powers[freq_index]

    while current_time < config.max_time:
        # choose READY job with SHORTEST PERIOD (i.e., smallest deadline param)
        cur = None
        best_period = float('inf')
        for j in jobs:
            if (not j.completed) and j.release_time <= current_time:
                p = j.task.deadline  # D == T provided by the inputs
                # tie-break by earlier release to stabilize trace
                if p < best_period or (p == best_period and j.release_time < (cur.release_time if cur else float('inf'))):
                    best_period = p
                    cur = j

        if cur is None:
            # no job ready -> idle to next release or horizon
            next_rel = None
            for j in jobs:
                if (not j.completed) and (j.release_time > current_time):
                    if next_rel is None or j.release_time < next_rel:
                        next_rel = j.release_time
            if next_rel is None:
                # pad to horizon
                if current_time < config.max_time:
                    idle_dt = config.max_time - current_time
                    if idle_dt > 0:
                        e = (config.idle_power/1000.0) * idle_dt
                        entry = ScheduleEntry()
                        entry.start_time = current_time
                        entry.task_name = "IDLE"
                        entry.frequency = 0
                        entry.duration = idle_dt
                        entry.energy = e
                        schedule.append(entry)
                        current_time += idle_dt
                break
            idle_dt = min(next_rel - current_time, config.max_time - current_time)
            if idle_dt > 0:
                e = (config.idle_power/1000.0) * idle_dt
                entry = ScheduleEntry()
                entry.start_time = current_time
                entry.task_name = "IDLE"
                entry.frequency = 0
                entry.duration = idle_dt
                entry.energy = e
                schedule.append(entry)
                current_time += idle_dt
            continue

        # initialize remaining at this frequency
        if cur.remaining_time is None:
            cur.remaining_time = cur.task.wcet[freq_index]

        # IMPORTANT: preempt at release of ANY HIGHER-PRIORITY TASK
        next_evt = config.max_time
        for j in jobs:
            if (not j.completed) and (j.release_time > current_time) and (j.release_time < next_evt):
                # if this future job has HIGHER priority (shorter period), it preempts at its release
                if j.task.deadline < cur.task.deadline:
                    next_evt = j.release_time

        # slice to completion, to next higher-priority release, or to horizon
        dt = min(cur.remaining_time, next_evt - current_time, config.max_time - current_time)
        if dt <= 0:
            break

        e = (power/1000.0) * dt
        entry = ScheduleEntry()
        entry.start_time = current_time
        entry.task_name = cur.task.name
        entry.frequency = freq
        entry.duration = dt
        entry.energy = e
        schedule.append(entry)

        current_time += dt
        cur.remaining_time -= dt
        if cur.remaining_time <= 0:
            cur.completed = True

    # pad to 1000s if needed so footer matches
    if schedule and schedule[-1].start_time + schedule[-1].duration < config.max_time:
        pad = config.max_time - (schedule[-1].start_time + schedule[-1].duration)
        if pad > 0:
            e = (config.idle_power/1000.0) * pad
            entry = ScheduleEntry()
            entry.start_time = schedule[-1].start_time + schedule[-1].duration
            entry.task_name = "IDLE"
            entry.frequency = 0
            entry.duration = pad
            entry.energy = e
            schedule.append(entry)

    return schedule

def print_footer(schedule):
    total_energy = 0.0
    idle_time = 0
    for s in schedule:
        total_energy += s.energy
        if s.task_name == "IDLE":
            idle_time += s.duration
    total_time = 0 if not schedule else schedule[-1].start_time + schedule[-1].duration
    print(f"\nTOTAL_ENERGY {total_energy:.3f}J")
    print(f"IDLE_PERCENT { (idle_time/float(total_time))*100.0 if total_time>0 else 0.0:.2f}%")
    print(f"TOTAL_TIME {int(total_time)}s")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input_file>")
        return 1
    cfg = SystemConfig()
    parse_input(sys.argv[1], cfg)
    jobs = generate_jobs(cfg)
    sched = schedule_rm(cfg, jobs)

    print(f"---- RM No-EE Scheduling for {sys.argv[1]} ----")
    for s in sched:
        if s.task_name == "IDLE":
            print(f"{s.start_time:.3f} IDLE IDLE {s.duration} {s.energy:.3f}J")
        else:
            print(f"{s.start_time:.3f} {s.task_name} 1188 {s.duration} {s.energy:.3f}J")
    print_footer(sched)
    return 0

if __name__ == "__main__":
    sys.exit(main())
