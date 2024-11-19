import gurobipy as gp
from gurobipy import GRB
import math
import numpy as np
import pandas as pd
from scipy.special import erf

# Fehlerfunktion (CDF der Normalverteilung)
def normal_cdf(x):
        return 0.5 * (1 + erf(x / np.sqrt(2)))

def normal_p(d, mu_d, sigma_d, d_max):
    if d == 0:
        pD = normal_cdf((d + 0.5 - mu_d) / sigma_d)
    # Berechnung für ord(d) > 1 und ord(d) < card(d) (zwischen den Bestellmengen)
    elif 0 < d < d_max:
        pD = normal_cdf((d + 0.5 - mu_d) / sigma_d) - normal_cdf((d - 0.5 - mu_d) / sigma_d)
    # Berechnung für ord(d) = card(d) (letzte Bestellmenge)
    elif d == d_max:
        pD = 1.0 - normal_cdf((d - 0.5 - mu_d) / sigma_d)
    return pD

def binomial_p(d,dmax,par_pD):
    return math.comb(dmax, d) * (par_pD ** d) * ((1 - par_pD) ** (dmax - d))


def reward(val_x , a , pi , h ,k,v,availabilities,ymax,par_pY,mu_y,sigma_y):
    """Compute reward for state s and action a"""
    if par_pY > 0.0:
         order_cost = pi * sum(binomial_p(y,ymax, par_pY) * min(a, y) for y in availabilities)
    elif mu_y > 0.0:
         order_cost = pi * sum(normal_p(y, mu_y, sigma_y,ymax) * min(a, y) for y in availabilities)
    holding_cost = h * max(0, val_x)
    fixed_order_cost = k if a > 0 else 0
    stockout_cost = v * max(0, -val_x)
    return -(order_cost + holding_cost + fixed_order_cost + stockout_cost)


def transition_prob(val_x, a, val_x_prime,availabilities,demands,xmax,ymax, par_pY,dmax,par_pD, mu_d, sigma_d, mu_y, sigma_y):
    if par_pD >0.0 and mu_y > 0.0:
           return sum(
            normal_p(y, mu_y, sigma_y,ymax)  * binomial_p(d,dmax,par_pD)
            for y in availabilities
            for d in demands
            if val_x_prime == min(max(val_x, 0) + min(a, y) - d, xmax)
        )
    elif par_pD > 0.0 and par_pY > 0.0:
        return sum(
            binomial_p(y,ymax, par_pY) * binomial_p(d,dmax,par_pD)
            for y in availabilities
            for d in demands
            if val_x_prime == min(max(val_x, 0) + min(a, y) - d, xmax)
        )
    elif par_pY >0.0 and mu_d > 0.0:
        return sum(
                binomial_p(y,ymax, par_pY)* normal_p(d,mu_d,sigma_d,dmax)
                for y in availabilities
                for d in demands
                if val_x_prime == min(max(val_x, 0) + min(a, y) - d, xmax)
            )
    elif mu_y >0.0 and mu_d > 0.0:
        return sum(
                normal_p(y, mu_y, sigma_y,ymax)*normal_p(d,mu_d,sigma_d,dmax)
                for y in availabilities
                for d in demands
                if val_x_prime == min(max(val_x, 0) + min(a, y) - d, xmax)
            )


def run_gurobi_solver(params):
        # Gurobi-Modell erstellen
        dmax = int(params["dmax"])
        xmax = int(params["xmax"])
        ymax = int(params["ymax"])
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
        states = range(-dmax, xmax + 1)          # State indices for inventory levels
        actions = range(min(ymax,xmax) +1)       # Action indices for order quantities
        demands = range(dmax + 1)                # Demand levels
        availabilities = range(ymax + 1)         # Availability levels

        model = gp.Model("InventoryOptimization")
        sigma = model.addVars(states,actions, vtype=GRB.CONTINUOUS, name="sigma(x,q)")

        #define admissibale actions
        A = {}
        for x in states:
            # Finde alle Aktionen q, die die Bedingung q <= xmax - s + dmax erfüllen
            valid_actions = [q for q in actions if q <= xmax - x + dmax]
            A[x] = valid_actions
        # Objective: Maximize expected reward
        model.setObjective(gp.quicksum(reward(x, q , pi , h ,k,v,availabilities,ymax, par_pY,mu_y,sigma_y)*sigma[x,q] 
                                       for q in A[x] for x in states), GRB.MAXIMIZE)
        # Constraints
        model.addConstr(gp.quicksum(
                sigma[x,q] for q in A[x] for x in states
            ) ==1.0)

        for xprime in states:      
            # Bellman constraint
            model.addConstr(gp.quicksum(sigma[xprime, q]for q in A[xprime]) == gp.quicksum(
                    transition_prob(x, q, xprime,availabilities,demands,xmax,ymax, par_pY,dmax,par_pD, mu_d, sigma_d, mu_y, sigma_y)*sigma[x,q]
                        for q in A[x] for x in states
                ))

        for x in states:
            for q in A[x]:
                model.addConstr(sigma[x,q] >=0.0)
        # Solve the model
        model.optimize()

        # Ergebnisse verarbeiten
        results = {
            "Inventory Level": [],
            "Order Quantity": [],
            "Probability": []
        }
        performance_results = { }
        # save the results 
        for x in states:
            max_sum = 0.0
            for q in A[x]:
              if sigma[x,q].x > 0.0:
                  q_best = q
                  max_sum = sigma[x,q].x   
            results["Inventory Level"].append(x)
            results["Order Quantity"].append(q_best)
            results["Probability"].append(round(max_sum, 10))
        
        # Get the objective value after solving (minimized cost per period)
        performance_results["Expected total cost per period"] = round(-model.objVal,4)
        performance_results["Expected inventory level"] = round(sum(x*sum(sigma[x, q].x for q in A[x] ) for x in states if x > 0),4)
        max_inv = np.max([x_val for x_val in states if (x_val >= 0 and sum(sigma[x_val,q].x for q in A[x_val])>0)])
        performance_results["Maximum inventory level"] = round(max_inv,4)
        exp_short = sum(-x*sum(sigma[x,q].x for q in A[x]) for x in states if x < 0 )
        performance_results["Expected shortage"] = exp_short
        max_short = max(-x for x in states if (x<0 and sum(sigma[x,q].x for q in A[x] if sigma[x,q].x>0)) )
        performance_results["Maximum shortage"] = max_short
        exp_ord_quant = sum(q * sigma[x, q].x for x in states for q in A[x])
        performance_results["Expected order quantity"] = exp_ord_quant
        
        return pd.DataFrame(results) ,performance_results




