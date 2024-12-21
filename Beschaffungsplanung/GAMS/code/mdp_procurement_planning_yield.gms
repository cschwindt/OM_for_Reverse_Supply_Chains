$Title Procurement Planning under Stochastic Yield
$Ontext

Course: Supply Chain Management
Section: 2.6 Procurement in Reverse Suppy Chains
Problem: Average-return MDP model for procurement planning under stochastic yield and demand

 - Model -

Author: Christoph Schwindt
Date: 03/08/2024

$Offtext

$eolcom //

scalars
   dmax    maximum demand / 10 /
   xmax    maximum inventory level / 20 /
   ynum    number of positive yields / 5 / // minimum yield = 0, maximum yield = 1
   qmax    maximum oder quantity / 10 /
   pi      unit variable procurement cost / 5 /
   h       unit holding cost / 1 /
   k       fixed procurement cost / 2 /
   v       unit shortage cost / 20 /
   par_pD  parameter p in distribution of demand / 0.4 /
   par_pY  parameter p in distribution of yield / 0.3 / ;

$eval DMAX dmax
$eval YNUM ynum
$eval XMAX dmax+xmax
$eval QMAX qmax

sets
   x            number of inventory level (state) / x0*x%XMAX% /
   q            order quantity (action) / q0*q%QMAX% /
   q_of_x(x,q)  feasible order quantities in state x
   d            demand / d0*d%DMAX% /
   y            yield  / y0*y%YNUM% / ;

alias(x, xPrime) ;

parameters
   val_x(x)       inventory level encoded by x
   val_y(y)       yield encoded by y
   pD(d)          probability of demand d
   pY(y)          probability of availability y
   p(x,q,xPrime)  transition probability from x to xPrime given action q
   r(x,q)         reward for state x and action q ;

   val_x(x) = ord(x)-1-dmax ;
   val_y(y) = (ord(y)-1)/ynum ;

   q_of_x(x,q) = yes ; // due to yields < 1 it may be rewarding to order more than xmax - x + dmax items even though items may be lost

   pD(d) = binomial(dmax, ord(d)-1)*par_pD**(ord(d)-1)*(1-par_pD)**(dmax-(ord(d)-1)) ;
   pY(y) = binomial(ynum, ord(y)-1)*par_pY**(ord(y)-1)*(1-par_pY)**(ynum-(ord(y)-1)) ;

   r(x,q)$q_of_x(x,q) = -(pi*(ord(q)-1) + h*max(0,val_x(x)) + k*(ord(q)>1) + v*max(0,-val_x(x))) ;

   p(x,q,xPrime)$q_of_x(x,q) = sum((d,y)$(val_x(xPrime) = min(max(val_x(x),0) + round((ord(q)-1)*val_y(y))-(ord(d)-1), xmax)), pD(d)*pY(y)) ;

variables
   c             "objective function = negative cost per unit time"
   b(x)          bias function value for state x
   Q_value(x,q)  Q-value for state x and action q
   aux_obj       auxiliary objective function value ;

equations
   def_value_function(x,q)  definition of value function
   def_aux_obj              defintition of auxiliary objective function
   def_Q_value(x,q)         definition of Q-value ;

   def_value_function(x,q)$q_of_x(x,q)..  c + b(x) =g= r(x,q) + sum(xPrime, p(x,q,xPrime)*b(xPrime)) ;
   def_aux_obj..                          aux_obj =e= sum(x, b(x)) ;
   def_Q_value(x,q)$q_of_x(x,q)..         Q_value(x,q) =e= r(x,q) + sum(xPrime, p(x,q,xPrime)*b(xPrime)) ;

model MDP / def_value_function / ;

options lp = cplex
        decimals = 8 ;

MDP.optfile = 1 ;
$onecho > cplex.opt
epopt 1e-5
eprhs 1e-5
$offecho

MDP.solprint = 2 ; // suppress entries in listing file

b.fx(x)$(ord(x)=1) = 0 ; // remove degree of freedom such that g = max_q Q(x0,q)

solve MDP using LP minimizing c ;

   def_value_function.m(x,q)$(def_value_function.m(x,q)=EPS) = 0 ; // put EPS values to zero

set q_pol(x,q) optimal policy ;

   q_pol(x,q) = no ;
   q_pol(x,q)$(q_of_x(x,q) and def_value_function.m(x,q)) = yes ;

display c.l, b.l, q_pol, def_value_function.m ;

scalars
   exp_inv        expected inventory level
   max_inv        maximum inventory level
   exp_short      expected shortage
   max_short      maximum shortage
   exp_ord_quant  expected order quantity ;

   exp_inv = sum(x$(val_x(x)>0), val_x(x)*sum(q, def_value_function.m(x,q))) ;
   max_inv = smax(x$((val_x(x) ge 0) and (sum(q, def_value_function.m(x,q))>0)), val_x(x)) ;
   exp_short = sum(x$(val_x(x)<0), -val_x(x)*sum(q, def_value_function.m(x,q))) ;
   max_short = smax(x$((val_x(x) le 0) and (sum(q, def_value_function.m(x,q)>0))), -val_x(x)) ;
   exp_ord_quant= sum(x, sum(q, (ord(q)-1)*def_value_function.m(x,q))) ;

file policy / policy_yield_model_v2.txt / ;
put policy ;
put 'Optimal policy for yield model' / / ;
put 'Inventory level', @17, '|', @19,
    'Order quantity', @34, '|', @36, 'Probability'/
    '=============================================='/
loop(x,
    put val_x(x):15:0, @17, '|', @19, (sum(q$q_pol(x,q), ord(q)-1)):14:0,
        @34, '|', @36, sum(q, def_value_function.m(x,q)):11:9 / ;
) ;
put /'Expected total cost per period:', @32, (-c.l):10:4/ ;
put 'Expected inventory level:', @32, exp_inv:10:4/ ;
put 'Maximum inventory level:', @32, max_inv:10:4/ ;
put 'Expected shortage:', @32, exp_short:10:4/ ;
put 'Maximum shortage:', @32, max_short:10:4/ ;
put 'Expected order quantity:', @32, exp_ord_quant:10:4 ;
putclose ;

$ontext // model for computing Q-values
model MDP_aux / def_value_function, def_aux_obj, def_Q_value / ;

MDP_aux.optfile = 1 ;

g.fx=g.l ;
solve MDP_aux using LP minimizing aux_obj ;

display Q_value.l ;
$offtext
