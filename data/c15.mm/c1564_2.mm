************************************************************************
file with basedata            : c1564_.bas
initial value random generator: 1635528071
************************************************************************
projects                      :  1
jobs (incl. supersource/sink ):  18
horizon                       :  129
RESOURCES
  - renewable                 :  2   R
  - nonrenewable              :  2   N
  - doubly constrained        :  0   D
************************************************************************
PROJECT INFORMATION:
pronr.  #jobs rel.date duedate tardcost  MPM-Time
    1     16      0       19        0       19
************************************************************************
PRECEDENCE RELATIONS:
jobnr.    #modes  #successors   successors
   1        1          3           2   3   4
   2        3          2           6   8
   3        3          3           5  10  14
   4        3          3          10  11  13
   5        3          1          16
   6        3          1           7
   7        3          1           9
   8        3          2          11  12
   9        3          2          15  17
  10        3          1          16
  11        3          1          16
  12        3          1          14
  13        3          2          14  15
  14        3          1          17
  15        3          1          18
  16        3          1          18
  17        3          1          18
  18        1          0        
************************************************************************
REQUESTS/DURATIONS:
jobnr. mode duration  R 1  R 2  N 1  N 2
------------------------------------------------------------------------
  1      1     0       0    0    0    0
  2      1     1       9    8    4    8
         2     3       8    8    2    8
         3     9       4    7    1    8
  3      1     1       4    5    3    8
         2     3       4    5    3    6
         3     6       2    5    3    4
  4      1     5       6    5    6    5
         2     5       7    3    7    5
         3     7       4    3    4    2
  5      1     5       6    7    2    6
         2     5       6    5    3    6
         3     8       5    5    2    5
  6      1     2      10    3    7    3
         2     2      10    2    8    5
         3     5       9    2    5    2
  7      1     4       7    5    4    8
         2     7       7    3    3    7
         3    10       5    1    3    6
  8      1     5      10    6    7    4
         2     6       7    4    6    4
         3     6       9    5    7    3
  9      1     6       8    6    4    9
         2     7       8    5    4    6
         3    10       4    3    4    2
 10      1     1       8    8    9    8
         2     3       5    7    9    7
         3     4       1    7    7    6
 11      1     6       6    7    3    6
         2     8       6    4    3    4
         3    10       6    2    3    1
 12      1     4       7    2    9    5
         2     5       7    2    5    5
         3     9       7    2    2    5
 13      1     1       4    9    9   10
         2     3       3    9    9   10
         3     9       2    9    9    9
 14      1     4       8    5    8    9
         2     8       6    4    8    8
         3    10       6    4    8    7
 15      1     1       6    7    9    8
         2     9       6    7    9    1
         3     9       6    5    9    3
 16      1     3       4    7    4    7
         2     8       4    6    4    6
         3     9       1    5    4    4
 17      1     5       7   10    9    8
         2     6       7    9    8    8
         3     8       5    9    7    6
 18      1     0       0    0    0    0
************************************************************************
RESOURCEAVAILABILITIES:
  R 1  R 2  N 1  N 2
   35   35  100  114
************************************************************************
