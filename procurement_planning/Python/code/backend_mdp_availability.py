import gurobipy as gp
from gurobipy import GRB
import math
import numpy as np
import pandas as pd
from scipy.special import erf
from main_mdp_availability import pY


# cumulative density function of standard normal distribution
def normal_cdf(x):
    return 0.5 * (1 + erf(x / np.sqrt(2)))


# cumulative density function of discretized normal distribution
def normal_p(d, mu_d, sigma_d, d_max):
    if d == 0:
        pD = normal_cdf((d + 0.5 - mu_d) / sigma_d)
    # computation for d > 0 und d < d_max
    elif 0 < d < d_max:
        pD = normal_cdf((d + 0.5 - mu_d) / sigma_d) - normal_cdf((d - 0.5 - mu_d) / sigma_d)
    # computation for d = d_max
    elif d == d_max:
        pD = 1.0 - normal_cdf((d - 0.5 - mu_d) / sigma_d)
    return pD


# cumulative density function of binomial distribution
def binomial_p(d, d_max, par_pD):
    return math.comb(d_max, d) * (par_pD ** d) * ((1 - par_pD) ** (d_max - d))


def reward(val_x, a, pi, h, k, v, availabilities, y_max, par_pY, mu_y, sigma_y):
    # compute reward for state s and action a
    if par_pY > 0.0:
        order_cost = pi * sum(binomial_p(y, y_max, par_pY) * min(a, y) for y in availabilities)
    elif mu_y > 0.0:
        order_cost = pi * sum(normal_p(y, mu_y, sigma_y, y_max) * min(a, y) for y in availabilities)
    holding_cost = h * max(0, val_x)
    fixed_order_cost = k if a > 0 else 0
    stockout_cost = v * max(0, -val_x)
    return -(order_cost + holding_cost + fixed_order_cost + stockout_cost)


def transition_prob(val_x, a, val_x_prime, availabilities, demands, x_max, y_max, par_pY, d_max, par_pD, mu_d, sigma_d,
                    mu_y, sigma_y):
    if par_pD > 0.0 and mu_y > 0.0:
        return sum(
            normal_p(y, mu_y, sigma_y, y_max) * binomial_p(d, d_max, par_pD)
            for y in availabilities for d in demands if val_x_prime == min(max(val_x, 0) + min(a, y) - d, x_max))
    elif par_pD > 0.0 and par_pY > 0.0:
        return sum(
            binomial_p(y, y_max, par_pY) * binomial_p(d, d_max, par_pD)
            for y in availabilities for d in demands
            if val_x_prime == min(max(val_x, 0) + min(a, y) - d, x_max)
        )
    elif par_pY > 0.0 and mu_d > 0.0:
        return sum(
                binomial_p(y, y_max, par_pY) * normal_p(d, mu_d, sigma_d, d_max) for y in availabilities
                for d in demands if val_x_prime == min(max(val_x, 0) + min(a, y) - d, x_max))
    elif mu_y > 0.0 and mu_d > 0.0:
        return sum(
                normal_p(y, mu_y, sigma_y, y_max)*normal_p(d, mu_d, sigma_d, d_max) for y in availabilities
                for d in demands if val_x_prime == min(max(val_x, 0) + min(a, y) - d, x_max))


def run_gurobi_solver(params):
    # Gurobi-Modell erstellen
    d_max = int(params["d_max"])
    x_max = int(params["x_max"])
    y_max = int(params["y_max"])
    pi = float(params["pi"])
    h = float(params["h"])
    k = float(params["k"])
    par_pY = float(params["par_pY"])
    par_pD = float(params["par_pD"])
    mu_d = float(params["mu_D"])
    mu_y = float(params["mu_Y"])
    sigma_d = float(params["sigma_D"])
    sigma_y = float(params["sigma_Y"])
    v = float(params["v"])
    states = range(-d_max, x_max + 1)        # State indices for inventory levels
    actions = range(min(y_max, x_max) + 1)   # Action indices for order quantities
    demands = range(d_max + 1)               # Demand levels
    availabilities = range(y_max + 1)        # Availability levels

    model = gp.Model("InventoryOptimization")
    model.setParam(GRB.Param.OptimalityTol, 1.0e-9)
    model.setParam(GRB.Param.FeasibilityTol, 1.0e-9)
    sigma = model.addVars(states, actions, vtype=GRB.CONTINUOUS, name="sigma(x,q)")

    # define feasible actions
    A = {}
    for x in states:
        # determine all actions q satisfying condition q ≤ x_max - s + d_max
        valid_actions = [q for q in actions if q <= x_max - x + d_max]
        A[x] = valid_actions
    # objective: maximize expected reward
    model.setObjective(gp.quicksum(reward(x, q, pi, h, k, v, availabilities, y_max, par_pY, mu_y, sigma_y)*sigma[x, q]
                                   for q in A[x] for x in states), GRB.MAXIMIZE)
    # constraints
    model.addConstr(gp.quicksum(
            sigma[x, q] for q in A[x] for x in states) == 1.0, name="probs_sum_to_one")

    for x_prime in states:
        # Bellman constraint
        model.addConstr(gp.quicksum(sigma[x_prime, q] for q in A[x_prime]) == gp.quicksum(
                transition_prob(x, q, x_prime, availabilities, demands, x_max, y_max, par_pY, d_max, par_pD, mu_d,
                                sigma_d, mu_y, sigma_y)*sigma[x, q]
                for q in A[x] for x in states), name="functional_equation")

    # solve the model
    model.optimize()

    # process the results
    results = {
        "Inventory Level": [],
        "Order Quantity": [],
        "Probability": []
    }
    performance_results = {}
    # save the results
    for x in states:
        max_sum = 0.0
        for q in A[x]:
            if sigma[x, q].x > 0.0:
                q_best = q
                max_sum = sigma[x, q].x
        results["Inventory Level"].append(x)
        results["Order Quantity"].append(q_best)
        results["Probability"].append(round(max_sum, 10))

    # get the optimal objective function value (minimal cost per period)
    performance_results["Expected total cost per period"] = round(-model.objVal, 4)
    performance_results["Expected inventory level"] = round(sum(x*sum(sigma[x, q].x for q in A[x]) for x in states
                                                                if x > 0), 4)
    max_inv = np.max([x_val for x_val in states if (x_val >= 0 and sum(sigma[x_val, q].x for q in A[x_val]) > 0)])
    performance_results["Maximum inventory level"] = round(max_inv, 4)
    exp_short = sum(-x*sum(sigma[x, q].x for q in A[x]) for x in states if x < 0)
    performance_results["Expected shortage"] = exp_short
    max_short = max(-x for x in states if (x < 0 and sum(sigma[x, q].x for q in A[x] if sigma[x, q].x > 0)))
    performance_results["Maximum shortage"] = max_short
    exp_ord_quant = sum(q * sigma[x, q].x for x in states for q in A[x])
    performance_results["Expected order quantity"] = exp_ord_quant
    exp_sup_quant = sum(pY(y) * min(a, y) * sigma[s, a].x for s in states for a in actions for y in availabilities)
    performance_results["Expected supply quantity"] = exp_sup_quant

    return pd.DataFrame(results), performance_results
