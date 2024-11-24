from gurobipy import GRB
from util import *

np.random.seed(101)

# set up parameters
T = 12  # number of periods
n = 6   # number of products
m = 4   # number of production factors

I_A = range(min(2, m))
d = [[np.random.randint(4, 8)*(1.1-np.sin(j+2*np.pi*t/T)) for t in range(T)] for j in range(n)]  # product demands
p = [np.random.randint(120, 150) for _ in range(n)]   # product prices
k = [np.random.randint(10, 20) for _ in range(n)]     # production cost
h = [np.random.uniform(0.5, 2.5) for _ in range(n)]   # holding cost
b = [np.random.randint(5, 10) for _ in I_A]           # procurement cost of secondary materials
c = [np.random.randint(30, 60) for _ in I_A]          # procurement cost of corresponding primary materials
A = [[np.random.randint(15, 35) for _ in range(T)] for _ in range(m)]  # availability of secondary materials (deterministic)                             # set of all secondary materials
a = [[np.random.randint(0, 8) for _ in range(n)] for _ in range(m)]    # production coefficients
I_minus_I_A = [i for i in range(m) if i not in I_A]   # set of non-secondary production factors
R_fix = [[np.random.randint(50, 100) for _ in range(T)] for _ in I_minus_I_A]  # capacity of non-secondary production factors
x_a = [np.random.randint(3, 5) for _ in range(n)]     # initial inventory levels of products
R_a = [np.random.randint(10, 50) for _ in I_A]        # initial inventory levels of secondary materials

# declare model
model = gp.Model("MPS_CE")

# define variables
# xjt: inventory level of product j at the end of period t
# yjt: quantity of product j manufactured in period t
# zjt: sales of product j in period t
# Rit: inventory level of secondary material i
# vit: procurement of secondary material i in period t
# wit: procurement of primary material replacing secondary material i in period t

x = model.addVars(n, T+1, name="x", vtype=GRB.CONTINUOUS)
y = model.addVars(n, T, name="y", vtype=GRB.CONTINUOUS)
z = model.addVars(n, T, name="z", vtype=GRB.CONTINUOUS)
v = model.addVars(m, T, name="v", vtype=GRB.CONTINUOUS)
w = model.addVars(m, T, name="w", vtype=GRB.CONTINUOUS)
R = model.addVars(m, T+1, name="R", vtype=GRB.CONTINUOUS)

# objective function: maximize profit
model.setObjective(gp.quicksum(gp.quicksum(p[j]*z[j, t] - k[j]*y[j, t] - h[j]*x[j, t+1] for j in range(n))
                   - gp.quicksum(b[i]*v[i, t] + c[i]*w[i, t] for i in I_A) for t in range(T)), GRB.MAXIMIZE)

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

# 5. non-negativity constraints
for t in range(T):
    for j in range(n):
        model.addConstr(x[j, t+1] >= 0, name=f"NonNegativityX_{j}_{t}")
        model.addConstr(y[j, t] >= 0, name=f"NonNegativityY_{j}_{t}")
        model.addConstr(z[j, t] >= 0, name=f"NonNegativityZ_{j}_{t}")

# 6. initial inventory secondary material
for i in I_A:
    model.addConstr(R[i, 0] == R_a[i], name=f"InventoryInitSecondary_{i}")

# 7. inventory balance constraint secondary material
for t in range(T):
    for i in I_A:
        model.addConstr(R[i, t+1] == R[i, t] + v[i, t] + w[i, t] - gp.quicksum(a[i][j]*y[j, t] for j in range(n)),
                        name=f"InventoryBalanceSecondary_{i}_{t}")

# 8. availability constraint secondary material
for t in range(T):
    for i in I_A:
        model.addConstr(v[i, t] <= A[i][t], name=f"AvailabilityConstraint_{i}_{t}")

# 9. non-negativity of secondary material
for t in range(T):
    for i in I_A:
        model.addConstr(R[i, t+1] >= 0, name=f"NonNegativityR_{i}_{t}")
        model.addConstr(v[i, t] >= 0, name=f"NonNegativityV_{i}_{t}")
        model.addConstr(w[i, t] >= 0, name=f"NonNegativityW_{i}_{t}")

# solve the model
model.optimize()

# save the solution if optimal
if model.status == GRB.OPTIMAL:
    predictive_CM = model.objVal
    save_results(model, x, y, z, w, v, R, T, n, d, I_A, "results_model")

num_exp = 100
real_CM_avg = simulate_schedule(n, T, I_A, x, y, z, v, a, A, p, k, h, b, c, R_a, num_exp)
real_CM_avg_rolling = simulate_rolling_schedule(model, n, T, I_A, I_minus_I_A, x, y, z, R, v, w, a, R_fix, d, A, p, k, h, b, c, num_exp)
print(f"\n\nContribution margin predicted by expected value model: {predictive_CM}")
print(f"Average realized contribution margin of schedule: {real_CM_avg}")
print(f"Average realized contribution margin of rolling schedule: {real_CM_avg_rolling}")
