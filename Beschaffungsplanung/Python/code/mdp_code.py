import gurobipy as gp
from gurobipy import GRB
import math
import numpy as np

# Define Parameter
dmax = 10    # maximum demand
xmax = 20    # maximum inventory level
ymax = 15    # maximum avaibility
pi = 5       # unit variable procurement cost
h = 1        # unit holding cost
k = 0        # fixed procurement cost
v = 20       # unit storage cost
par_pD = 0.4 # parameter p in distribution of demand
par_pY = 0.3 # parameter p in distribution of yield


states = range(-dmax ,xmax + 1)          # State indices for inventory levels
actions = range(min(ymax,xmax) +1)       # Action indices for order quantities
demands = range(dmax + 1)                # Demand levels
availabilities = range(ymax + 1)         # Availability levels

#define admissibale actions
A = {}
for x in states:
    # Finde alle Aktionen q, die die Bedingung q <= xmax - s + dmax erfüllen
    valid_actions = [q for q in actions if q <= xmax - x + dmax]
    A[x] = valid_actions


# Create the model
model = gp.Model("InventoryOptimization")

# Variables
sigma = model.addVars(states,actions, vtype=GRB.CONTINUOUS, name="sigma(x,q)")

def pD(d):
    """Probability of demand level d"""
    return math.comb(dmax, d) * (par_pD ** d) * ((1 - par_pD) ** (dmax - d))

def pY(y):
    """Probability of availability level y"""
    return math.comb(ymax, y) * (par_pY ** y) * ((1 - par_pY) ** (ymax - y))

def reward(s, a):
    """Compute reward for state s and action a"""
    val_x = s   # Inventory level encoded by s
    order_cost = pi * sum(pY(y) * min(a, y) for y in availabilities)
    holding_cost = h * max(0, val_x)
    fixed_order_cost = k if a > 0 else 0
    stockout_cost = v * max(0, -val_x)
    return -(order_cost + holding_cost + fixed_order_cost + stockout_cost)

def transition_prob(s, a, s_prime):
    """Compute transition probability from state s to s_prime given action a"""
    val_x = s
    val_x_prime = s_prime
    return sum(
        pY(y) * pD(d)
        for y in availabilities
        for d in demands
        if val_x_prime == min(max(val_x, 0) + min(a, y) - d, xmax)
    )

# Objective: Maximize expected reward
model.setObjective(gp.quicksum(reward(x, q)*sigma[x,q] for q in A[x] for x in states), GRB.MAXIMIZE)

# Constraints
model.addConstr(gp.quicksum(
        sigma[x,q] for q in A[x] for x in states
    ) ==1.0)

for xprime in states:      
    # Bellman constraint
    model.addConstr(gp.quicksum(sigma[xprime, q]for q in A[xprime]) == gp.quicksum(
            transition_prob(x, q, xprime) * sigma[x,q]
                for q in A[x] for x in states
        ))

for x in states:
    for q in A[x]:
        model.addConstr(sigma[x,q] >=0.0)

# Solve the model
model.optimize()

if model.status == GRB.OPTIMAL:
    # Get the objective value after solving (minimized cost per period)
    total_cost_per_period = model.objVal
    exp_inv = sum(x*sum(sigma[x, q].x for q in A[x] ) for x in states if x > 0)
    print(f"Erwarteter Lagerbestand: {exp_inv:.4f}")
    # maximal inventory 
    max_inv = np.max([x_val for x_val in states if (x_val >= 0 and sum(sigma[x_val,q].x for q in A[x_val])>0)])
    print(f"Maximaler Bestand: {max_inv:.4f}")
    # expected shortage 
    exp_ord_quant = sum(a * sigma[s, a].x for s in states for a in actions)
    print(f"Erwartete Bestellmenge: {exp_ord_quant:.4f}")
    #maximal shortage
    exp_short = sum(-x*sum(sigma[x,q].x for q in A[x]) for x in states if x < 0 )
    print(f"Erwartete Fehlmengekosten: {exp_short:.4f}")
    max_short = max(-x for x in states if (x<0 and sum(sigma[x,q].x for q in A[x] if sigma[x,q].x>0)) )
    print(f"maximale Fehlmenge: {max_short:.4f}")
    # expected total cost
    expected_costs = sum(reward(s, a) * sigma[s, a].x for s in states for a in actions)
    print(f"Erwartete Kosten: {-expected_costs:.4f}")
    # Write the results to a file
    with open("poilic_avaibility_model_python.txt", "w") as f:
        f.write(f'optimal policy for avaibility model (Gurobi solver) \n\n')
        f.write(f"Inventory level | Order quantity | Probability\n")
        f.write(f'===============================================\n')
        for x in states:
            max_sum = 0
            for q in A[x]:
              if max_sum < sigma[x,q].x:
                  q_best = q
                  max_sum = sigma[x,q].x
            f.write(f"         {x:>6} |         {q_best:>6} | {max_sum:.10f}\n")
        f.write(f'\nExpected total cost per period: {-total_cost_per_period:.4f}\n')
        f.write(f'Expected inventory level: {exp_inv:.4f}\n')
        f.write(f'Maximum inventory level: {max_inv}\n')
        f.write(f'Expected shortage: {exp_short:.4f}\n')
        f.write(f'Maximum shortage: {max_short:.4f}\n')
        f.write(f'Expected order quantity: {exp_ord_quant:.4f}\n')

else:
    print("Model did not solve to optimality.")
