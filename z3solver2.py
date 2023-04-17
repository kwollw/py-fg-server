from z3 import *
import db

# Zeit seit 00:00 Uhr in Minuten:
def minute(time):
  t = time.split(":")
  return int(t[0])*60 + int(t[1])

# Fahrtkosten:
def drive_costs(req): 
  return 1000 + req['passengers_count']-req['rides_count']

def schedule(date):
  req = db.getactive_requests(date)
  drive_cost = IntVector('drive_cost', len(req))
  time_to = IntVector('time_to', len(req))
  time_fro =  IntVector('time_fro', len(req))
  my_drive_to = IntVector('my_drive_to', len(req))
  my_drive_fro = IntVector('my_drive_fro', len(req))
  delays = IntVector('delays', len(req))
  
  opt = Optimize()
  # Fahrtkosten:
  opt.add([ drive_cost[i] == drive_costs(req[i]) for i in range(len(req)) if req[i]["driver_status"]=="F" ])
  opt.add([ drive_cost[i] == 0 for i in range(len(req)) if req[i]["driver_status"]=="M" ])
  opt.add([ (Or(drive_cost[i] == 0, drive_cost[i] == drive_costs(req[i]))) for i in range(len(req)) if req[i]["driver_status"]=="FM" ])

  # Fahrtzeiten:
  opt.add([ And(time_to[i] >= minute(req[i]['time_to']) - req[i]['time_to_max_delay'], time_to[i]<= minute(req[i]['time_to'])) for i in range(len(req)) if req[i]["time_to"] != ""])
  opt.add([ And(time_fro[i] >= minute(req[i]['time_fro']) - req[i]['time_fro_max_delay'], time_fro[i]<= minute(req[i]['time_fro'])) for i in range(len(req)) if req[i]["time_fro"] != ""])
  
  for r in req:
    print(r['user'], r['driver_status'], r['time_to'], r['time_to_max_delay'], r['max_passengers_to'], r['time_fro'], r['time_fro_max_delay'], r['max_passengers_fro'])
  
  print(opt)

  total_costs = Int('cost')

  opt.add(total_costs == Sum(drive_cost) + Sum(delays))
  opt.minimize(total_costs)
  check = opt.check()
  
  if check == sat: 
    solution = opt.model()
    print((total_costs,solution[total_costs]))
    print([(var,solution[var]) for var in drive_cost])
    print([(var,solution[var]) for var in time_to])
    print([(var,solution[var]) for var in time_fro])
    print([(var,solution[var]) for var in delays])
  else:
    print("unsat")

    # Fahrzeuge:
    # Fahrer fährt in seinem Fahrzeug, Mitfahrer fahren nicht in ihrem Fahrzeug
    # opt.add(If(drive_cost[i] > 0, my_drive[i] == i, my_drive[i] != i))
    # Anzahl der Plätze in einem Fahrzeug ist beschränkt 
    # opt.add(If(drive_cost[i] > 0, AtMost(*[(x == i) for x in my_drive_to], req['max_passengers_to']+2), And([(x == i) for x in my_drive_to]))
      
  
      
    
  
