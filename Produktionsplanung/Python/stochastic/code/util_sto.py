import numpy as np
import gurobipy as gp
from gurobipy import GRB

def restore_model(model, n, T, q, I_A, I_minus_I_A, x, y, z, R, v, w, a, R_fix, d, A_l):
    # reset variable bounds for each simulation
    for t in range(T):
        for j in range(n):
            x[j, t+1].LB = 0
            x[j, t+1].UB = np.inf
            y[j, t].LB = 0
            y[j, t].UB = np.inf
            z[j, t].LB = 0
            z[j, t].UB = np.inf

   
        for l in range(q):
            for i in I_A:
                R[i, t+1, l].LB = 0
                R[i, t+1, l].UB = np.inf
                v[i, t, l].LB = 0
                v[i, t, l].UB = np.inf
                w[i, t, l].LB = 0
                w[i, t, l].UB = np.inf

    # add deleted constraints
    for t in range(T):
        for i in I_minus_I_A:
            model.addConstr(
                gp.quicksum(a[i][j]*y[j, t] for j in range(n)) <= R_fix[i-I_A.stop][t],
                name=f"ResourceConstraint_{i}_{t}")

        for j in range(n):
            model.addConstr(x[j, t+1] == x[j, t] + y[j, t] - z[j, t], name=f"InventoryBalanceProduct_{j}_{t}")
            model.addConstr(z[j, t] <= d[j][t], name=f"SalesConstraint_{j}_{t}")

       
        for l in range(q):
            for i in I_A:
                model.addConstr(
                    R[i, t + 1, l] == R[i, t, l] + v[i, t, l] + w[i, t, l] - gp.quicksum(a[i][j] * y[j, t] for j in range(n)),
                    name=f"InventoryBalanceSecondary_{i}_{t}_{l}")
                model.addConstr(v[i, t, l] <= A_l[i][t][l], name=f"AvailabilityConstraint_{i}_{t}_{l}")

    model.update()


def reoptimize_subject_to_non_anticipativity(model, n, T, q, I_A, x, y, z, v, w, p, k, h, b, c, f_star, epsilon):
    model.addConstr(gp.quicksum(gp.quicksum(p[j]*z[j, t] - k[j]*y[j, t] - h[j]*x[j, t+1] for j in range(n))
                   - (1/q)*gp.quicksum(gp.quicksum(b[i]*v[i, t, l] + c[i]*w[i, t, l] for i in I_A) for l in range(q))
                     for t in range(T)) == f_star, name="OptimalityConstraint")
    model.setObjective(gp.quicksum(gp.quicksum(gp.quicksum((1+epsilon)**t * b[i]*v[i, t, l] for i in I_A)
                     for l in range(q)) for t in range(T)), GRB.MINIMIZE)
    model.optimize()


def simulate_rolling_schedule(model, n, T, q, m_a, I_A, I_minus_I_A, x, y, z, R, v, w, a, R_fix, d, A_l, p, k, h, b, c, num_exp):
    real_CMs_rolling = []
    for ctr in range(num_exp):
        np.random.seed(ctr+1)
            
        CM_without_secondary_materials_cost = 0
        secondary_materials_cost = 0

        # iterations of rolling horizon approach
        for tau in range(T):
            # solve model with decisions fixed up to tau-1
            # objective function: maximize profit
            model.setObjective(gp.quicksum(gp.quicksum(p[j]*z[j, t] - k[j]*y[j, t] - h[j]*x[j, t+1] for j in range(n))
                   - (1/q)*gp.quicksum(gp.quicksum(b[i]*v[i, t, l] + c[i]*w[i, t, l] for i in I_A) for l in range(q)) for t in range(T)), GRB.MAXIMIZE)
            model.optimize()

            if model.status == GRB.OPTIMAL:
                f_star = model.objVal
                reoptimize_subject_to_non_anticipativity(model, n, T, q, I_A, x, y, z, v, w, p, k, h, b, c, f_star, 1.1)
                # fix variables at time tau
                for j in range(n):
                    # retrieve x, y, and z values
                    x_value = x[j, tau].x
                    y_value = y[j, tau].x
                    z_value = z[j, tau].x
                    new_x_value = x_value + y_value - z_value

                    # fix x, y, and z variables
                    x[j, tau+1].LB = new_x_value
                    x[j, tau+1].UB = new_x_value
                    y[j, tau].LB = y_value
                    y[j, tau].UB = y_value
                    z[j, tau].LB = z_value
                    z[j, tau].UB = z_value

                    CM_without_secondary_materials_cost += p[j]*z_value - k[j]*y_value - h[j]*new_x_value
                
                for l in range(q): 
                    for i in I_A:
                        # retrieve R value
                        R_value_l = R[i, tau, l].x

                        # sample availability
                        realized_A_l = np.random.randint(0, m_a*A_l[i][tau][l]+1)

                        # compute realized purchases of secondary and primary materials
                        sum_req = sum([sum([a[i][j] * y[j, t].x for t in range(tau, T)]) for j in range(n)])
                        if R_value_l + realized_A_l <= sum_req:
                            realized_v_l = realized_A_l
                        else:
                            realized_v_l = max(0, sum_req - R_value_l)
                        realized_w_l = max(0, sum([a[i][j]*y[j, tau].x for j in range(n)]) - R_value_l - realized_v_l)

                        # fix purchase variables and inventory
                        v[i, tau, l].LB = realized_v_l
                        v[i, tau, l].UB = realized_v_l
                        w[i, tau, l].LB = realized_w_l
                        w[i, tau, l].UB = realized_w_l
                        new_R_value_l = R_value_l + realized_v_l + realized_w_l - sum([a[i][j]*y[j, tau].x for j in range(n)])
                        R[i, tau+1, l].LB = new_R_value_l
                        R[i, tau+1, l].UB = new_R_value_l

                        secondary_materials_cost += b[i]*realized_v_l + c[i]*realized_w_l
                secondary_materials_cost *= (1/q)
                # remove constraints for time tau
                for l in range(q):
                    for i in I_A:
                        model.remove(model.getConstrByName(f"InventoryBalanceSecondary_{i}_{tau}_{l}"))
                        model.remove(model.getConstrByName(f"AvailabilityConstraint_{i}_{tau}_{l}"))
                    
                for i in I_minus_I_A:
                    model.remove(model.getConstrByName(f"ResourceConstraint_{i}_{tau}"))

                for j in range(n):
                    model.remove(model.getConstrByName(f"InventoryBalanceProduct_{j}_{tau}"))
                    model.remove(model.getConstrByName(f"SalesConstraint_{j}_{tau}"))
                
                model.remove(model.getConstrByName(name="OptimalityConstraint"))     
                
                model.update()
        total_CM = CM_without_secondary_materials_cost - secondary_materials_cost
        real_CMs_rolling.append(total_CM)
        restore_model(model, n, T, q, I_A, I_minus_I_A, x, y, z, R, v, w, a, R_fix, d, A_l)
  
    real_CM_avg_rolling = np.mean(real_CMs_rolling)
    return real_CM_avg_rolling


