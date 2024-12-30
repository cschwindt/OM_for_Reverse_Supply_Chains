$Title Procurement Planning under Stochastic Availability
$Ontext

Course: Supply Chain Management
Section: 2.6 Procurement in Reverse Suppy Chains
Problem: Average-return MDP model for procurement planning under stochastic availability and demand

 - Data -

Author: Christoph Schwindt
Date: 18/10/2024

$Offtext

scalars
   dmax    maximum demand / 10 /
   xmax    maximum inventory level / 20 /
   ymax    maximum availability / 15 /
   pi      unit variable procurement cost / 5 /
   h       unit holding cost / 1 /
   k       fixed procurement cost / 5 /
   v       unit shortage cost / 20 /
   par_pD  parameter p in distribution of demand / 0.5 /
   par_pY  parameter p in distribution of availability / 0.5 / ;

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

alias(x, xPrime) ;

parameters
   val(x)                  inventory level encoded by x
   pD(d)                   probability of demand d
   pY(y)                   probability of availability y
   p(x,q,xPrime)           transition probability from x to xPrime given action q
   r(x,q)                  expected reward for inventory x and action q ;

   val(x) = ord(x)-1-dmax ;

   q_of_x(x,q) = no ;
   q_of_x(x,q)$(ord(q)-1 le xmax-val(x)+dmax) = yes ;

   pD(d) = binomial(dmax, ord(d)-1)*par_pD**(ord(d)-1)*(1-par_pD)**(dmax-(ord(d)-1)) ;
   pY(y) = binomial(ymax, ord(y)-1)*par_pY**(ord(y)-1)*(1-par_pY)**(ymax-(ord(y)-1)) ;

   r(x,q)$q_of_x(x,q) = -(pi*sum(y, pY(y)*min(ord(q)-1,ord(y)-1)) + h*max(0,val(x)) + k*(ord(q)>1) + v*max(0,-val(x))) ;

   p(x,q,xPrime)$q_of_x(x,q) = sum((d,y)$((val(xPrime) = min(max(val(x),0) + min(ord(q)-1,ord(y)-1) - (ord(d)-1), xmax))), pD(d)*pY(y)) ;
