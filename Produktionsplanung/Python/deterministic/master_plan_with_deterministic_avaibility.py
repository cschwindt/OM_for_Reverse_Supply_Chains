import gurobipy as gp
from gurobipy import GRB
import numpy as np
np.random.seed(50)

# Define the model
model = gp.Model("CircularEconomyProduction")

# Set up parameters
T = 5  # Example: number of periods
n = 6  # Number of products
m = 4  # Number of factors

d = [[np.random.randint(1, 100) for _ in range(T)] for _ in range(n)]  # products demand
p = [np.random.randint(8, 15) for _ in range(n)]      # Prices of products
k = [np.random.randint(5, 15) for _ in range(n)]      # Production cost
h = [np.random.randint(1, 5) for _ in range(n)]       # Holding costs
b = [np.random.randint(1, 3) for _ in range(m)]       # Procurement costs for factors
c = [np.random.randint(4, 6) for _ in range(m)]       # Procurement cost of corresponding primary products
A = [ [np.random.randint(30, 80) for _ in range(T)] for _ in range(m) ] # Availability of reusable factors (certain)
I_A = list(np.random.choice(range(m), 3, replace=False) )          # Set of all reusable factors
a = [ [np.random.randint(1, 3) for _ in range(n)] for _ in range(m) ]
A_diff_I_A = [i for i in range(m) if i not in I_A] # the set of product factor that are not reusable
x_a = [np.random.randint(3, 5) for _ in range(n)]  # start invertory level for each product 
R_a =[np.random.randint(1, 5) for _ in I_A]  #start capacity for each reusable product

# Define variables
# xjt: Inventory level of product j at the end of period t
# yjt: Quantity of factor i used in period t
# zjt: Quantity of demand satisfied by product j in period t
# vit: Procurement of factor i in period t
# wit: Procurement of primary product replacing factor i in period t
x = model.addVars(n, T+1, name="x", vtype=GRB.CONTINUOUS)  # inventory of product j at time t
y = model.addVars(n, T, name="y", vtype=GRB.CONTINUOUS)  # use of factor i in period t
z = model.addVars(n, T, name="z", vtype=GRB.CONTINUOUS)  # demand satisfied
v = model.addVars(m, T, name="v", vtype=GRB.CONTINUOUS)  # procurement of reusable factor i
w = model.addVars(m, T, name="w", vtype=GRB.CONTINUOUS)  # procurement of primary product replacing factor i
R = model.addVars(m , T+1,name="R", vtype=GRB.CONTINUOUS )

# Objective Function: Maximize profit
model.setObjective(gp.quicksum(gp.quicksum(p[j]*z[j,t] - k[j]*y[j,t] - h[j]*x[j,t+1] for j in range(n))  
                   - gp.quicksum(b[i]*v[i,t] + c[i]*w[i,t] for i in I_A ) for t in range(T)), GRB.MAXIMIZE)

# Constraints
# 1. Resource constraints
for t in range(T):
    for i in A_diff_I_A:
        model.addConstr(gp.quicksum(a[i][j]*y[j,t] for j in range(n)) <= R[i,t], 
                        name=f"ResourceConstraint_{i}_{t}")

# 2. Inventory initialization
for j in range(n):
    model.addConstr(x[j,0] == x_a[j], name=f"InventoryInit_{j}")

# 3. Inventory dynamics
for t in range(T):
    for j in range(n):
        model.addConstr(x[j,t+1] == x[j,t] + y[j,t] - z[j,t], 
                        name=f"InventoryDynamics_{j}_{t}")

# 4. Demand constraint
for t in range(T):
    for j in range(n):
        model.addConstr(z[j,t] <= d[j][t], name=f"DemandConstraint_{j}_{t}")

# 5. Non-negativity
for t in range(T):
    for j in range(n):
        model.addConstr(x[j,t+1] >= 0, name=f"NonNegativity_{j}_{t}")
        model.addConstr(y[j,t] >= 0, name=f"NonNegativityZ_{j}_{t}")
        model.addConstr(z[j,t] >= 0, name=f"NonNegativityZ_{j}_{t}")

# 6. Initial Resource Allocation
for i in I_A:
    model.addConstr(R[i,0] == R_a[i], name=f"InitialResourceAllocation_{i}")

# 7. Resource Dynamics
for t in range(T):
    for i in I_A:
        model.addConstr(R[i,t+1] == R[i,t] + v[i,t] + w[i,t] - gp.quicksum(a[i][j]*y[j,t] for j in range(n)),
                        name=f"ResourceDynamics_{i}_{t}")

# 8. Availability constraints
for t in range(T):
    for i in range(m):
        model.addConstr(v[i,t] <= A[i][t], name=f"AvailabilityConstraint_{i}_{t}")

# 9. Non-negativity of Resources
for t in range(T):
    for i in I_A:
        model.addConstr(R[i,t+1] >= 0, name=f"NonNegativityResource_{i}_{t}")
        model.addConstr(v[i,t] >= 0, name=f"NonNegativityV_{i}_{t}")
        model.addConstr(w[i,t] >= 0, name=f"NonNegativityW_{i}_{t}")

# Solve the model
model.optimize()

# Print the solution if optimal
if model.status == GRB.OPTIMAL:
   with open(r"Produktionsplanung\Python\deterministic\inventory_results_extended.txt", "w") as f:
    # Summary of key metrics
    # Production plan, factor usage, resource allocation, and inventory for each product i and period t
    f.write("\n Optimal production plan for production programm planning in circualr economic\n\n")
    f.write("-----------------------------------------------------------------\n")
    f.write("Product  | Period  | Iventory  | production  | sales  | demands \n")
    f.write("-----------------------------------------------------------------\n") 
    for i in range(n):
        for t in range(T):
            # Write rows for each product i and period t
            f.write(f"{i+1:8} | {t+1:7} | {x[i,t].x:9} | {y[i,t].x:11} | {z[i,t].x:6} | {d[i][t]:8}\n")
    f.write("\n")
    f.write("----------------------------------------------------------------------------\n")
    f.write("Product  | Period  |  Residual Capacity  | reusable factor  | primary factor\n")
    f.write("----------------------------------------------------------------------------\n")
    for i in range(m):
        for t in range(T):
            # Write rows for each factor i and period t
            f.write(f"{i+1:8} | {t+1:7} | {R[i,t].x:19} | {v[i,t].x:16} | {w[i,t].x:8}\n")

    f.write("\n")
    
    # Compute service levels for each product
    service_levels = []
    for j in range(n):
        # Check if inventory + production >= demand in each period
        fulfilled_periods = sum((x[j,t].x + y[j,t].x) >= d[j][t] for t in range(T))
        service_level_j = fulfilled_periods / T  # Fraction of periods with fulfilled demand
        service_levels.append(service_level_j)

    # Compute overall service level
    overall_service_level = np.prod(service_levels)
    for j, sl in enumerate(service_levels):
        f.write(f"Service Level for Product {j + 1}: {sl:.4f}\n")
    f.write(f"\nOverall Service Level: {overall_service_level:.4f}\n\n")

    f.write(f"total profit: {model.objVal:.4f}\n")



else:
    print(f'No optimal solution found. Status: {model.status}')
