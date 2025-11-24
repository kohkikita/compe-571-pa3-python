import sys
from scheduler_common import *
from scheduler_rm import schedule_rm
from scheduler_eerm import schedule_eerm
from scheduler_edf import schedule_edf
from scheduler_eeedf import schedule_eeedf

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input_file>")
        print(f"Example: {sys.argv[0]} input1.txt")
        return 1
    
    config = SystemConfig()
    parse_input(sys.argv[1], config)
    
    # Generate jobs once
    jobs = generate_jobs(config)
    
    # Run all four algorithms
    print("\n" + "="*80)
    print("RUNNING ALL SCHEDULING ALGORITHMS")
    print("="*80)
    
    # RM
    schedule = schedule_rm(config, jobs)
    print_schedule(schedule, "RM")
    
    # EE RM
    schedule = schedule_eerm(config, jobs)
    print_schedule(schedule, "EE RM")
    
    # EDF
    schedule = schedule_edf(config, jobs)
    print_schedule(schedule, "EDF")
    
    # EE EDF
    schedule = schedule_eeedf(config, jobs)
    print_schedule(schedule, "EE EDF")
    
    print("="*80)
    print("ALL SCHEDULES COMPLETED")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())