$Title Procurement Planning under Stochastic Availability - Advanced Case
$Ontext

Course: Supply Chain Management
Section: 2.6 Procurement in Reverse Suppy Chains
Problem: Average-return MDP base model for procurement planning under stochastic availability and demand
Assumption: do not pay for undelivered items (necessiates larger state space)
Version 3: Avoid undershoot-specific rewards r

 - Model -

Author: Christoph Schwindt
Date: 18/10/2024

$Offtext

$eolcom //

scalars
   dmax    maximum demand / 10 /
   xmax    maximum inventory level / 20 /
   ymax    maximum availability / 15 /
   pi      unit variable procurement cost / 5 /
   h       unit holding cost / 1 /
   k       fixed procurement cost / 2 /
   v       unit shortage cost / 20 /
   par_pD  parameter p in distribution of demand / 0.4 /
   par_pY  parameter p in distribution of yield / 0.3 / ;

$eval DMAX dmax
$eval YMAX ymax
$eval XMAX dmax+xmax
$eval QMAX min(xmax,ymax)

sets
   x            number of inventory level (state) / x0*x%XMAX% /
   q            order quantity (action) / q0*q%QMAX% /
   q_of_x(x,q)  feasible order quantities in state x
   d            demand / d0*d%DMAX% /
   y            availability / y0*y%YMAX% / ;
*   u            undershoot q - y / u0*u%QMAX% / ;

alias(x, xPrime) ;

parameters
   val(x)                  inventory level encoded by x
   pD(d)                   probability of demand d
   pY(y)                   probability of availability y
   p(x,q,xPrime)           transition probability from x to xPrime given action q
   r(x,q)                  expected reward for inventory x and action q ;
*   rbar(x,q)               expected reward for inventory x and order quantity q ;

   val(x) = ord(x)-1-dmax ;

   q_of_x(x,q) = no ;
   q_of_x(x,q)$(ord(q)-1 le xmax-val(x)+dmax) = yes ;

   pD(d) = binomial(dmax, ord(d)-1)*par_pD**(ord(d)-1)*(1-par_pD)**(dmax-(ord(d)-1)) ;
   pY(y) = binomial(ymax, ord(y)-1)*par_pY**(ord(y)-1)*(1-par_pY)**(ymax-(ord(y)-1)) ;

   r(x,q)$q_of_x(x,q) = -(pi*sum(y, pY(y)*min(ord(q)-1,ord(y)-1)) + h*max(0,val(x)) + k*(ord(q)>1) + v*max(0,-val(x))) ;
*   rbar(x,q) = sum((u,y)$(ord(u)-1=max(0, ord(q)-ord(y))), pY(y)*r(x,u,q)) ;

   p(x,q,xPrime)$q_of_x(x,q) = sum((d,y)$((val(xPrime) = min(max(val(x),0) + min(ord(q)-1,ord(y)-1)-(ord(d)-1), xmax))), pD(d)*pY(y)) ;

variables
   c       objective function = negative cost per unit time
   b(x)    bias function value for state x

equations
   def_value_function(x,q)  definition of value function ;

   def_value_function(x,q)$q_of_x(x,q)..  c + b(x) =g= r(x,q) + sum(xPrime, p(x,q,xPrime)*b(xPrime)) ;

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

   exp_inv = sum(x$(val(x)>0), val(x)*sum(q, def_value_function.m(x,q))) ;
   max_inv = smax(x$((val(x) ge 0) and (sum(q, def_value_function.m(x,q))>0)), val(x)) ;
   exp_short = sum(x$(val(x)<0), -val(x)*sum(q, def_value_function.m(x,q))) ;
   max_short = smax(x$((val(x) le 0) and (sum(q, def_value_function.m(x,q)>0))), -val(x)) ;
   exp_ord_quant= sum(x, sum(q, (ord(q)-1)*def_value_function.m(x,q))) ;

file policy / policy_availability_model_v3.txt / ;
put policy ;
put 'Optimal policy for availability model v3' / / ;
put 'Inventory level', @17, '|', @19,
    'Order quantity', @34, '|', @36, 'Probability'/
    '=============================================='/
;
loop(x,
    put val(x):15:0, @17, '|', @19, (max(0,smax(q$q_pol(x,q), ord(q)-1))):14:0,
        @34, '|', @36, sum(q, def_value_function.m(x,q)):11:9 / ;
) ;
put /'Expected total cost per period:' @32, (-c.l):10:4/ ;
put 'Expected inventory level:', @32, exp_inv:10:4/ ;
put 'Maximum inventory level:', @32, max_inv:10:4/ ;
put 'Expected shortage:', @32, exp_short:10:4/ ;
put 'Maximum shortage:', @32, max_short:10:4/ ;
put 'Expected order quantity:', @32, exp_ord_quant:10:4 ;
putclose ;

