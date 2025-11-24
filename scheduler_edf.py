import sys
from scheduler_common import *

def schedule_edf(config, jobs):
    current_time = 0
    schedule = []

    # reset job state
    for job in jobs:
        job.completed = False
        job.remaining_time = None
        job.selected_freq_index = None

    while current_time < config.max_time:
        # pick earliest-deadline ready job
        earliest_job = None
        earliest_deadline = float('inf')
        for j in jobs:
            if (not j.completed and
                j.release_time <= current_time and
                j.absolute_deadline < earliest_deadline):
                earliest_deadline = j.absolute_deadline
                earliest_job = j

        if earliest_job is None:
            # ---- patched idle branch: DO NOT pad to max_time ----
            next_release = None
            for j in jobs:
                if (not j.completed and
                    j.release_time > current_time and
                    j.release_time < config.max_time):
                    if next_release is None or j.release_time < next_release:
                        next_release = j.release_time

            # stop if nothing else before cutoff
            if next_release is None:
                break

            idle_time = next_release - current_time
            # cap to cutoff just in case
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
            # EDF: always max freq
            freq_index = 0
            freq = config.frequencies[freq_index]

            if earliest_job.remaining_time is None:
                earliest_job.remaining_time = earliest_job.task.wcet[freq_index]

            # preemption: next release with earlier deadline
            next_event_time = config.max_time
            for j in jobs:
                if (not j.completed and
                    j.release_time > current_time and
                    j.release_time < next_event_time and
                    j.absolute_deadline < earliest_job.absolute_deadline):
                    next_event_time = j.release_time

            execution_time = min(
                earliest_job.remaining_time,
                next_event_time - current_time,
                config.max_time - current_time
            )

            if execution_time > 0:
                power = config.powers[freq_index]
                energy = (power / 1000.0) * execution_time

                entry = ScheduleEntry()
                entry.start_time = current_time
                entry.task_name = earliest_job.task.name
                entry.frequency = freq
                entry.duration = execution_time
                entry.energy = energy
                schedule.append(entry)

                current_time += execution_time
                earliest_job.remaining_time -= execution_time

                if earliest_job.remaining_time <= 0:
                    earliest_job.completed = True
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
    schedule = schedule_edf(config, jobs)
    print_schedule(schedule, "EDF")
    return 0

if __name__ == "__main__":
    sys.exit(main())
