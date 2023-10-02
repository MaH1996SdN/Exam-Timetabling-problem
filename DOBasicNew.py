import gurobipy as gp
from gurobipy import GRB


exams=[] 
f = open("C:\\Users\\Mahsa\\Desktop\\discreteinstances\\instance01.exm", "r")
for x in f:
    try:
        [exam_ID, number_of_students]=x.split()
        exams.append(exam_ID)
    except:
        pass
f.close()

f = open("C:\\Users\\Mahsa\\Desktop\\discreteinstances\\instance01.slo", "r")
time_slots=range(1,int(f.readline().split()[0])+1) 
distance=range(1,min(6,len(time_slots))) 
f.close()

enrollment=dict() 
f = open("C:\\Users\\Mahsa\\Desktop\\discreteinstances\\instance01.stu", "r")
for x in f:
    try:
        enrollment[x.split()[0]].append(x.split()[1])
    except:
        enrollment[x.split()[0]]=[x.split()[1]]
f.close()
students=enrollment.keys()

#############################################################################

conflicting_exams = {}

for exam1 in exams:
    for exam2 in exams:
        if exam1 != exam2 and exam1 < exam2:
            common_students = [s for s in students if exam1 in enrollment[s] and exam2 in enrollment[s]]
            if common_students:
                conflicting_exams[(exam1, exam2)] = len(common_students)

#############################################################################

model = gp.Model()

# variables definition
x = model.addVars(time_slots, exams, vtype=GRB.BINARY, name='x')  # if an exam is held in a slot

# Constraint: Each exam is scheduled exactly once during the examination period
for exam in exams:
    model.addConstr(gp.quicksum(x[time_slot, exam] for time_slot in time_slots) == 1)


# Constraint: Two conflicting exams can not be scheduled in the same time-slot
for t in time_slots:
    for exam1, exam2 in conflicting_exams:
        if conflicting_exams[(exam1, exam2)] != 0:
            model.addConstr(x[t, exam1] + x[t, exam2] <= 1)


a = model.addVars(distance, time_slots, exams, exams, vtype=GRB.BINARY, name='a')  # variable for distances
b = model.addVars(distance, time_slots, exams, exams, vtype=GRB.BINARY, name='b')  # variable for distances
p = model.addVars(distance, exams, exams, vtype=GRB.INTEGER, name='p') # Penalty for exams

# Constraint for scheduling exams with a distance
for i in distance:
    for t in time_slots:
        for (exam1, exam2) in conflicting_exams:
                if exam1 != exam2 and t + i <= len(time_slots):
                    model.addConstr(a[i, t, exam1, exam2] >= x[t, exam1] + x[t + i, exam2] - 1)
                    model.addConstr(b[i, t, exam1, exam2] >= x[t + i, exam1] + x[t, exam2] - 1)
                model.addConstr(p[i, exam1, exam2] == sum(a[i, t, exam1, exam2] + b[i, t, exam1, exam2] for t in range(1, len(time_slots) - i + 1)))        
         
############################################################################################
# Objective function and penalty calculation
objective = sum(p[i, exam1, exam2] * (2**(5-i)) * conflicting_exams.get((exam1, exam2), 0) / len(students)
                for i in distance for exam1, exam2 in conflicting_exams )

model.setObjective(objective, GRB.MINIMIZE)

model.Params.TimeLimit = 3000
model.optimize()

# Print the optimal solution
if model.status == GRB.TIME_LIMIT:
    sol = model.getAttr('X', x)
    scheduled_exams = [(key[1], key[0]) for key, value in sol.items() if value == 1]

    if scheduled_exams:
        print("Scheduled exams:")
        for exam, time_slot in scheduled_exams:
            print(f"Exam {exam} : Time slot {time_slot}")
        print(f'Objective value: {model.objVal}')
    else:
        print('No exams scheduled.')
else:
    print('No solution found.')
