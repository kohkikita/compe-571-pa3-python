MAX_TASKS = 10
MAX_JOBS = 10000
NUM_FREQUENCIES = 4

class Task:
    def __init__(self):
        self.name = ""
        self.deadline = 0
        self.wcet = [0] * NUM_FREQUENCIES

class Job:
    def __init__(self):
        self.task = None
        self.release_time = 0
        self.absolute_deadline = 0
        self.job_number = 0
        self.completed = False

class ScheduleEntry:
    def __init__(self):
        self.start_time = 0
        self.task_name = ""
        self.frequency = 0
        self.duration = 0
        self.energy = 0.0

class SystemConfig:
    def __init__(self):
        self.tasks = [Task() for _ in range(MAX_TASKS)]
        self.num_tasks = 0
        self.max_time = 0
        self.frequencies = [1188, 918, 648, 384]
        self.powers = [0] * NUM_FREQUENCIES
        self.idle_power = 0

def parse_input(filename, config):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            line_idx = 0
            
            num_tasks, max_time = map(int, lines[line_idx].split())
            config.num_tasks = num_tasks
            config.max_time = max_time
            line_idx += 1
            
            powers = list(map(int, lines[line_idx].split()))
            for i in range(NUM_FREQUENCIES):
                config.powers[i] = powers[i]
            line_idx += 1
            
            config.idle_power = int(lines[line_idx].strip())
            line_idx += 1
            
            for i in range(config.num_tasks):
                parts = lines[line_idx].split()
                config.tasks[i].name = parts[0]
                config.tasks[i].deadline = int(parts[1])
                for j in range(NUM_FREQUENCIES):
                    config.tasks[i].wcet[j] = int(parts[2 + j])
                line_idx += 1
                
    except FileNotFoundError:
        print(f"Error: Cannot open file {filename}")
        exit(1)

def generate_jobs(config):
    jobs = []
    
    for i in range(config.num_tasks):
        task = config.tasks[i]
        release_time = 0
        job_num = 0
        
        while release_time < config.max_time:
            job = Job()
            job.task = task
            job.release_time = release_time
            job.absolute_deadline = release_time + task.deadline
            job.job_number = job_num
            job.completed = False
            
            jobs.append(job)
            release_time += task.deadline
            job_num += 1
    
    return jobs

def print_schedule(schedule, algorithm_name):
    print(f"\n================================================================")
    print(f"Schedule: {algorithm_name}")
    print(f"================================================================")
    
    total_energy = 0
    idle_time = 0
    
    for entry in schedule:
        if entry.task_name == "IDLE":
            print(f"{entry.start_time} IDLE IDLE {entry.duration} {entry.energy:.3f}J")
            idle_time += entry.duration
        else:
            print(f"{entry.start_time} {entry.task_name} {entry.frequency} {entry.duration} {entry.energy:.3f}J")
        total_energy += entry.energy
    
    total_time = schedule[-1].start_time + schedule[-1].duration
    idle_percentage = (idle_time / total_time) * 100.0
    
    print(f"\n----------------------------------------------------------------")
    print(f"Total Energy Consumption: {total_energy:.3f} J")
    print(f"Percentage Idle Time: {idle_percentage:.2f}%")
    print(f"Total Execution Time: {total_time} seconds")
    print(f"================================================================\n")