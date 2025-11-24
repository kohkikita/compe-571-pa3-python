import sys
from scheduler_common import *

def schedule_edf(config, jobs):
    current_time = 0
    schedule = []
    
    # Reset all jobs
    for job in jobs:
        job.completed = False
    
    while current_time < config.max_time:
        # Find job with earliest deadline
        earliest_job = None
        earliest_deadline = float('inf')
        
        for job in jobs:
            if (not job.completed and 
                job.release_time <= current_time and
                job.absolute_deadline < earliest_deadline):
                earliest_deadline = job.absolute_deadline
                earliest_job = job
        
        if earliest_job is None:
            # Find next release time
            next_release = config.max_time
            for job in jobs:
                if not job.completed and job.release_time > current_time:
                    if job.release_time < next_release:
                        next_release = job.release_time
            
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
            # Always use maximum frequency for EDF
            freq = config.frequencies[0]
            freq_index = 0
            
            wcet = earliest_job.task.wcet[freq_index]
            power = config.powers[freq_index]
            energy = (power / 1000.0) * wcet
            
            entry = ScheduleEntry()
            entry.start_time = current_time
            entry.task_name = earliest_job.task.name
            entry.frequency = freq
            entry.duration = wcet
            entry.energy = energy
            schedule.append(entry)
            
            current_time += wcet
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