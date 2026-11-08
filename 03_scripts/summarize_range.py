import csv,collections
rows=list(csv.DictReader(open('04_outputs/range_validation/leave_one_block_out.csv')));groups=collections.defaultdict(dict)
for r in rows:groups[(r['max_lag_m'],r['omitted_block'])][int(r['scale_m'])]=float(r['nsr'])
for lag in ['25000','45000','55000']:
 g=[v for (l,b),v in groups.items() if l==lag and all(s in v for s in [950,1100,1250])];ds=[v[1250]-v[1100] for v in g];print(lag,'matched blocks',len(g),'1100 local min support',sum(v[1100]<v[950] and v[1100]<v[1250] for v in g),'difference min/max',min(ds),max(ds))
