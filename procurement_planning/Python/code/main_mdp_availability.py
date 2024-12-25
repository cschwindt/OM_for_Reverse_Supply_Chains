import gurobipy as gp
from gurobipy import GRB
import math
import numpy as np

# define parameters
d_max = 10    # maximum demand
x_max = 20    # maximum inventory level
y_max = 15    # maximum availability
pi = 5        # unit variable procurement cost
h = 1         # unit holding cost
k = 2         # fixed procurement cost
v = 20        # unit storage cost
par_pD = 0.4  # parameter p in distribution of demand
par_pY = 0.3  # parameter p in distribution of availability


states = range(-d_max, x_max + 1)       # State indices for inventory levels
actions = range(min(y_max, x_max) + 1)  # Action indices for order quantities
demands = range(d_max + 1)              # Demand levels
availabilities = range(y_max + 1)       # Availability levels

# define feasible actions
A = {}
for x in states:
    # determine all actions q satisfying condition q ≤ x_max - s + d_max
    valid_actions = [q for q in actions if q <= x_max - x + d_max]
    A[x] = valid_actions


# create the model
model = gp.Model("InventoryOptimization")
model.setParam(GRB.Param.OptimalityTol, 1.0e-9)
model.setParam(GRB.Param.FeasibilityTol, 1.0e-9)

# variables
sigma = model.addVars(states, actions, vtype=GRB.CONTINUOUS, name="sigma(x,q)")


def pD(d):
    # probability of demand level d
    return math.comb(d_max, d) * (par_pD ** d) * ((1 - par_pD) ** (d_max - d))


def pY(y):
    # probability of availability level y
    return math.comb(y_max, y) * (par_pY ** y) * ((1 - par_pY) ** (y_max - y))


def reward(s, a):
    # compute reward for state s and action a
    val_x = s   # Inventory level encoded by s
    order_cost = pi * sum(pY(y) * min(a, y) for y in availabilities)
    holding_cost = h * max(0, val_x)
    fixed_order_cost = k if a > 0 else 0
    stockout_cost = v * max(0, -val_x)
    return -(order_cost + holding_cost + fixed_order_cost + stockout_cost)


def transition_prob(s, a, s_prime):
    # compute transition probability from state s to s_prime given action a
    val_x = s
    val_x_prime = s_prime
    return sum(
        pY(y) * pD(d)
        for y in availabilities
        for d in demands
        if val_x_prime == min(max(val_x, 0) + min(a, y) - d, x_max)
    )


# objective: maximize expected reward
model.setObjective(gp.quicksum(reward(x, q)*sigma[x, q] for q in A[x] for x in states), GRB.MAXIMIZE)

# constraints
model.addConstr(gp.quicksum(
        sigma[x, q] for q in A[x] for x in states) == 1.0, name="probs_sum_to_one")

for x_prime in states:
    # Bellman constraint
    model.addConstr(gp.quicksum(sigma[x_prime, q]for q in A[x_prime]) == gp.quicksum(
            transition_prob(x, q, x_prime) * sigma[x, q] for q in A[x] for x in states), name="balance_equations")

# solve the model
model.optimize()

if model.status == GRB.OPTIMAL:
    # get the optimal objective function value (minimal cost per period)
    total_cost_per_period = model.objVal
    exp_inv = sum(x*sum(sigma[x, q].x for q in A[x]) for x in states if x > 0)
    print(f"Expected inventory level: {exp_inv:.4f}")
    # maximal inventory 
    max_inv = np.max([x_val for x_val in states if (x_val >= 0 and sum(sigma[x_val, q].x for q in A[x_val]) > 0)])
    print(f"Maximal inventory level: {max_inv:.4f}")
    # expected shortage 
    exp_ord_quant = sum(a * sigma[s, a].x for s in states for a in actions)
    print(f"Expected order quantity: {exp_ord_quant:.4f}")
    # maximal shortage
    exp_short = sum(-x*sum(sigma[x, q].x for q in A[x]) for x in states if x < 0)
    print(f"Expected shortage cost: {exp_short:.4f}")
    max_short = max(-x for x in states if (x < 0 and sum(sigma[x, q].x for q in A[x] if sigma[x, q].x > 0)))
    print(f"Maximal shortage: {max_short:.4f}")
    # expected total cost
    expected_costs = sum(reward(s, a) * sigma[s, a].x for s in states for a in actions)
    print(f"Expected cost: {-expected_costs:.4f}")
    # write the results to a file
    with open("policy_availability_model_python.txt", "w") as f:
        f.write(f'Optimal policy for availability model (Gurobi solver) \n\n')
        f.write(f"Inventory level | Order quantity | Probability\n")
        f.write(f'===============================================\n')
        for x in states:
            max_sum = 0
            for q in A[x]:
                if max_sum < sigma[x, q].x:
                    q_best = q
                    max_sum = sigma[x, q].x
            f.write(f"         {x:>6} |         {q_best:>6} | {max_sum:.10f}\n")
        f.write(f'\nExpected total cost per period: {-total_cost_per_period:.4f}\n')
        f.write(f'Expected inventory level: {exp_inv:.4f}\n')
        f.write(f'Maximum inventory level: {max_inv}\n')
        f.write(f'Expected shortage: {exp_short:.4f}\n')
        f.write(f'Maximum shortage: {max_short:.4f}\n')
        f.write(f'Expected order quantity: {exp_ord_quant:.4f}\n')

else:
    print("Model could not be solved to optimality.")
