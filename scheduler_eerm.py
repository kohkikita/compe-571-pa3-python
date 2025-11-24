import sys
from scheduler_common import *

def select_frequency_ee(config, job, current_time):
    deadline = job.absolute_deadline
    time_available = deadline - current_time
    
    best_freq = config.frequencies[0]
    best_energy = float('inf')
    
    # Try each frequency from lowest to highest
    for i in range(NUM_FREQUENCIES - 1, -1, -1):
        freq = config.frequencies[i]
        wcet = job.task.wcet[i]
        
        # Check if this frequency meets the deadline
        if wcet <= time_available:
            power = config.powers[i]
            energy = (power / 1000.0) * wcet
            
            # Select frequency with minimum energy
            if energy < best_energy:
                best_energy = energy
                best_freq = freq
    
    return best_freq

def schedule_eerm(config, jobs):
    current_time = 0
    schedule = []
    
    # Reset all jobs
    for job in jobs:
        job.completed = False
        job.remaining_time = None
        job.selected_freq_index = None
    
    while current_time < config.max_time:
        # Find job with highest priority (shortest period) that's ready
        highest_priority_job = None
        shortest_period = float('inf')
        
        for job in jobs:
            if not job.completed and job.release_time <= current_time:
                period = job.task.deadline
                if period < shortest_period:
                    shortest_period = period
                    highest_priority_job = job
        
        if highest_priority_job is None:
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
            # Select frequency if not already selected for this job
            if highest_priority_job.selected_freq_index is None:
                freq = select_frequency_ee(config, highest_priority_job, current_time)
                # Find frequency index
                freq_index = 0
                for i in range(NUM_FREQUENCIES):
                    if config.frequencies[i] == freq:
                        freq_index = i
                        break
                highest_priority_job.selected_freq_index = freq_index
                highest_priority_job.remaining_time = highest_priority_job.task.wcet[freq_index]
            
            freq_index = highest_priority_job.selected_freq_index
            freq = config.frequencies[freq_index]
            
            # Check for preemption: find next event (release or deadline)
            next_event_time = config.max_time
            
            # Check for new job releases that could preempt
            for job in jobs:
                if (not job.completed and 
                    job.release_time > current_time and 
                    job.release_time < next_event_time):
                    # Check if this job has higher priority (shorter period)
                    if job.task.deadline < highest_priority_job.task.deadline:
                        next_event_time = job.release_time
            
            # Execute until completion, preemption, or max_time
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
                
                # Mark as completed if finished
                if highest_priority_job.remaining_time <= 0:
                    highest_priority_job.completed = True
    
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