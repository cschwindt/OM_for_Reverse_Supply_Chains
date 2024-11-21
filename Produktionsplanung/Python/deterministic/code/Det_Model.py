import gdxpds
import os
import numpy as np
import gurobipy as gp
from gurobipy import GRB


# Sets and Parameters
I = 3  # Number of production factors
J = 5  # Number of product groups
T = 4  # Total number of periods including the fictitious period
L = 100  # Number of samples

# Cost of production factors
cost = [0.1, 0.1, 0.2]

# Holding costs
h = [0.1, 0.2, 0.5, 0.2, 0.1]

# Initial inventory
xa = [0, 5, 10, 0, 5]

p_max = [10, 20, 15, 20, 5]

d_max = [30, 50, 40, 20, 40]

T_actual = T - 1

mu = np.array([
    [1.5, 1.0, 0.75],
    [1.7, 0.5, 1.75],
    [1.0, 0.75, 1.25],
    [0.5, 0.85, 0.75],
    [1.8, 0.9, 0.75]
])

sigma = np.array([
    [0.05, 0.05, 0.025],
    [0.19, 0.075, 0.175],
    [1.25, 0.5, 1.5],
    [0.95, 0.55, 1.75],
    [1.2, 0.8, 1.75]
]) * 5

coeff_a = np.array([
    [4, 6, 4, 5, 3],
    [2, 0, 2, 1, 0],
    [0, 1, 2, 1, 1]
])

# Capacities
R = np.array([
    [float('inf'), 50, float('inf'), 0],
    [30, 32, 26, 0],
    [50, 53, 47, 0]
])

# Production costs
k = np.array([20 * sum(coeff_a[i][j] * cost[i] for i in range(I)) for j in range(J)])


os.environ['GAMS_DIR'] = r"C:\GAMS\win64\47"
# Initialize GDXPDS with the GAMS directory
gdxpds.load_gdxcc(gams_dir=os.environ['GAMS_DIR'])
gdx_file_path = r"C:\Users\ma92\Desktop\Python\Research\real_sl.gdx"
gams_real_sl_df = gdxpds.to_dataframe(gdx_file_path, symbol_name='real_sl', old_interface=False)

real_sl = np.empty((J, T, 3))
for i in range(len(gams_real_sl_df)):
    j = int(gams_real_sl_df["j"][i].replace('j', '')) - 1
    t = int(gams_real_sl_df["t"][i].replace('t', '')) - 1
    index = int(gams_real_sl_df["index"][i].replace('s', '')) - 1
    # if t < 3:
    real_sl[j][t][index] = gams_real_sl_df["Value"][i]


def simulate_contribution_margin(p_opt, y_opt, xa, real_sl, d_max, p_max, k, h, num_simulations=3):
    real_DBs = []

    for sim in range(num_simulations):

        np.random.seed(sim)

        real_d = np.zeros((J, T_actual))
        for j in range(J):
            for t in range(T_actual):
                real_d[j, t] = real_sl[j, t, sim] * d_max[j] * (1 - p_opt[j, t] / p_max[j])

        real_x = np.zeros((J, T))
        real_z = np.zeros((J, T_actual))
        real_x[:, 0] = xa

        for t in range(T_actual):
            for j in range(J):
                real_z[j, t] = min(real_x[j, t] + y_opt[j, t], real_d[j, t])
                real_x[j, t + 1] = real_x[j, t] + y_opt[j, t] - real_z[j, t]

        total_DB = sum(
            p_opt[j, t] * real_z[j, t]
            - k[j] * y_opt[j, t]
            - h[j] * real_x[j, t + 1]
            for j in range(J) for t in range(T_actual)
        )

        real_DBs.append(total_DB)

    real_DB_avg = np.mean(real_DBs)
    return real_DB_avg

