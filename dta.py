# Simulation of Patient flow with Uniform distribution

# Import necessary libraries
import random  # For generating random numbers
import simpy  # For simulating events over time
import matplotlib.pyplot as plt  # For data visualization

# Setting up basic constants for the simulation:
RANDOM_SEED = 48  # Random seed for reproducibility
NUM_DOCTORS = 2  # Initial number of doctors
TREATMENT_TIME = 5  # Average treatment time for a patient
T_INTER = 7  # Average time between patient arrivals
SIM_TIME = 200  # Total simulation time
TREAT_PROBABILITY = 0.8  # Probability that a patient gets treated

# Lists to keep track of event timings and queue lengths:
arrival_times = []  # Times when patients arrive
treated_times = []  # Times when patients are treated
left_without_treatment_times = []  # Times when patients leave without treatment
queue_lengths = []  # Queue length over time for calculating average
wait_times = []  # Wait times for treated patients

# Define a Hospital class to handle hospital functions:
class Hospital(object):
   def __init__(self, env, num_doctors, treatment_time):
       self.env = env  # Current simulation environment
       self.doctor = simpy.Resource(env, num_doctors)  # Resource representing doctors
       self.treatment_time = treatment_time  # Average treatment time
       self.queue = simpy.Store(env)  # A queue where patients wait for treatment

   def treat(self, patient):
       # Method that simulates treatment of a patient
       yield self.env.timeout(random.randint(self.treatment_time - 2, self.treatment_time + 2))  # Wait until the patient is treated
       print("%s was treated." % patient)  # Print message about treatment

# Function that simulates a patient's behavior in the hospital:
def patient(env, name, hospital):
   # Patient's arrival and arrival time are recorded
   arrival_time = env.now
   print('%s arrives at the hospital at %.2f.' % (name, arrival_time))
   arrival_times.append(arrival_time)
   queue_lengths.append(len(hospital.queue.items))  # Record queue length at arrival

   # Patient joins the queue
   with hospital.queue.put(name):
       yield env.timeout(0)

   # Patient requests treatment
   with hospital.doctor.request() as request:
        yield request  # Wait until a doctor is available
        
        # Record queue length when a doctor becomes available
        queue_lengths.append(len(hospital.queue.items))

        # Calculate wait time based on individual arrival time
        wait_time = env.now - arrival_time
        wait_times.append(wait_time)  # Record the wait time

        # Decide if the patient gets treated or leaves
        if random.random() < TREAT_PROBABILITY:
           yield env.process(hospital.treat(name))  # Patient's treatment time is recorded
           print('%s leaves the hospital after being treated at %.2f.' % (name, env.now))
           treated_times.append(env.now)
        else:
           # Patient's departure time (without treatment) is recorded
           print('%s chooses to leave the hospital without treatment at %.2f.' % (name, env.now))
           left_without_treatment_times.append(env.now)

# Setting up the simulation: start with a few patients and add more over time
def setup(env, num_doctors, treatment_time, t_inter):
   hospital = Hospital(env, num_doctors, treatment_time)
   
   # Start with 3 initial patients
   for i in range(1, 4):
       env.process(patient(env, 'Patient %d' % i, hospital))

   # Add new patients at regular intervals
   i = 4
   while True:
       yield env.timeout(random.randint(t_inter - 2, t_inter + 2))
       env.process(patient(env, 'Patient %d' % i, hospital))
       i += 1

# Function to add more doctors during the simulation
def add_doctors(env, hospital, num_doctors_to_add):
   # Inform that new doctors are being added
   print(f'Adding {num_doctors_to_add} new doctors at t = {env.now}.')
   
   # Add new doctors (simulate by requesting additional doctor resources)
   for _ in range(num_doctors_to_add):
       hospital.doctor.request()
       yield env.timeout(0)

# Initialize and run the simulation:
print('Hospital Simulation')
random.seed(RANDOM_SEED)  # Set seed for reproducibility

# Create a new simpy environment
env = simpy.Environment()
hospital = Hospital(env, NUM_DOCTORS, TREATMENT_TIME)
env.process(setup(env, NUM_DOCTORS, TREATMENT_TIME, T_INTER))
env.run(until=SIM_TIME)  # Run the first part of the simulation

env.process(add_doctors(env, hospital, 2))
env.run(until=300)  # Run the second part of the simulation (after adding doctors)

# Create and display a line chart with matplotlib:
plt.figure(figsize=(12, 8))

# Calculate and plot queue lengths over time
time_bins = list(range(0, SIM_TIME + 1, 10))
arrival_counts = [0] + [sum(1 for t in arrival_times if t < tb) for tb in time_bins[1:]]
treated_counts = [0] + [sum(1 for t in treated_times if t < tb) for tb in time_bins[1:]]
left_counts = [0] + [sum(1 for t in left_without_treatment_times if t < tb) for tb in time_bins[1:]]
average_wait_time = sum(wait_times) / len(wait_times) if wait_times else float('inf')

# Plot line chart with the data
plt.plot(time_bins, arrival_counts, '-o', label='Arrivals')
plt.plot(time_bins, treated_counts, '-o', label='Treated')
plt.plot(time_bins, left_counts, '-o', label='Left without treatment')

# Labeling the plot
plt.title('Hospital Simulation Results')
plt.xlabel('Time (minutes)')
plt.ylabel('Number of Patients')
plt.legend()
plt.grid(True)

# Calculate the total number of patients
total_patients = len(arrival_times)
treated_count = len(treated_times)
left_without_treatment_count = len(left_without_treatment_times)

# Calculate the average queue length (L)
if queue_lengths:
    average_queue_length = sum(queue_lengths) / len(queue_lengths)
else:
    average_queue_length = 0

# Calculate throughput based on the first simulation duration (SIM_TIME)
throughput = treated_count / SIM_TIME

# Print the results:
print("--------------------------------------------------------------")
print("Probability of a patient being treated:", TREAT_PROBABILITY * 100, "%")
print("Average Queue Length (L):", average_queue_length)
print("Throughput (patients per minute):", throughput)
print("Total Patients:", total_patients)
print("Average wait time for treated patients: %.2f minutes" % average_wait_time)
print("Number of patients treated:", treated_count)
print(f"Actual percentage of treated patients: {(treated_count / total_patients) * 100:.2f}%")
print("Number of patients who left without treatment:", left_without_treatment_count)

# Display the plot
plt.show()
