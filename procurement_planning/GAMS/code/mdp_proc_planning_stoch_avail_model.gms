$Title Procurement Planning under Stochastic Availability
$Ontext

Course: Supply Chain Management
Section: 2.6 Procurement in Reverse Suppy Chains
Problem: Average-return MDP base model for procurement planning under stochastic availability and demand
Assumption: Do not pay for undelivered items

 - Model -

Author: Christoph Schwindt
Date: 18/10/2024

$Offtext

$eolcom //

$include mdp_proc_planning_stoch_avail_data.gms

variables
   rbar  objective function = negative cost per unit time
   b(x)  bias function value for state x

equations
   def_value_function(x,q)  definition of value function ;

   def_value_function(x,q)$q_of_x(x,q)..  rbar + b(x) =g= r(x,q) + sum(xPrime, p(x,q,xPrime)*b(xPrime)) ;

model MDP / all / ;

options lp = cplex
        decimals = 8 ;

MDP.optfile = 1 ;
$onecho > cplex.opt
epopt 1e-9
eprhs 1e-9
$offecho

MDP.solprint = 2 ; // suppress entries in listing file

b.fx(x)$(ord(x)=1) = 0 ; // remove degree of freedom such that g = max_q Q(x0,q)

solve MDP using LP minimizing rbar ;

   def_value_function.m(x,q)$(def_value_function.m(x,q)=EPS) = 0 ; // put EPS values to zero

set q_pol(x,q) optimal policy ;

   q_pol(x,q) = no ;
   q_pol(x,q)$(q_of_x(x,q) and def_value_function.m(x,q)) = yes ;

display rbar.l, b.l, q_pol, def_value_function.m ;

scalars
   exp_inv        expected inventory level
   max_inv        maximum inventory level
   exp_short      expected shortage
   max_short      maximum shortage
   exp_ord_quant  expected order quantity
   exp_sup_quant  expected supply quantity ;

   exp_inv = sum(x$(val(x)>0), val(x)*sum(q, def_value_function.m(x,q))) ;
   max_inv = smax(x$((val(x) ge 0) and (sum(q, def_value_function.m(x,q))>0)), val(x)) ;
   exp_short = sum(x$(val(x)<0), -val(x)*sum(q, def_value_function.m(x,q))) ;
   max_short = smax(x$((val(x) le 0) and (sum(q, def_value_function.m(x,q)>0))), -val(x)) ;
   exp_ord_quant = sum(x, sum(q, (ord(q)-1)*def_value_function.m(x,q))) ;
   exp_sup_quant = sum(x, sum(q, sum(y, pY(y)*min(ord(q)-1,ord(y)-1))*def_value_function.m(x,q))) ;

file policy / policy_availability_model.txt / ;
put policy ;
put 'Optimal policy for availability model' / / ;
put 'Inventory level', @17, '|', @19,
    'Order quantity', @34, '|', @36, 'Probability'/
    '=============================================='/
;
loop(x,
    put val(x):15:0, @17, '|', @19, (max(0,smax(q$q_pol(x,q), ord(q)-1))):14:0,
        @34, '|', @36, sum(q, def_value_function.m(x,q)):11:9 / ;
) ;
put /'Expected total cost per period:' @32, (-rbar.l):10:4/ ;
put 'Expected inventory level:', @32, exp_inv:10:4/ ;
put 'Maximum inventory level:', @32, max_inv:10:4/ ;
put 'Expected shortage:', @32, exp_short:10:4/ ;
put 'Maximum shortage:', @32, max_short:10:4/ ;
put 'Expected order quantity:', @32, exp_ord_quant:10:4/ ;
put 'Expected supply quantity:', @32, exp_sup_quant:10:4 ;
putclose ;

