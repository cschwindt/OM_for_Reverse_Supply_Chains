import numpy as np


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
