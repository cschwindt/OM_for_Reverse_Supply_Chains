import numpy as np



def simulate_rolling_horizon(model, x, y, z,v,w,p,d,b,c,R,R_a, x_a,I_A, A_diff_I_A, k, h, n, T, num_experiments=1):
    real_DBs_rolling = []
    for _ in range(num_experiments):
        # Reset variable bounds for each simulation
        for j in range(n):
            x[j, 0].LB = x_a[j]
            x[j, 0].UB = x_a[j]

            for t in range(T):
                y[j, t].LB = 0
                z[j, t].LB = 0

            for t in range(1, T + 1):
                x[j, t].LB = 0
        
        for i in I_A: 
            R[i,0].LB = R_a[i]
            R[i,0].UB = R_a[i]
            for t in range(T):
                v[i, t].LB = 0
                w[i, t].LB = 0
            for t in range(1,T+1):
                R[i,t].LB = 0
            
        DB_without_factor_cost = 0
        factor_cost = 0
        total_DB = 0
    
        for tau in range(T):
            #m.Params.TimeLimit = 10
            model.optimize()
            # Fix variables at time tau based on realized demand

            for j in range(n):
                # Retrieve the optimized values
                y_value = y[j,tau].x
                x_value = x[j,tau].x

                realized_demand = d[j][tau] + np.random.randint(-5,5)

                z_value = min(x_value + y_value, realized_demand)

                # Fix sales variable at tau
                z[j, tau].LB = z_value
                z[j, tau].UB = z_value
                
                #update initial inventory 
                x_a[j]  = max(0,x_value + y_value - realized_demand) 
                
                # Update inventory for tau + 1
                x_value = x_value + y_value - z_value
                x[j,tau + 1].LB = x_value
                x[j,tau + 1].UB = x_value

                # Fix production variables at tau
                y[j,tau].LB = y_value
                y[j,tau].UB = y_value
        
                DB_without_factor_cost += p[j]*z_value - k[j]*y_value - h[j]*x_value
            
            for i in I_A:
                v_value = v[i,tau].x
                w_value = w[i,tau].x
                      
                factor_cost += v_value*b[i] + w_value*c[i]     
            total_DB = DB_without_factor_cost - factor_cost
           
            # Remove constraints for time tau
            for i in I_A:
                con = model.getConstrByName(f"AvailabilityConstraint_{i}_{tau}")
                if con:
                    model.remove(con)
                con = model.getConstrByName(f"NonNegativityResource_{i}_{tau}")
                if con:
                    model.remove(con)
                con =  model.getConstrByName(f"NonNegativityV_{i}_{tau}")
                if con : 
                    model.remove(con)
                model.getConstrByName(f"NonNegativityW_{i}_{tau}")  
                if con :
                    model.remove(con)  
                model.getConstrByName(f"ResourceDynamics_{i}_{tau}")
                if con :
                    model.remove(con)  
                model.getConstrByName(f"InitialResourceAllocation_{i}")
                if con :
                    model.remove(con)
            
            for i in A_diff_I_A:
                con = model.getConstrByName(f"ResourceConstraint_{i}_{tau}")
                if con:
                    model.remove(con)

            for j in range(n):
                con = model.getConstrByName(f"InventoryDynamics_{j}_{tau}")
                if con:
                    model.remove(con)
                con = model.getConstrByName(f"NonNegativitX_{j}_{tau}")
                if con:
                    model.remove(con)
                con = model.getConstrByName(f"NonNegativitY_{j}_{tau}")
                if con:
                    model.remove(con)
                con = model.getConstrByName(f"NonNegativitZ_{j}_{tau}")
                if con:
                    model.remove(con)
                con = model.getConstrByName(f"DemandConstraint_{j}_{tau}")
                if con:
                    model.remove(con)
                
            model.update()

        real_DBs_rolling.append(total_DB)
  
    real_DB_avg_rolling = np.mean(real_DBs_rolling)
    return real_DB_avg_rolling

def save_results(model,x,y,z,w,v,R,T,n,d,I_A,filename):
    with open(f"Produktionsplanung/Python/deterministic/documents/{filename}.txt", "w") as f:
        # Summary of key metrics
        # Production plan, factor usage, resource allocation, and inventory for each product i and period t
        f.write("\n Optimal production plan for production programm planning in circualr economic\n\n")
        f.write("-----------------------------------------------------------------\n")
        f.write("Product  | Period  | Iventory  | production  | sales  | demands \n")
        f.write("-----------------------------------------------------------------\n") 
        for i in range(n):
            for t in range(T):
                # Write rows for each product i and period t
                f.write(f"{i+1:8} | {t+1:7} | {x[i,t].x:9} | {y[i,t].x:11} | {z[i,t].x:6} | {d[i][t]:8}\n")
        f.write("\n")
        f.write("----------------------------------------------------------------------------\n")
        f.write("Product  | Period  |  Residual Capacity  | reusable factor  | primary factor\n")
        f.write("----------------------------------------------------------------------------\n")
        for i in I_A:
            for t in range(T):
                # Write rows for each factor i and period t
                f.write(f"{i+1:8} | {t+1:7} | {R[i,t].x:19} | {v[i,t].x:16} | {w[i,t].x:8}\n")

        f.write("\n")
        
        # Compute service levels for each product
        service_levels = []
        for j in range(n):
            # Check if inventory + production >= demand in each period
            fulfilled_periods = sum((x[j,t].x + y[j,t].x) >= d[j][t] for t in range(T))
            service_level_j = fulfilled_periods / T  # Fraction of periods with fulfilled demand
            service_levels.append(service_level_j)

        # Compute overall service level
        overall_service_level = np.prod(service_levels)
        for j, sl in enumerate(service_levels):
            f.write(f"Service Level for Product {j + 1}: {sl:.4f}\n")
        f.write(f"\nOverall Service Level: {overall_service_level:.4f}\n\n")

        f.write(f"total contribution margin: {model.objVal:.4f}\n")