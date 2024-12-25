from models_det import ProductionDetPlanModel


def run_gurobi_solver(n, m, m_A, T, x_a, R_a, R_fix, a, A, b, c, h, k, p, d):
    
    I_A = range(m_A)
    I_minus_I_A = [i for i in range(m) if i not in I_A] 
    # create and build model
    productionDetPlanModel = ProductionDetPlanModel(n, T, m, m_A, I_A, I_minus_I_A, R_fix, a, p, d, A, h, k, b, c, R_a,
                                                    x_a)
    productionDetPlanModel.build_model()

    results = {}
    # evaluate predictive master production schedule
    if productionDetPlanModel.optimize():
        productionDetPlanModel.save_results("results_model")
        predictive_CM = productionDetPlanModel.model.objVal
        real_CM_avg_pred = productionDetPlanModel.simulate_schedule(num_sim=100)
        productionDetPlanModel.reoptimize_subject_to_non_anticipativity(f_star=predictive_CM, epsilon=0.1)
        productionDetPlanModel.save_results("results_model_na")
        real_CM_avg_pred_na = productionDetPlanModel.simulate_schedule(num_sim=100)
        # set epsilon to 0, if you don't want to use the model with non-anticipativity
        real_CM_avg_rolling = productionDetPlanModel.simulate_rolling_schedule(num_sim=100, epsilon=0)
        real_CM_avg_rolling_na = productionDetPlanModel.simulate_rolling_schedule(num_sim=100, epsilon=0.1)

        results["Contribution margin predicted by expected value model without non-anticipativity"] = predictive_CM
        results["Contribution margin predicted by expected value model with non-anticipativity"] = predictive_CM
        results["Average realized contribution margin of predictive schedule without non-anticipativity"] = \
            real_CM_avg_pred
        results["Average realized contribution margin of predictive schedule with non-anticipativity"] = \
            real_CM_avg_pred_na
        results["Average realized contribution margin of rolling schedule without non-anticipativity"] = \
            real_CM_avg_rolling
        results["Average realized contribution margin of rolling schedule with non-anticipativity"] = \
            real_CM_avg_rolling_na
    else:
        print("Could not determine predictive master production schedule")

    return results


    
