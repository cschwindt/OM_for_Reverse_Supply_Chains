$Title Procurement Planning under Stochastic Yield
$Ontext

Course: Supply Chain Management
Section: 2.6 Procurement in Reverse Suppy Chains
Problem: Average-return MDP model for procurement planning under stochastic yield and demand

 - Data -

Author: Christoph Schwindt
Date: 03/08/2024

$Offtext

scalars
   dmax    maximum demand / 10 /
   xmax    maximum inventory level / 20 /
   qmax    maximum oder quantity / 15 /
   pi      unit variable procurement cost / 5 /
   h       unit holding cost / 1 /
   k       fixed procurement cost / 5 /
   v       unit shortage cost / 20 /
   par_pD  parameter p in distribution of demand / 0.5 /
   par_pY  parameter p in distribution of yield / 0.5 / ;

$eval DMAX dmax
$eval YMAX qmax
$eval XMAX dmax+xmax
$eval QMAX qmax

sets
   x            number of inventory level (state) / x0*x%XMAX% /
   q            order quantity (action) / q0*q%QMAX% /
   q_of_x(x,q)  feasible order quantities in state x
   d            demand / d0*d%DMAX% /
   y            yield  / y0*y%YMAX% / ;

alias(x, xPrime) ;

parameters
   val_x(x)       inventory level encoded by x
   val_y(y)       yield encoded by y
   pD(d)          probability of demand d
   pY(q,y)        probability of yield y given order quantity q
   p(x,q,xPrime)  transition probability from x to xPrime given action q
   r(x,q)         reward for state x and action q ;

   val_x(x) = ord(x)-1-dmax ;

   q_of_x(x,q) = yes ; // due to yields < 1 it may be rewarding to order more than xmax - x + dmax items even though items may be lost

   pD(d) = binomial(dmax, ord(d)-1)*par_pD**(ord(d)-1)*(1-par_pD)**(dmax-(ord(d)-1)) ;
   pY(q,y)$(ord(y) le ord(q)) = binomial(ord(q)-1, ord(y)-1)*par_pY**(ord(y)-1)*(1-par_pY)**(ord(q)-(ord(y))) ;

   r(x,q)$q_of_x(x,q) = -(pi*(ord(q)-1) + h*max(0,val_x(x)) + k*(ord(q)>1) + v*max(0,-val_x(x))) ;

   p(x,q,xPrime)$q_of_x(x,q) = sum((d,y)$((ord(y) le ord(q)) and (val_x(xPrime) = min(max(val_x(x),0) + (ord(y)-1) - (ord(d)-1), xmax))), pD(d)*pY(q,y)) ;
