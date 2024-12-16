import numpy as np
from util import ProductionDetPlanModel

np.random.seed(102)

def main():
    # set up parameters
    T = 12  # number of periods
    n = 6   # number of products
    m = 4   # number of production factors
    m_a = 2 # number of secondary factors

    I_A = range(min(m_a, m))
    d = [[np.random.randint(4, 8)*(1.1-np.sin(j+2*np.pi*t/T)) for t in range(T)] for j in range(n)]  # product demands
    p = [np.random.randint(120, 150) for _ in range(n)]   # product prices
    k = [np.random.randint(10, 20) for _ in range(n)]     # production cost
    h = [np.random.uniform(0.5, 2.5) for _ in range(n)]   # holding cost
    b = [np.random.randint(5, 10) for _ in I_A]           # procurement cost of secondary materials
    c = [np.random.randint(30, 60) for _ in I_A]          # procurement cost of corresponding primary materials
    A = [[np.random.randint(15, 35) for _ in range(T)] for _ in range(m)]  # availability of secondary materials (deterministic)                  # set of all secondary materials
    a = [[np.random.randint(0, 8) for _ in range(n)] for _ in range(m)]    # production coefficients
    I_minus_I_A = [i for i in range(m) if i not in I_A]   # set of non-secondary production factors
    R_fix = [[np.random.randint(50, 100) for _ in range(T)] for _ in I_minus_I_A]  # capacity of non-secondary production factors  
    x_a = [np.random.randint(3, 5) for _ in range(n)]     # initial inventory levels of products
    R_a = [np.random.randint(10, 50) for _ in I_A]        # initial inventory levels of secondary materials
  
    # create and build model
    productionDetPlanModel = ProductionDetPlanModel(n, T, m, m_a, I_A, I_minus_I_A, R_fix, a, p, d, A, h , k, b, c, R_a, x_a)
    productionDetPlanModel.build_model()
    
    # run diverse experiment
    # TODO : create a function run_simulation with filename and number of experiment
    num_exp = 100
    if productionDetPlanModel.optimize():
        predictive_CM = productionDetPlanModel.model.objVal
    
        real_CM_avg_pred = productionDetPlanModel.simulate_schedule(num_exp)
        productionDetPlanModel.save_results("results_model")
        #set epsilon to 0 , if you don't want to use the model with non-anticipativity
        real_CM_avg_rolling = productionDetPlanModel.simulate_rolling_schedule(num_exp, epsilon=0) 
        real_CM_avg_rolling_na = productionDetPlanModel.simulate_rolling_schedule(num_exp, epsilon=1.1) 
        productionDetPlanModel.reoptimize_subject_to_non_anticipativity(f_star= predictive_CM, epsilon= 1.1)
        productionDetPlanModel.save_results("results_model_na")
        real_CM_avg_pred_na = productionDetPlanModel.simulate_schedule(num_exp) 

        # show results in console 
        print(f"\n\nContribution margin predicted by expected value model without non-anticipativity : {predictive_CM}")
        print(f"Contribution margin predicted by expected value model with non-anticipativity : {predictive_CM}")
        print(f"Average realized contribution margin of predictive schedule without non-anticipativity: {real_CM_avg_pred}")
        print(f"Average realized contribution margin of predictive schedule with non-anticipativity: {real_CM_avg_pred_na}")
        print(f"Average realized contribution margin of rolling predictive schedule without non-anticipativity: {real_CM_avg_rolling}")
        print(f"Average realized contribution margin of rolling predictive schedule with non-anticipativity: {real_CM_avg_rolling_na}")


    
    else:
        print("Optimization failed.")

if __name__ == "__main__":
    main()