def simulate_schedule(n, T, I_A, m_a, x, y, z, a, A, p, k, h, b, c, R_a, num_exp):
    real_CMs = []
    for ctr in range(num_exp):
        # initialize
        np.random.seed(ctr+1)
        CM_without_secondary_materials_cost = sum([sum([p[j]*z[j, t].x-k[j]*y[j, t].x-h[j]*x[j, t+1].x for j in range(n)]) for t in range(T)])
        secondary_materials_cost = 0
        R_values = [R_a[i] for i in I_A]

        # iterate periods
        for tau in range(T):
            for i in I_A:
                # sample availability
                realized_A = np.random.randint(0, m_a*A[i][tau])
                R_value = R_values[i]

                # compute realized purchases of secondary and primary materials
                sum_req = sum([sum([a[i][j] * y[j, t].x for t in range(tau, T)]) for j in range(n)])
                if R_value + realized_A <= sum_req:
                    realized_v = realized_A
                else:
                    realized_v = max(0, sum_req - R_value)
                realized_w = max(0, sum([a[i][j] * y[j, tau].x for j in range(n)]) - R_value - realized_v)

                # update inventory for tau + 1
                R_values[i] = R_value + realized_v + realized_w - sum([a[i][j] * y[j, tau].x for j in range(n)])

                secondary_materials_cost += b[i] * realized_v + c[i] * realized_w

        total_CM = CM_without_secondary_materials_cost - secondary_materials_cost
        real_CMs.append(total_CM)

    real_CM = np.mean(real_CMs)
    return real_CM


def save_results(model, x, y, z, w, v, q, m_a, R, T, n, d, I_A, filename):
    # check whether folder results exists; if not, create folder
    with open(f"{filename}.txt", "w") as f:
        # Summary of key metrics
        f.write("Optimal circular master production schedule\n\n")
        f.write("------------------------------------------------------------\n")
        f.write(" Product | Period | Inventory | Production | Sales | Demand \n")
        f.write("------------------------------------------------------------\n")
        for i in range(n):
            for t in range(T):
                # Write rows for each product i and period t
                f.write(f"{i+1:8} | {t+1:6} | {x[i,t].x:9.2f} | {y[i,t].x:10.2f} | {z[i,t].x:5.2f} | {d[i][t]:6.2f} \n")
        f.write("\n")
        f.write("---------------------------------------------------------------------------------\n")
        f.write(" Secondary m. | Period |  Inventory | Procurement sec. m. | Procurement prim. m. \n")
        f.write("---------------------------------------------------------------------------------\n")
        
        v_mean= [[0.0]*T]*m_a
        for i in I_A:
            for t in range(T):
               v_mean[i][t] == (1/q)*sum(v[i, t, l].x for l in range(q))
        
        w_mean= [[0.0]*T]*m_a
        for i in I_A:
            for t in range(T):
               w_mean[i][t] == (1/q)*sum(w[i, t, l].x for l in range(q))
        
        R_mean= [[0.0]*T]*m_a
        for i in I_A:
            for t in range(T):
               R_mean[i][t] == (1/q)*sum(R[i, t, l].x for l in range(q))
            
        for i in I_A:
            for t in range(T):
                # Write rows for each secondary material i and period t
                f.write(f"{i+1:13} | {t+1:6} | {R_mean[i][t]:10.2f} | {v_mean[i][t]:19.2f} | {w_mean[i][t]:20.2f} \n")

        f.write("\n")
        
        # Compute alpha service level for each product
        service_levels = []
        for j in range(n):
            # Check if inventory + production >= demand in each period
            fulfilled_periods = sum((x[j, t].x + y[j, t].x) >= d[j][t] for t in range(T))
            service_level_j = fulfilled_periods / T  # fraction of periods with fulfilled demand
            service_levels.append(service_level_j)

        for j, sl in enumerate(service_levels):
            f.write(f"Service level for product {j + 1}: {sl:.4f}\n")

        f.write(f"Total contribution margin: {model.objVal:.4f}\n")
