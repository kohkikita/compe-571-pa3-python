import sys
from scheduler_common import *

def schedule_edf(config, jobs):
    current_time = 0
    schedule = []

    # reset job state
    for job in jobs:
        job.completed = False
        job.remaining_time = None

    while current_time < config.max_time:
        # Find ALL ready jobs (not just one)
        ready_jobs = [j for j in jobs if not j.completed and j.release_time <= current_time]
        
        if not ready_jobs:
            # Find next job release
            next_release = None
            for j in jobs:
                if not j.completed and j.release_time > current_time and j.release_time < config.max_time:
                    if next_release is None or j.release_time < next_release:
                        next_release = j.release_time
            
            if next_release is None:
                break
            
            # Idle until next release
            idle_time = next_release - current_time
            entry = ScheduleEntry()
            entry.start_time = current_time
            entry.task_name = "IDLE"
            entry.frequency = 0
            entry.duration = idle_time
            entry.energy = (config.idle_power / 1000.0) * idle_time
            schedule.append(entry)
            current_time += idle_time
        else:
            # EDF: Pick job with earliest deadline among ready jobs
            earliest_job = min(ready_jobs, key=lambda j: j.absolute_deadline)
            
            # Always use max frequency for EDF
            freq_index = 0
            freq = config.frequencies[freq_index]
            
            # Initialize remaining time if first time scheduled
            if earliest_job.remaining_time is None:
                earliest_job.remaining_time = earliest_job.task.wcet[freq_index]
            
            # Find next preemption point: when a job with EARLIER deadline arrives
            next_event = config.max_time
            for j in jobs:
                if (not j.completed and 
                    j.release_time > current_time and 
                    j.release_time < next_event and
                    j.absolute_deadline < earliest_job.absolute_deadline):
                    next_event = j.release_time
            
            # Execute for minimum of: remaining time, time until preemption, time until max_time
            execution_time = min(
                earliest_job.remaining_time,
                next_event - current_time,
                config.max_time - current_time
            )
            
            if execution_time <= 0:
                break
            
            # Create schedule entry
            power = config.powers[freq_index]
            energy = (power / 1000.0) * execution_time
            
            entry = ScheduleEntry()
            entry.start_time = current_time
            entry.task_name = earliest_job.task.name
            entry.frequency = freq
            entry.duration = execution_time
            entry.energy = energy
            schedule.append(entry)
            
            # Update state
            current_time += execution_time
            earliest_job.remaining_time -= execution_time
            
            if earliest_job.remaining_time <= 0:
                earliest_job.completed = True

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