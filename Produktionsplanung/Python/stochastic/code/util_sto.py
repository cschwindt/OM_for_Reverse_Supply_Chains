import numpy as np
import gurobipy as gp


def simulate_schedule(n, T, I_A, x, y, z, a, A, p, k, h, b, c, R_a, num_exp):
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
                realized_A = np.random.randint(0, 2*A[i][tau])
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

def save_results(model, x, y, z, w, v, q, alpha, R, T, n, d, I_A, filename):
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
        
        v_mean= [[0.0]*T]*alpha
        print(I_A)
        for i in I_A:
            for t in range(T):
               v_mean[i][t] == (1/q)*sum(v[i, t, l].x for l in range(q))
        
        w_mean= [[0.0]*T]*alpha
        for i in I_A:
            for t in range(T):
               w_mean[i][t] == (1/q)*sum(w[i, t, l].x for l in range(q))
        
        R_mean= [[0.0]*T]*alpha
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
