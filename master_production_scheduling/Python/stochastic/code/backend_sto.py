import numpy as np
from models_sto import ProductionStoPlanModel

np.random.seed(102)


def run_gurobi_solver(n, m, m_a, T, x_a, R_a, R_fix, a, A, b, c, h, k, p, d, q):
    
    I_A = range(m_a)
    I_minus_I_A = [i for i in range(m) if i not in I_A]  
    A_l = [[[np.random.randint(0, m_a*A[i][t]) for _ in range(q)] for t in range(T)] for i in range(m)]
    
    # create and build model
    productionStoPlanModel = ProductionStoPlanModel(n, T, m, q, m_a, I_A, I_minus_I_A, R_fix, a, p, d, A, A_l, h, k, b,
                                                    c, R_a, x_a)
    productionStoPlanModel.build_model()

    results = {}
    # evaluate predictive master production schedule
    if productionStoPlanModel.optimize():
        productionStoPlanModel.save_results("results_model")
        predictive_CM = productionStoPlanModel.model.objVal
        real_CM_avg_pred = productionStoPlanModel.simulate_schedule(num_sim=100)
        productionStoPlanModel.reoptimize_subject_to_non_anticipativity(f_star=predictive_CM, epsilon=1.1)
        productionStoPlanModel.save_results("results_model_na")
        real_CM_avg_pred_na = productionStoPlanModel.simulate_schedule(num_sim=100)
        # set epsilon to 0, if you don't want to use the model with non-anticipativity
        real_CM_avg_rolling = productionStoPlanModel.simulate_rolling_schedule(num_sim=100, epsilon=0)
        real_CM_avg_rolling_na = productionStoPlanModel.simulate_rolling_schedule(num_sim=100, epsilon=1.1)

        results["Contribution margin predicted by sampling approximation model without non-anticipativity"] \
            = predictive_CM
        results["Contribution margin predicted by sampling approximation model with non-anticipativity"] \
            = predictive_CM
        results["Average realized contribution margin of sampling approximation without non-anticipativity"] \
            = real_CM_avg_pred
        results["Average realized contribution margin of sampling approximation with non-anticipativity"] \
            = real_CM_avg_pred_na
        results["Average realized contribution margin of rolling sampling approximation without non-anticipativity"] \
            = real_CM_avg_rolling
        results["Average realized contribution margin of rolling sampling approximation with non-anticipativity"] \
            = real_CM_avg_rolling_na
    else:
        print("Could not determine predictive master production schedule")
     
    return results


    
