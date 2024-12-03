from gurobipy import GRB
from util_sto import *

np.random.seed(101)

def run_gurobi_solver(params , params_inputs):
    
    T  = int(params["T (periods)"]) # number of periods
    n = int(params["n (products)"]) # number of products
    m = int(params["m (factors)"])  # number of production factors
    alpha = int(params["alpha "]) #number of secondary factors
    I_A = range(alpha) # set of secondary factors
    q = int(params["q (samples)"]) # samples

    d = [[0.0]*T]*n
    for j in range(n):
          for t in range(T):
                d[j][t] = float(params_inputs[f"d-{j+1}-{t+1}"].text())*(1.1-np.sin(j+2*np.pi*t/T))
    p = [0.0]*n
    for j in range(n):
         p[j] = float(params_inputs[f"p-{j+1}"].text())
    k = [0.0]*n
    for j in range(n):
         k[j] = float(params_inputs[f"k-{j+1}"].text())
    h = [0.0]*n
    for j in range(n):
         h[j] = float(params_inputs[f"h-{j+1}"].text())
    b = [0.0]*alpha
    for i in range(alpha):
        b[i] = float(params_inputs[f"b-{i+1}"].text())   
    c = [0.0]*alpha
    for i in range(alpha):
        c[i] = float(params_inputs[f"c-{i+1}"].text()) 
    A = [[0.0]*T]*m
    for i in range(m):
          for t in range(T):
                A[i][t] = float(params_inputs[f"d-{j+1}-{t+1}"].text())
    a = [[0.0]*n]*m
    for i in range(m):
        for j in range(n):
                a[i][j] = float(params_inputs[f"a-{i+1}-{j+1}"].text())
    I_minus_I_A = [i for i in range(m) if i not in I_A]  
    R_fix = [[0.0]*T]*(m-alpha)
    for i in range(m-alpha):
        for t in range(T):
                R_fix[i][t] = float(params_inputs[f"R_fix-{i+1}-{t+1}"].text())
    x_a = [0.0]*n
    for j in range(n):
         x_a[j] = float(params_inputs[f"x_a-{j+1}"].text()) 
    R_a = [0.0]*alpha
    for i in range(alpha):
         R_a[i] = float(params_inputs[f"Ra-{i+1}"].text())
    
    A_l = [[[np.random.randint(0, alpha*A[i][t]) for _ in range(q)] for t in range(T)] for i in range(m)]
    
    # declare model
    model = gp.Model("MPS_CE_Sampling")
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
    v = model.addVars(m, T, q, name="v", vtype=GRB.CONTINUOUS)
    w = model.addVars(m, T, q, name="w", vtype=GRB.CONTINUOUS)
    R = model.addVars(m, T+1, q, name="R", vtype=GRB.CONTINUOUS)

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
    results = {}

    # save the solution if optimal
    if model.status == GRB.OPTIMAL:
          predictive_CM = model.objVal
          save_results(model, x, y, z, w, v, q, alpha, R, T, n, d, I_A, "results_model")

    num_exp = 100
    real_CM_avg = simulate_schedule(n, T, I_A, x, y, z, a, A, p, k, h, b, c, R_a, num_exp)
    results["Contribution margin predicted by expected value model"] = predictive_CM
    results["Average realized contribution margin of schedule"] = real_CM_avg

    return results


    
