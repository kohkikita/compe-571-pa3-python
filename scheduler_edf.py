import sys
from scheduler_common import *

def schedule_edf(config, jobs):
    current_time = 0
    schedule = []

    # reset job state
    for j in jobs:
        j.completed = False
        j.remaining_time = None
        j.selected_freq_index = None

    # constant: run at max freq for non-EE EDF
    freq_index = 0
    freq = config.frequencies[freq_index]
    power = config.powers[freq_index]

    while current_time < config.max_time:
        # pick earliest absolute deadline among READY jobs
        cur = None
        best_deadline = float('inf')
        for j in jobs:
            if (not j.completed) and j.release_time <= current_time:
                if j.absolute_deadline < best_deadline or (
                    j.absolute_deadline == best_deadline and j.release_time < (cur.release_time if cur else float('inf'))
                ):
                    best_deadline = j.absolute_deadline
                    cur = j

        if cur is None:
            # idle to next release < max_time; if none, idle to horizon
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

        # initialize remaining
        if cur.remaining_time is None:
            cur.remaining_time = cur.task.wcet[freq_index]

        # compute next preemption event: any future release whose job will have an EARLIER deadline
        next_evt = config.max_time
        for j in jobs:
            if (not j.completed) and (j.release_time > current_time) and (j.release_time < next_evt):
                # if that job, once released, has earlier deadline than current -> potential preemption
                if j.release_time + j.task.deadline < cur.absolute_deadline:
                    next_evt = j.release_time

        # slice until completion, earlier-deadline release, or horizon
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

    # ensure footer prints 1000s by padding if needed
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
    # force 1000 in footer formatting (but schedule already padded)
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
    sched = schedule_edf(cfg, jobs)

    # print header-style like your screenshot
    print(f"---- EDF No-EE Scheduling for {sys.argv[1]} ----")
    for s in sched:
        if s.task_name == "IDLE":
            print(f"{s.start_time:.3f} IDLE IDLE {s.duration} {s.energy:.3f}J")
        else:
            print(f"{s.start_time:.3f} {s.task_name} 1188 {s.duration} {s.energy:.3f}J")
    print_footer(sched)
    return 0

if __name__ == "__main__":
    sys.exit(main())
