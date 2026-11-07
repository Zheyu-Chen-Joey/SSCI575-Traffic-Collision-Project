import csv
from collections import defaultdict
rows=list(csv.DictReader(open('04_outputs/grid_search/origin_sensitivity.csv')));groups=defaultdict(list)
for r in rows:groups[(r['offset_x_fraction'],r['offset_y_fraction'])].append(r)
for k,g in groups.items():
 a=[float(r['nsr']) for r in g];print(k,[(r['scale_m'],round(float(r['nsr']),4)) for r in g]);print('minima',[g[i]['scale_m'] for i in range(1,len(a)-1) if a[i]<=a[i-1] and a[i]<a[i+1]])
