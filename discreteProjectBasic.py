import gurobipy as gp
from gurobipy import GRB

env = gp.Env()
env.start()
env.setParam("Threads", 4)
env.setParam("Presolve", 2)
env.setParam("MIPGap", 1e-5)
env.setParam("TimeLimit", 600)

def read_input_files(instance):
    exams = {}
    students = set()
    num_time_slots = 0
    enrollments = []

    with open(r"C:\Users\edoardo\Desktop\discreteinstances\instance07.exm", "r") as file:
        lines = file.readlines()  # Read all lines at once

    #NUMBER OF SRUDENTS IN EACH EXAM
    for line in lines:
        parts = line.split()  # Split by whitespace
        if len(parts) == 2:  # Check if the line contains both exam_id and num_enrolled_students
            exam_id, num_enrolled_students = parts
            exams[int(exam_id)] = int(num_enrolled_students)

    # NUMBER OF TIME SLOTS
    # Read instance.slo file
    with open(r"C:\Users\edoardo\Desktop\discreteinstances\instance07.slo", "r") as file:
        num_time_slots = int(file.readline())

    # Read instance.stu file
    with open(r"C:\Users\edoardo\Desktop\discreteinstances\instance07.stu", "r") as file:
        lines = file.readlines()

    # ENROLLMENTS OF EACH STUDENT
    for line in lines:
        parts = line.split()  # Split by whitespace
        if len(parts) == 2:
            student_id, exam_id = parts
            students.add(student_id)
        enrollments.append((student_id, int(exam_id)))

    return exams, students, num_time_slots, enrollments

def find_conflicting_exams():
    exams, students, num_time_slots, enrollments = read_input_files(None)
    conflicting_pairs = set()  # To store conflicting exam pairs
    shared_students_counts = {}  # To store the number of shared students for each pair
    
    exam_enrollments = {}
    for student, exam in enrollments:
        if exam in exam_enrollments:
            exam_enrollments[exam].add(student)
        else:
            exam_enrollments[exam] = {student}

    sorted_exams = sorted(exams.keys())

    for i in range(len(sorted_exams)):
        exam1 = sorted_exams[i]
        for j in range(i + 1, len(sorted_exams)):
            exam2 = sorted_exams[j]
            shared_students = len(exam_enrollments.get(exam1, set()) & exam_enrollments.get(exam2, set()))
            if shared_students > 0:
                conflicting_pairs.add((exam1, exam2))
                shared_students_counts[(exam1, exam2)] = shared_students

    return conflicting_pairs, shared_students_counts

