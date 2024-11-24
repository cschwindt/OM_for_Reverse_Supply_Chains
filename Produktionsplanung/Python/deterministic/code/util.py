import numpy as np
import gurobipy as gp


def restore_model(model, n, T, I_A, I_minus_I_A, x, y, z, R, v, w, a, R_fix, d, A):
    # reset variable bounds for each simulation
    for t in range(T):
        for j in range(n):
            x[j, t+1].LB = 0
            x[j, t+1].UB = np.inf
            y[j, t].LB = 0
            y[j, t].UB = np.inf
            z[j, t].LB = 0
            z[j, t].UB = np.inf

        for i in I_A:
            R[i, t+1].LB = 0
            R[i, t+1].UB = np.inf
            v[i, t].LB = 0
            v[i, t].UB = np.inf
            w[i, t].LB = 0
            w[i, t].UB = np.inf

    # add deleted constraints
    for t in range(T):
        for i in I_minus_I_A:
            model.addConstr(
                gp.quicksum(a[i][j]*y[j, t] for j in range(n)) <= R_fix[i-I_A.stop][t],
                name=f"ResourceConstraint_{i}_{t}")

        for j in range(n):
            model.addConstr(x[j, t+1] == x[j, t] + y[j, t] - z[j, t], name=f"InventoryBalanceProduct_{j}_{t}")
            model.addConstr(z[j, t] <= d[j][t], name=f"SalesConstraint_{j}_{t}")
            model.addConstr(x[j, t+1] >= 0, name=f"NonNegativityX_{j}_{t}")
            model.addConstr(y[j, t] >= 0, name=f"NonNegativityY_{j}_{t}")
            model.addConstr(z[j, t] >= 0, name=f"NonNegativityZ_{j}_{t}")

        for i in I_A:
            model.addConstr(
                R[i, t + 1] == R[i, t] + v[i, t] + w[i, t] - gp.quicksum(a[i][j] * y[j, t] for j in range(n)),
                name=f"InventoryBalanceSecondary_{i}_{t}")
            model.addConstr(v[i, t] <= A[i][t], name=f"AvailabilityConstraint_{i}_{t}")
            model.addConstr(R[i, t+1] >= 0, name=f"NonNegativityR_{i}_{t}")
            model.addConstr(v[i, t] >= 0, name=f"NonNegativityV_{i}_{t}")
            model.addConstr(w[i, t] >= 0, name=f"NonNegativityW_{i}_{t}")

    model.update()


def simulate_schedule(n, T, I_A, x, y, z, v, a, A, p, k, h, b, c, R_a, num_exp):
    real_CMs = []
    for ctr in range(num_exp):
        # initialize
        np.random.seed(ctr)
        CM_without_secondary_materials_cost = sum([sum([p[j]*z[j, t].x-k[j]*y[j, t].x-h[j]*x[j, t+1].x for j in range(n)]) for t in range(T)])
        secondary_materials_cost = 0
        R_values = [R_a[i] for i in I_A]

        # iterate periods
        for tau in range(T):
            for i in I_A:
                # sample availability
                realized_A = max(0, A[i][tau] + np.random.randint(-15, 15))
                R_value = R_values[i]

                # compute realized purchases of secondary and primary materials
                realized_v = min(v[i, tau].x, realized_A)
                # realized_v = min(realized_A, max(0, sum([a[i][j] * y[j, tau].x for j in range(n)]) - R_value))
                realized_w = max(0, sum([a[i][j] * y[j, tau].x for j in range(n)]) - R_value - realized_v)

                # update inventory for tau + 1
                R_values[i] = R_value + realized_v + realized_w - sum([a[i][j] * y[j, tau].x for j in range(n)])

                secondary_materials_cost += b[i] * realized_v + c[i] * realized_w

        total_CM = CM_without_secondary_materials_cost - secondary_materials_cost
        real_CMs.append(total_CM)

    real_CM = np.mean(real_CMs)
    return real_CM


def simulate_rolling_schedule(model, n, T, I_A, I_minus_I_A, x, y, z, R, v, w, a, R_fix, d, A, p, k, h, b, c, num_exp):
    real_CMs_rolling = []
    for ctr in range(num_exp):
        np.random.seed(ctr)
            
        CM_without_secondary_materials_cost = 0
        secondary_materials_cost = 0

        # iterations of rolling horizon approach
        for tau in range(T):
            # solve model with decisions fixed up to tau-1
            model.optimize()
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
            
            for i in I_A:
                # retrieve R value
                R_value = R[i, tau].x

                # sample availability
                realized_A = max(0, A[i][tau] + np.random.randint(-15, 15))

                # compute realized purchases of secondary and primary materials
                realized_v = min(v[i, tau].x, realized_A)
                # realized_v = min(realized_A, max(0, sum([a[i][j]*y[j, tau].x for j in range(n)]) - R_value))
                realized_w = max(0, sum([a[i][j]*y[j, tau].x for j in range(n)]) - R_value - realized_v)

                # fix purchase variables and inventory
                v[i, tau].LB = realized_v
                v[i, tau].UB = realized_v
                w[i, tau].LB = realized_w
                w[i, tau].UB = realized_w
                new_R_value = R_value + realized_v + realized_w - sum([a[i][j]*y[j, tau].x for j in range(n)])
                R[i, tau+1].LB = new_R_value
                R[i, tau+1].UB = new_R_value

                secondary_materials_cost += b[i]*realized_v + c[i]*realized_w
           
            # remove constraints for time tau
            for i in I_A:
                model.remove(model.getConstrByName(f"InventoryBalanceSecondary_{i}_{tau}"))
                model.remove(model.getConstrByName(f"AvailabilityConstraint_{i}_{tau}"))
                model.remove(model.getConstrByName(f"NonNegativityR_{i}_{tau}"))
                model.remove(model.getConstrByName(f"NonNegativityV_{i}_{tau}"))
                model.remove(model.getConstrByName(f"NonNegativityW_{i}_{tau}"))
            
            for i in I_minus_I_A:
                model.remove(model.getConstrByName(f"ResourceConstraint_{i}_{tau}"))

            for j in range(n):
                model.remove(model.getConstrByName(f"InventoryBalanceProduct_{j}_{tau}"))
                model.remove(model.getConstrByName(f"SalesConstraint_{j}_{tau}"))
                model.remove(model.getConstrByName(f"NonNegativityX_{j}_{tau}"))
                model.remove(model.getConstrByName(f"NonNegativityY_{j}_{tau}"))
                model.remove(model.getConstrByName(f"NonNegativityZ_{j}_{tau}"))
                
            model.update()

        total_CM = CM_without_secondary_materials_cost - secondary_materials_cost
        real_CMs_rolling.append(total_CM)
        restore_model(model, n, T, I_A, I_minus_I_A, x, y, z, R, v, w, a, R_fix, d, A)
  
    real_CM_avg_rolling = np.mean(real_CMs_rolling)
    return real_CM_avg_rolling


def save_results(model, x, y, z, w, v, R, T, n, d, I_A, filename):
    # check whether folder results exists; if not, create folder
    with open(f"Produktionsplanung/Python/deterministic/results/{filename}.txt", "w") as f:
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
        for i in I_A:
            for t in range(T):
                # Write rows for each secondary material i and period t
                f.write(f"{i+1:13} | {t+1:6} | {R[i,t].x:10.2f} | {v[i,t].x:19.2f} | {w[i,t].x:20.2f} \n")

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
