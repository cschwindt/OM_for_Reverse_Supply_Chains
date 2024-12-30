$Title Procurement Planning under Stochastic Yield
$Ontext

Course: Supply Chain Management
Section: 2.6 Procurement in Reverse Suppy Chains
Problem: Average-return MDP model for procurement planning under stochastic yield and demand
Assumption: Do also pay for defective items

 - Model -

Author: Christoph Schwindt
Date: 03/08/2024

$Offtext

$eolcom //

$include mdp_proc_planning_stoch_yield_data.gms

variables
   rbar          "objective function = negative cost per unit time"
   b(x)          bias function value for state x
   Q_value(x,q)  Q-value for state x and action q
   aux_obj       auxiliary objective function value ;

equations
   def_value_function(x,q)  definition of value function
   def_aux_obj              defintition of auxiliary objective function
   def_Q_value(x,q)         definition of Q-value ;

   def_value_function(x,q)$q_of_x(x,q)..  rbar + b(x) =g= r(x,q) + sum(xPrime, p(x,q,xPrime)*b(xPrime)) ;
   def_aux_obj..                          aux_obj =e= sum(x, b(x)) ;
   def_Q_value(x,q)$q_of_x(x,q)..         Q_value(x,q) =e= r(x,q) + sum(xPrime, p(x,q,xPrime)*b(xPrime)) ;

model MDP / def_value_function / ;

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
   exp_yield      expected yield ;

   exp_inv = sum(x$(val_x(x)>0), val_x(x)*sum(q, def_value_function.m(x,q))) ;
   max_inv = smax(x$((val_x(x) ge 0) and (sum(q, def_value_function.m(x,q))>0)), val_x(x)) ;
   exp_short = sum(x$(val_x(x)<0), -val_x(x)*sum(q, def_value_function.m(x,q))) ;
   max_short = smax(x$((val_x(x) le 0) and (sum(q, def_value_function.m(x,q)>0))), -val_x(x)) ;
   exp_ord_quant = sum(x, sum(q, (ord(q)-1)*def_value_function.m(x,q))) ;
   exp_yield = sum(x, sum(q, sum(y$(ord(y) le ord(q)), pY(q,y)*(ord(y)-1))*def_value_function.m(x,q))) ;

display exp_yield ;


file policy / policy_yield_model.txt / ;
put policy ;
put 'Optimal policy for yield model' / / ;
put 'Inventory level', @17, '|', @19,
    'Order quantity', @34, '|', @36, 'Probability'/
    '=============================================='/
loop(x,
    put val_x(x):15:0, @17, '|', @19, (sum(q$q_pol(x,q), ord(q)-1)):14:0,
        @34, '|', @36, sum(q, def_value_function.m(x,q)):11:9 / ;
) ;
put /'Expected total cost per period:', @32, (-rbar.l):10:4/ ;
put 'Expected inventory level:', @32, exp_inv:10:4/ ;
put 'Maximum inventory level:', @32, max_inv:10:4/ ;
put 'Expected shortage:', @32, exp_short:10:4/ ;
put 'Maximum shortage:', @32, max_short:10:4/ ;
put 'Expected order quantity:', @32, exp_ord_quant:10:4/ ;
put 'Expected yield:', @32, exp_yield:10:4 ;
putclose ;

$ontext // model for computing Q-values of state-action value function Q
model MDP_aux / def_value_function, def_aux_obj, def_Q_value / ;

MDP_aux.optfile = 1 ;

g.fx=g.l ;
solve MDP_aux using LP minimizing aux_obj ;

display Q_value.l ;
$offtext
