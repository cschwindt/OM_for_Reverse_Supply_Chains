from gurobipy import GRB
import gurobipy as gp
from util_sto import *

np.random.seed(101)

# set up parameters
T = 12   # number of periods
n = 6    # number of products
m = 4    # number of production factors
q = 100  # number of samples

I_A = range(min(2, m))
d = [[np.random.randint(4, 8)*(1.1-np.sin(j+2*np.pi*t/T)) for t in range(T)] for j in range(n)]  # product demands
p = [np.random.randint(120, 150) for _ in range(n)]   # product prices
k = [np.random.randint(10, 20) for _ in range(n)]     # production cost
h = [np.random.uniform(0.5, 2.5) for _ in range(n)]   # holding cost
b = [np.random.randint(5, 10) for _ in I_A]           # procurement cost of secondary materials
c = [np.random.randint(30, 60) for _ in I_A]          # procurement cost of corresponding primary materials
A = [[np.random.randint(15, 35) for _ in range(T)] for _ in range(m)]  # availability of secondary materials (stochastic)
a = [[np.random.randint(0, 8) for _ in range(n)] for _ in range(m)]    # production coefficients
I_minus_I_A = [i for i in range(m) if i not in I_A]   # set of non-secondary production factors
R_fix = [[np.random.randint(50, 100) for _ in range(T)] for _ in I_minus_I_A]  # capacity of non-secondary production factors
x_a = [np.random.randint(3, 5) for _ in range(n)]     # initial inventory levels of products
R_a = [np.random.randint(10, 50) for _ in I_A]        # initial inventory levels of secondary materials

A_l = [[[np.random.randint(0, 2*A[i][t]) for _ in range(q)] for t in range(T)] for i in range(m)]

# declare model
model = gp.Model("MPS_CE_Sampling")

# define variables
# xjt: inventory level of product j at the end of period t
# yjt: quantity of product j manufactured in period t
# zjt: sales of product j in period t
# Ritl: inventory level of secondary material i in periode t in sample l
# vitl: procurement of secondary material i in period t in sample l
# witl: procurement of primary material replacing secondary material i in period t in sample l

x = model.addVars(n, T+1, name="x", vtype=GRB.CONTINUOUS)
y = model.addVars(n, T, name="y", vtype=GRB.CONTINUOUS)
z = model.addVars(n, T, name="z", vtype=GRB.CONTINUOUS)
v = model.addVars(m, T, q, name="v", vtype=GRB.CONTINUOUS)
w = model.addVars(m, T, q, name="w", vtype=GRB.CONTINUOUS)
R = model.addVars(m, T+1, q, name="R", vtype=GRB.CONTINUOUS)

# objective function: maximize profit
model.setObjective(gp.quicksum(gp.quicksum(p[j]*z[j, t] - k[j]*y[j, t] - h[j]*x[j, t+1] for j in range(n))
                   - (1/q)*gp.quicksum(gp.quicksum(b[i]*v[i, t, l] + c[i]*w[i, t, l] for i in I_A) for l in range(q)) for t in range(T)), GRB.MAXIMIZE)

# constraints
# 1. resource constraint for non-secondary production factors
for t in range(T):
    for i in I_minus_I_A:
        model.addConstr(gp.quicksum(a[i][j]*y[j, t] for j in range(n)) <= R_fix[i-I_A.stop][t], name=f"ResourceConstraint_{i}_{t}")

# 2. inventory initialization
for j in range(n):
    model.addConstr(x[j, 0] == x_a[j], name=f"InventoryInitProduct_{j}")

# 3. inventory balance
for t in range(T):
    for j in range(n):
        model.addConstr(x[j, t+1] == x[j, t] + y[j, t] - z[j, t], name=f"InventoryBalanceProduct_{j}_{t}")

# 4. sales constraint
for t in range(T):
    for j in range(n):
        model.addConstr(z[j, t] <= d[j][t], name=f"SalesConstraint_{j}_{t}")

# 6. initial inventory secondary material
for l in range(q):
    for i in I_A:
        model.addConstr(R[i, 0, l] == R_a[i], name=f"InventoryInitSecondary_{i}_{l}")

# 7. inventory balance constraint secondary material
for l in range(q):
    for t in range(T):
        for i in I_A:
            model.addConstr(R[i, t+1, l] == R[i, t, l] + v[i, t, l] + w[i, t, l] - gp.quicksum(a[i][j]*y[j, t]
                for j in range(n)), name=f"InventoryBalanceSecondary_{i}_{t}_{l}")

# 8. availability constraint secondary material
for l in range(q):
    for t in range(T):
        for i in I_A:
            model.addConstr(v[i, t, l] <= A_l[i][t][l], name=f"AvailabilityConstraint_{i}_{t}_{l}")

# solve the model
model.optimize()

# save the solution if optimal
if model.status == GRB.OPTIMAL:
    predictive_CM = model.objVal
    print(f"\n\nContribution margin predicted by sampling approximation: {predictive_CM}")

num_exp = 100
real_CM_avg = simulate_schedule(n, T, I_A, x, y, z, a, A, p, k, h, b, c, R_a, num_exp)
print(f"Average realized contribution margin of schedule: {real_CM_avg}")
