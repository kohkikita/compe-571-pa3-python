import sys
from scheduler_common import *

def select_frequency_ee(config, job, current_time):
    deadline = job.absolute_deadline
    time_available = deadline - current_time
    best_freq = config.frequencies[0]
    best_energy = float('inf')
    for i in range(NUM_FREQUENCIES - 1, -1, -1):
        wcet = job.task.wcet[i]
        if wcet <= time_available:
            power = config.powers[i]
            energy = (power / 1000.0) * wcet
            if energy < best_energy:
                best_energy = energy
                best_freq = config.frequencies[i]
    return best_freq

def schedule_eerm(config, jobs):
    current_time = 0
    schedule = []

    # reset job state
    for job in jobs:
        job.completed = False
        job.remaining_time = None
        job.selected_freq_index = None

    while current_time < config.max_time:
        # highest priority = shortest period (deadline)
        highest_priority_job = None
        shortest_period = float('inf')
        for j in jobs:
            if (not j.completed and j.release_time <= current_time):
                period = j.task.deadline
                if period < shortest_period:
                    shortest_period = period
                    highest_priority_job = j

        if highest_priority_job is None:
            # ---- patched idle branch: DO NOT pad to max_time ----
            next_release = None
            for j in jobs:
                if (not j.completed and
                    j.release_time > current_time and
                    j.release_time < config.max_time):
                    if next_release is None or j.release_time < next_release:
                        next_release = j.release_time

            if next_release is None:
                break

            idle_time = next_release - current_time
            if current_time + idle_time > config.max_time:
                idle_time = config.max_time - current_time

            if idle_time > 0:
                entry = ScheduleEntry()
                entry.start_time = current_time
                entry.task_name = "IDLE"
                entry.frequency = 0
                entry.duration = idle_time
                entry.energy = (config.idle_power / 1000.0) * idle_time
                schedule.append(entry)
                current_time += idle_time
            else:
                break
        else:
            # choose EE freq (cache per job)
            if highest_priority_job.selected_freq_index is None:
                chosen_freq = select_frequency_ee(config, highest_priority_job, current_time)
                idx = 0
                for i in range(NUM_FREQUENCIES):
                    if config.frequencies[i] == chosen_freq:
                        idx = i
                        break
                highest_priority_job.selected_freq_index = idx
                highest_priority_job.remaining_time = highest_priority_job.task.wcet[idx]

            freq_index = highest_priority_job.selected_freq_index
            freq = config.frequencies[freq_index]

            # preemption: any shorter period release
            next_event_time = config.max_time
            for j in jobs:
                if (not j.completed and
                    j.release_time > current_time and
                    j.release_time < next_event_time and
                    j.task.deadline < highest_priority_job.task.deadline):
                    next_event_time = j.release_time

            execution_time = min(
                highest_priority_job.remaining_time,
                next_event_time - current_time,
                config.max_time - current_time
            )

            if execution_time > 0:
                power = config.powers[freq_index]
                energy = (power / 1000.0) * execution_time

                entry = ScheduleEntry()
                entry.start_time = current_time
                entry.task_name = highest_priority_job.task.name
                entry.frequency = freq
                entry.duration = execution_time
                entry.energy = energy
                schedule.append(entry)

                current_time += execution_time
                highest_priority_job.remaining_time -= execution_time

                if highest_priority_job.remaining_time <= 0:
                    highest_priority_job.completed = True
            else:
                break

    return schedule

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input_file>")
        return 1
    config = SystemConfig()
    parse_input(sys.argv[1], config)
    jobs = generate_jobs(config)
    schedule = schedule_eerm(config, jobs)
    print_schedule(schedule, "EE RM")
    return 0

if __name__ == "__main__":
    sys.exit(main())
