import sys
from scheduler_common import *

def schedule_edf(config, jobs):
    current_time = 0
    schedule = []
    
    # Reset all jobs
    for job in jobs:
        job.completed = False
        job.remaining_time = None
        job.selected_freq_index = None
    
    while current_time < config.max_time:
        # Find job with earliest deadline that's ready
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
            
            # Initialize remaining time if this is the first execution of this job
            if earliest_job.remaining_time is None:
                earliest_job.remaining_time = earliest_job.task.wcet[freq_index]
            
            # Check for preemption: find next event (release that could preempt)
            next_event_time = config.max_time
            
            # Check for new job releases that could preempt (earlier deadline)
            for job in jobs:
                if (not job.completed and 
                    job.release_time > current_time and 
                    job.release_time < next_event_time):
                    # Check if this job has earlier deadline
                    if job.absolute_deadline < earliest_job.absolute_deadline:
                        next_event_time = job.release_time
            
            # Execute until completion, preemption, or max_time
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
                
                # Mark as completed if finished
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