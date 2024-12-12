from gurobipy import GRB
from util_sto import *

np.random.seed(101)

def run_gurobi_solver(n, m, m_a, T, x_a, R_a, R_fix, a, A, b, c, h, k, p , d, q):
    
    I_A = range(m_a)
    I_minus_I_A = [i for i in range(m) if i not in I_A]  
    A_l = [[[np.random.randint(0, m_a*A[i][t]) for _ in range(q)] for t in range(T)] for i in range(m)]
    
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
      predictive_CM_sa = model.objVal
      save_results(model, x, y, z, w, v, q, m_a, R, T, n, d, I_A, "results_model")

      real_CM_avg_sa_na_rolling = simulate_rolling_schedule(model, n, T, q, m_a, I_A, I_minus_I_A, x, y, z, R, v, w, a, R_fix, d, A_l, p, k, h, b, c, num_exp)

      num_exp = 100
      real_CM_avg_sa = simulate_schedule(n, T, I_A, x, y, z, a, A, p, k, h, b, c, R_a, num_exp)
      reoptimize_subject_to_non_anticipativity(model, n, T, q, I_A, x, y, z, v, w, p, k, h, b, c, predictive_CM_sa, 1.1)
      real_CM_avg_sa_na = simulate_schedule(n, T, I_A, x, y, z, a, A, p, k, h, b, c, R_a, num_exp)
      save_results(model, x, y, z, w, v, q, m_a, R, T, n, d, I_A, "results_model_na")
      results["Contribution margin predicted by expected value model"] = predictive_CM_sa
      results["Average realized contribution margin of sampling approximation without non-anticipativity"] = real_CM_avg_sa
      print(f"Average realized contribution margin of rolling schedule: {real_CM_avg_sa_na_rolling}")
      results["Average realized contribution margin of sampling approximation with non-anticipativity"] = real_CM_avg_sa_na

    return results


    
