# Simulation of Patient flow with exponential distribution

import random  # For generating random numbers
import simpy  # For simulating events over time
import matplotlib.pyplot as plt  # For data visualization

# Setting up basic constants for the simulation:
RANDOM_SEED = 48  # Random seed for reproducibility
NUM_DOCTORS = 2  # Initial number of doctors
TREATMENT_TIME = 5  # Average treatment time for a patient (mean of exponential distribution)
T_INTER = 7  # Average time between patient arrivals (mean of exponential distribution)
SIM_TIME = 200  # Initial simulation time before adding more doctors
TREAT_PROBABILITY = 0.8  # Probability that a patient gets ec

# Lists to keep track of event timings:
arrival_times = []  # Times when patients arrive
treated_times = []  # Times when patients are treated
left_without_treatment_times = []  # Times when patients leave without treatment
wait_times = []  # Times patients spend waiting before being treated
queue_lengths = []  # Track queue length over time
time_stamps = []  # Track corresponding time stamps for queue lengths

# Define a Hospital class to handle hospital functions:
class Hospital(object):
    def __init__(self, env, num_doctors, treatment_time):
        self.env = env  # Current simulation environment
        self.doctor = simpy.Resource(env, num_doctors)  # Resource representing doctors
        self.treatment_time = treatment_time  # Average treatment time
        self.queue_length = 0  # Track current queue length

    def treat(self, patient):
        # Simulate treatment of a patient with exponential distribution
        treatment_duration = random.expovariate(1 / self.treatment_time)
        yield self.env.timeout(treatment_duration)  # Wait for treatment to complete
        print(f"{patient} was treated in {treatment_duration:.2f} minutes.")  # Print message about treatment

# Function that simulates a patient's behavior in the hospital:
def patient(env, name, hospital):
    # Patient's arrival and arrival time are recorded
    arrival_time = env.now
    print(f'{name} arrives at the hospital at {arrival_time:.2f}.')
    arrival_times.append(arrival_time)
    
    # Increase the queue length and record it with timestamp
    hospital.queue_length += 1
    queue_lengths.append(hospital.queue_length)
    time_stamps.append(arrival_time)

    # Patient requests treatment
    with hospital.doctor.request() as request:
        yield request  # Wait until a doctor is available

        # Decrease the queue length and record it with timestamp
        hospital.queue_length -= 1
        queue_lengths.append(hospital.queue_length)
        time_stamps.append(env.now)

        # Calculate wait time based on individual arrival time
        wait_time = env.now - arrival_time
        wait_times.append(wait_time)  # Record the wait time

        # Decide if the patient gets treated or leaves
        if random.random() < TREAT_PROBABILITY:
            yield env.process(hospital.treat(name))  # Patient's treatment time is recorded
            print(f'{name} leaves the hospital after being treated at {env.now:.2f}.')
            treated_times.append(env.now)
        else:
            # Patient's departure time (without treatment) is recorded
            print(f'{name} chooses to leave the hospital without treatment at {env.now:.2f}.')
            left_without_treatment_times.append(env.now)

# Setting up the simulation: start with a few patients and add more over time
def setup(env, num_doctors, treatment_time, t_inter):
    hospital = Hospital(env, num_doctors, treatment_time)
    
    # Start with initial patients
    for i in range(1, 5):
        env.process(patient(env, f'Patient {i}', hospital))

    # Add new patients at random intervals
    i = 5
    while True:
        inter_arrival_time = random.expovariate(1 / t_inter)
        yield env.timeout(inter_arrival_time)
        print(f'Patient {i} arrives after {inter_arrival_time:.2f} minutes.')
        env.process(patient(env, f'Patient {i}', hospital))
        i += 1

# Function to add more doctors during the simulation
def add_doctors(env, hospital, num_doctors_to_add):
    # Inform that new doctors are being added
    print(f'Adding {num_doctors_to_add} new doctors at t = {env.now}.')
    for _ in range(num_doctors_to_add):
        # This approach does not change resource capacity, so consider alternative simulations for true scaling.
        hospital.doctor.request()  # Simulate request by 'doctors'
        yield env.timeout(0)

# Initialize and run the simulation:
print('Hospital Simulation (M/M/c Queue)')
random.seed(RANDOM_SEED)  # Set seed for reproducibility

# Create a new simpy environment
env = simpy.Environment()
hospital = Hospital(env, NUM_DOCTORS, TREATMENT_TIME)
env.process(setup(env, NUM_DOCTORS, TREATMENT_TIME, T_INTER))
env.run(until=SIM_TIME)  # Run the first part of the simulation

env.process(add_doctors(env, hospital, 2))  # Adding doctors midway
env.run(until=300)  # Extend the simulation

# Calculate results based on total simulation time (200 minutes)
total_patients = len(arrival_times)
treated_count = len(treated_times)
left_without_treatment_count = len(left_without_treatment_times)
average_wait_time = sum(wait_times) / len(wait_times) if wait_times else float('inf')
throughput = treated_count / 200  # Based on the entire simulation period of 200 minutes

if queue_lengths:
    average_queue_length = sum(queue_lengths) / len(queue_lengths)
else:
    average_queue_length = 0
# Display results
print("\n--------------------------------------------------------------")
print("Expected percentage of patients to be treated:", TREAT_PROBABILITY * 100, "%")
print("Total Patients:", total_patients)
print("Number of patients treated:", treated_count)
print("Number of patients who left without treatment:", left_without_treatment_count)
print(f"Actual percentage of treated patients: {(treated_count / total_patients) * 100:.2f}%")
print("Average wait time for treated patients: %.2f minutes" % average_wait_time)
print(f"Average Queue Length (L): {average_queue_length:.2f}")
print(f"Throughput: {throughput:.2f} patients per minute")

# Create and display cumulative line plot with matplotlib:
time_points = sorted(set(arrival_times + treated_times + left_without_treatment_times))
cumulative_arrivals = [sum(1 for t in arrival_times if t <= time) for time in time_points]
cumulative_treated = [sum(1 for t in treated_times if t <= time) for time in time_points]
cumulative_left = [sum(1 for t in left_without_treatment_times if t <= time) for time in time_points]

plt.figure(figsize=(12, 8))
plt.plot(time_points, cumulative_arrivals, label='Cumulative Arrivals', color='blue', marker='o')
plt.plot(time_points, cumulative_treated, label='Cumulative Treated', color='green', marker='o')
plt.plot(time_points, cumulative_left, label='Cumulative Left Without Treatment', color='red', marker='o')
plt.title('Hospital Simulation Results (Cumulative Over Time)')
plt.xlabel('Time (minutes)')
plt.ylabel('Cumulative Number of Patients')
plt.legend()
plt.grid(True)
plt.show()
