import numpy as np
from util_sto import ProductionStoPlanModel

np.random.seed(102)

def run_gurobi_solver(n, m, m_a, T, x_a, R_a, R_fix, a, A, b, c, h, k, p, d, q):
    
    I_A = range(m_a)
    I_minus_I_A = [i for i in range(m) if i not in I_A]  
    A_l = [[[np.random.randint(0, m_a*A[i][t]) for _ in range(q)] for t in range(T)] for i in range(m)]
    
    # create and build model
    productionStoPlanModel = ProductionStoPlanModel(n, T, m, q, m_a, I_A, I_minus_I_A, R_fix, a, p, d, A, A_l, h, k, b, c, R_a, x_a)
    productionStoPlanModel.build_model()
    
    # run diverse experiment
    # TODO : create a function run_simulation with filename and number of experiment
    num_exp = 100
    results = {}

    # save the solution if optimal
    if  productionStoPlanModel.optimize():
        predictive_CM_sa = productionStoPlanModel.model.objVal
    
        real_CM_avg_sa = productionStoPlanModel.simulate_schedule(num_exp)
        productionStoPlanModel.save_results("results_model")
        #set epsilon to 0 , if you don't want to use the model with non-anticipativity
        real_CM_avg_sa_na_rolling = productionStoPlanModel.simulate_rolling_schedule(num_exp, epsilon=1.1) 
        real_CM_avg_sa_rolling = productionStoPlanModel.simulate_rolling_schedule(num_exp, epsilon=0) 
        productionStoPlanModel.reoptimize_subject_to_non_anticipativity(f_star= predictive_CM_sa, epsilon= 1.1)
        real_CM_avg_sa_na = productionStoPlanModel.simulate_schedule(num_exp) 

        results["Contribution margin predicted by sampling approximatione model without non-anticipativity"] = predictive_CM_sa
        results["Contribution margin predicted by sampling approximatione model with non-anticipativity"] = predictive_CM_sa
        results["Average realized contribution margin of sampling approximation without non-anticipativity"] = real_CM_avg_sa
        results["Average realized contribution margin of sampling approximation with non-anticipativity"] = real_CM_avg_sa_na
        results["Average realized contribution margin of rolling sampling approximation with non-anticipativity"] = real_CM_avg_sa_na_rolling
        results["Average realized contribution margin of rolling sampling approximation without non-anticipativity"] = real_CM_avg_sa_rolling
     
    return results


    