def simulate_rolling_horizon(m, x, y, z, p, xa, real_sl, d_max, p_max, k, h, J, T, I, num_experiments=1):
    real_DBs_rolling = []

    for sim in range(num_experiments):
        # Reset variable bounds for each simulation
        for j in range(J):
            x[j, 0].LB = xa[j]
            x[j, 0].UB = xa[j]

            for t in range(T):
                p[j, t].LB = 0
                p[j, t].UB = p_max[j]

                y[j, t].LB = 0
                y[j, t].UB = GRB.INFINITY

                z[j, t].LB = 0
                z[j, t].UB = GRB.INFINITY

            for t in range(1, T + 1):
                x[j, t].LB = 0
                x[j, t].UB = GRB.INFINITY

        #real_s = real_sl[:, :, sim]

        total_DB = 0

        for tPrime in range(T):
            m.Params.TimeLimit = 10

            m.optimize()

            # Fix variables at time tPrime based on realized demand
            for j in range(J):
                # Retrieve the optimized values
                p_value = p[j, tPrime].X
                y_value = y[j, tPrime].X
                x_value_t = x[j, tPrime].X

                realized_demand = hat_s[j, tPrime] * d_max[j] * (1 - p_value / p_max[j])

                z_value = min(x_value_t + y_value, realized_demand)

                # Fix sales variable at tPrime
                z[j, tPrime].LB = z_value
                z[j, tPrime].UB = z_value

                # Update inventory for tPrime + 1
                x_value = x_value_t + y_value - z_value
                x[j, tPrime + 1].LB = x_value
                x[j, tPrime + 1].UB = x_value

                # Fix price and production variables at tPrime
                p[j, tPrime].LB = p_value
                p[j, tPrime].UB = p_value

                y[j, tPrime].LB = y_value
                y[j, tPrime].UB = y_value

                total_DB += (
                        p_value * z_value
                        - k[j] * y_value
                        - h[j] * x_value
                )

            # Remove constraints for time tPrime
            for i in range(I):
                con = m.getConstrByName(f"capacity_{i}_{tPrime}")
                if con:
                    m.remove(con)

            for j in range(J):
                con = m.getConstrByName(f"inventory_balance_{j}_{tPrime}")
                if con:
                    m.remove(con)
                con = m.getConstrByName(f"demand_constraint_{j}_{tPrime}")
                if con:
                    m.remove(con)

            m.update()

        real_DBs_rolling.append(total_DB)

    real_DB_avg_rolling = np.mean(real_DBs_rolling)
    return real_DB_avg_rolling

# model
m = gp.Model("Deterministic_MPS")

# Variables
p = m.addVars(J, T_actual, lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="p")
y = m.addVars(J, T, lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="y")
z = m.addVars(J, T, lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="z")
x = m.addVars(J, T + 1, lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="x")

# upper bounds for prices
for j in range(J):
    for t in range(T_actual):
        m.addConstr(p[j, t] <= p_max[j], name=f"price_upper_bound_{j}_{t}")

# no production and sales in fictitious period
for j in range(J):
    m.addConstr(y[j, T_actual] == 0, name=f"no_production_{j}_T")
    m.addConstr(z[j, T_actual] == 0, name=f"no_sales_{j}_T")

# Initial inventory
for j in range(J):
    m.addConstr(x[j, 0] == xa[j], name=f"initial_inventory_{j}")

# Objective function
m.setObjective(
    gp.quicksum(
        p[j, t] * z[j, t] - k[j] * y[j, t] - h[j] * x[j, t + 1]
        for j in range(J) for t in range(T_actual)
    ),
    GRB.MAXIMIZE
)

# Capacity constraints
for i in range(I):
    for t in range(T_actual):
        m.addConstr(
            gp.quicksum(coeff_a[i][j] * y[j, t] for j in range(J)) <= R[i][t],
            name=f"capacity_{i}_{t}"
        )

# Inventory balance constraints
for j in range(J):
    for t in range(T):
        m.addConstr(
            x[j, t + 1] == x[j, t] + y[j, t] - z[j, t],
            name=f"inventory_balance_{j}_{t}"
        )

# Demand constraints
for j in range(J):
    for t in range(T_actual):
        m.addConstr(
            z[j, t] <= mu[j, t] * d_max[j] * (1 - p[j, t] / p_max[j]),
            name=f"demand_constraint_{j}_{t}"
        )

m.Params.NonConvex = 2
m.Params.TimeLimit = 10
m.Params.MIPGap = 0

m.optimize()

if m.status == GRB.OPTIMAL or m.status == GRB.TIME_LIMIT:
    # Retrieve optimized values
    p_opt = np.array([[p[j, t].X for t in range(T_actual)] for j in range(J)])
    x_opt = np.array([[x[j, t].X for t in range(T + 1)] for j in range(J)])
    y_opt = np.array([[y[j, t].X for t in range(T)] for j in range(J)])
    z_opt = np.array([[z[j, t].X for t in range(T)] for j in range(J)])

    print(f"Optimal contribution margin: {m.ObjVal}")

    # Simulated contribution margin
    real_DB_avg = simulate_contribution_margin(p_opt, y_opt, xa, real_sl, d_max, p_max, k, h, num_simulations=3)
    print("Average Realized Contribution Margin:", real_DB_avg)


real_DB_avg_rolling = simulate_rolling_horizon(
    m, x, y, z, p, xa, real_sl, d_max, p_max, k, h, J, T_actual, T, I, num_experiments=1)

print("Average Realized Contribution Margin (Rolling Horizon):", real_DB_avg_rolling)
