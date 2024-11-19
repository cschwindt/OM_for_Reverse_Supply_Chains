$Title Procurement Planning under Stochastic Availability - Advanced Case
$Ontext

Course: Supply Chain Management
Section: 2.5 Procurement in Reverse Suppy Chains
Problem: Average-return MDP base model for procurement planning under stochastic availability and demand
Assumption: do not pay for undelivered items (necessiates larger state space)
Version 2: Aggregate undershoot-specific rewards r to expected rewards rbar

 - Model -

Author: Christoph Schwindt
Date: 03/08/2024

$Offtext

$eolcom //

scalars
   dmax     maximum demand / 10 /
   xmax     maximum inventory level / 20 /
   ymax     maximum availability / 15 /
   c        unit variable procurement cost / 5 /
   h        unit holding cost / 1/
   k        fixed procurement cost / 0 /
   v        unit shortage cost / 20 /
   mu_d     mean demand parameter normal distribution / 6 /
   sigma_d  standard deviation demand normal distribution / 3/
   mu_y     mean avaibility parameter normal distribution / 10 /
   sigma_y  standard deviation avaibility normal distribution / 6 /
   par_pD   parameter p in distribution of demand / 0.2 /
   par_pY   parameter p in distribution of yield / 0.2/ ;

$eval DMAX dmax
$eval YMAX ymax
$eval XMAX dmax+xmax
$eval QMAX min(xmax,ymax)

sets
   x            number of inventory level (state) / x0*x%XMAX% /
   q            order quantity (action) / q0*q%QMAX% /
   q_of_x(x,q)  feasible order quantities in state x
   d            demand / d0*d%DMAX% /
   y            availability / y0*y%YMAX% /
   u            undershoot q - y / u0*u%QMAX% / ;

alias(x, xPrime), (u, uPrime) ;

parameters
   val(x)                  inventory level encoded by x
   pD(d)                   probability of demand d
   pY(y)                   probability of availability y
   p(x,q,xPrime)           transition probability from x to xPrime given action q
   r(x,u,q)                "reward for inventory x, undershoot u, and action q"
   rbar(x,q)               expected reward for inventory x and order quantity q ;

   val(x) = ord(x)-1-dmax ;

   q_of_x(x,q) = no ;
   q_of_x(x,q)$(ord(q)-1 le xmax-val(x)+dmax) = yes ;

   pD(d) = binomial(dmax, ord(d)-1)*par_pD**(ord(d)-1)*(1-par_pD)**(dmax-(ord(d)-1)) ;
   pY(y) = binomial(ymax, ord(y)-1)*par_pY**(ord(y)-1)*(1-par_pY)**(ymax-(ord(y)-1)) ;
   //pD(d)$(ord(d)=1) = errorf([(ord(d)-1)+0.5-mu_d]/sigma_d) ;
   //pD(d)$((ord(d)>1) and (ord(d)<card(d))) = errorf([(ord(d)-1)+0.5-mu_d]/sigma_d) - errorf([((ord(d)-1)-1)+0.5-mu_d]/sigma_d) ;
   //pD(d)$(ord(d)=card(d)) = 1.0 - errorf([((ord(d)-1)-1)+0.5-mu_d]/sigma_d) ;

   //pY(y)$(ord(y)=1) = errorf([(ord(y)-1)+0.5-mu_y]/sigma_y) ;
   //pY(y)$((ord(y)>1) and (ord(y)<card(y))) = errorf([(ord(y)-1)+0.5-mu_y]/sigma_y) - errorf([((ord(y)-1)-1)+0.5-mu_y]/sigma_y) ;
   //pY(y)$(ord(y)=card(y)) = 1.0 - errorf([((ord(y)-1)-1)+0.5-mu_y]/sigma_y) ;

   r(x,u,q)$q_of_x(x,q) = -(c*(ord(q)-ord(u)) + h*max(0,val(x)) + k*(ord(q)>1) + v*max(0,-val(x))) ;
   rbar(x,q) = sum((u,y)$(ord(u)-1=max(0, ord(q)-ord(y))), pY(y)*r(x,u,q)) ;

   p(x,q,xPrime)$q_of_x(x,q) = sum((d,y)$((val(xPrime) = min(max(val(x),0) + min(ord(q)-1,ord(y)-1)-(ord(d)-1), xmax))), pD(d)*pY(y)) ;

variables
   g       objective function = negative cost per unit time
   b(x)    bias function value for state x

equations
   def_value_function(x,q)  definition of value function ;

   def_value_function(x,q)$q_of_x(x,q)..  g + b(x) =g= rbar(x,q) + sum(xPrime, p(x,q,xPrime)*b(xPrime)) ;

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

solve MDP using LP minimizing g ;

   def_value_function.m(x,q)$(def_value_function.m(x,q)=EPS) = 0 ; // put EPS values to zero

set pi(x,q) optimal policy ;

   pi(x,q) = no ;
   pi(x,q)$(q_of_x(x,q) and def_value_function.m(x,q)) = yes ;

display g.l, b.l, pi, def_value_function.m ;

scalars
   exp_inv        expected inventoty level
   max_inv        maximum inventory level
   exp_short      expeced shortage
   max_short      maximum shortage
   exp_ord_quant  expected order quantity ;

   exp_inv = sum(x$(val(x)>0), val(x)*sum(q, def_value_function.m(x,q))) ;
   max_inv = smax(x$((val(x) ge 0) and (sum(q, def_value_function.m(x,q))>0)), val(x)) ;
   exp_short = sum(x$(val(x)<0), -val(x)*sum(q, def_value_function.m(x,q))) ;
   max_short = smax(x$((val(x) le 0) and (sum(q, def_value_function.m(x,q)>0))), -val(x)) ;
   exp_ord_quant= sum(x, sum(q, (ord(q)-1)*def_value_function.m(x,q))) ;

file policy / policy_availability_model_v2.txt / ;
put policy ;
put 'Optimal policy for availability model v2' / / ;
put 'Inventory level', @17, '|', @19,
    'Order quantity', @34, '|', @36, 'Probability'/
    '=============================================='/
;
loop(x,
    put val(x):15:0, @17, '|', @19, (max(0,smax(q$pi(x,q), ord(q)-1))):14:0,
        @34, '|', @36, sum(q, def_value_function.m(x,q)):11:9 / ;
) ;
put /'Expected total cost per period:' @32, (-g.l):10:4/ ;
put 'Expected inventory level:', @32, exp_inv:10:4/ ;
put 'Maximum inventory level:', @32, max_inv:10:4/ ;
put 'Expected shortage:', @32, exp_short:10:4/ ;
put 'Maximum shortage:', @32, max_short:10:4/ ;
put 'Expected order quantity:', @32, exp_ord_quant:10:4 ;
putclose ;