def exam_timetabling(instance):
    # Read input files
    exams, students, num_time_slots, enrollments = read_input_files(None)

    # Create a dictionary that maps each exam to a set of its students
    exam_to_students = {}
    for student_id, exam_id in enrollments:
        if exam_id not in exam_to_students:
            exam_to_students[exam_id] = set()
        exam_to_students[exam_id].add(student_id)

    # Create model
    model = gp.Model()
    
    # Disable output
    model.Params.OutputFlag = 0
    
    # Create decision variables
    x = {}
    for exam_id in exams:
        for time_slot in range(1, num_time_slots + 1):
            x[exam_id, time_slot] = model.addVar(vtype=GRB.BINARY) # 1 if exam e is scheduled in timeslot t, 0 otherwise

    # Ensure that each exam is scheduled exactly once
    for exam_id in exams:
        model.addConstr(
            gp.quicksum(x[exam_id, t] for t in range(1, num_time_slots + 1)) == 1
        )

    conflicting_pairs, shared_students_counts = find_conflicting_exams()

    # Ensure conflicting exam pairs are not scheduled together

    def calculate_common_enrollment(exam1,exam2):
        students_exam1 = {student for student, exam in enrollments if exam == exam1}
        students_exam2 = {student for student, exam in enrollments if exam == exam2}
        common_students = students_exam1.intersection(students_exam2)
        return len(common_students)
    

     # Ensure conflicting exam pairs are not scheduled together
    for exam1, exam2 in conflicting_pairs:
        for time_slot in range(1, num_time_slots + 1):
            model.addConstr(
                x[exam1, time_slot] + x[exam2, time_slot] <= 1
            )
            y = {}
            penalty_distance = 5  # Maximum time slot difference for penalty calculation

            for distance in range(1, penalty_distance + 1):
                y[exam1, exam2, distance] = model.addVar(vtype=GRB.BINARY)

                # Add constraints to enforce the relationship between y and x variables
                for time_slot in range(1, num_time_slots - distance + 1):
                    model.addConstr(
                        y[exam1, exam2, distance] >= x[exam1, time_slot] + x[exam2, time_slot + distance] - 1
                    )

    objective_expr = 0
    for exam1 in exams:
        for exam2 in exams:
            if exam1 != exam2:
                shared_students = calculate_common_enrollment(exam1,exam2)

                #print("exam1: " + str(exam1) + " - exam2: " + str(exam2) + "\nn. shared students: " + str(shared_students) + "\n\n")

                if shared_students > 0:
                    for t1 in range(1, num_time_slots + 1):
                        for i in range(1, 6):
                            t2 = (t1 + i) if (t1 + i) <= num_time_slots else (t1 + i - num_time_slots)  # Wrap the index correctly
                            penalty = ((2 ** (5 - i)) * (shared_students)) / len(students)
                            #print("penalty: " + str(penalty))
                            objective_expr += penalty * ((x[exam1, t1]) + (x[exam2, t2])) 

    # Set the objective to minimize the total penalty
    model.setObjective(objective_expr, GRB.MINIMIZE)

    # Set optimization parameters
    model.Params.TimeLimit = 6000  # Maximum runtime in seconds (10 minutes)

    # Optimize the model
    model.optimize()
    #print(f"Optimized Total Penalty: {objective_expr} ")

    def calculate_penalty_basic(timetable):
        #print('\n')
        final_penalty = 0.0
        # Convert the timetable to a dictionary mapping exams to their time slots
        exam_to_time_slot = {exam: time_slot for time_slot, exams in timetable.items() for exam in exams}

        for exam1 in exams:
            for exam2 in exams:
                if exam1 < exam2:  # Only calculate penalty if ID of exam1 is less than ID of exam2
                    shared_students = calculate_common_enrollment(exam1, exam2)
                    #print("exam1: " + str(exam1) + " exam2: " + str(exam2))
                    #print("shared_students: " + str(shared_students))
                    if shared_students > 0:
                        t1 = exam_to_time_slot[exam1]
                        t2 = exam_to_time_slot[exam2]
                        #print("t1: " + str(t1) + " t2: " + str(t2))
                        distance = abs(t1 - t2) if abs(t1 - t2) <= 5 else 0  # a penalty is assigned for each pair of conflicting exams scheduled up to a distance of 5 time-slots
                        #print("distance " + str(distance) )
                        if distance > 0:
                            final_penalty += ((2 ** (5 - distance)) * shared_students) 
                            #print(str(final_penalty) + '\n\n')
        return final_penalty/len(students)

    # Print the timetable
    if model.status == GRB.OPTIMAL:
        print(f"Optimized Total Penalty: {model.objVal} ")
        timetable = {}
        for exam_id, time_slot in x:
            if x[exam_id, time_slot].X > 0.5:
                if time_slot not in timetable:
                    timetable[time_slot] = []
                timetable[time_slot].append(exam_id)

        for time_slot in sorted(timetable.keys()):
            print(f"Time Slot {time_slot}: {timetable[time_slot]}")
        

        #ordered_timetable = {key: timetable[key] for key in sorted(timetable.keys())}
        print("Penalty of the solution: " + str(calculate_penalty_basic(timetable)))    
        #print("Penalty of the solution: " + str(calculate_penalty_advanced(ordered_timetable)))

    else:
        print("No feasible solution found.")


exam_timetabling(None)