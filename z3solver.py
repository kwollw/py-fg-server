from z3 import *
import db



# Zeit seit 00:00 Uhr in 5-Minuten Abständen:
def time_slot(time):
  t = time.split(":")
  return (int(t[0])*60 + int(t[1])) // 5

def time(time_slot):
  minutes = time_slot * 5
  return str(minutes // 60).zfill(2) + ":" + str(minutes % 60).zfill(2)

# Fahrtkosten:
def drive_costs(req): 
  return 1000 + req['passengers_count']-req['rides_count']

def schedule(date):
  req = db.active_requests(date)
  drive_cost = IntVector('drive_cost', len(req))
  time_to = IntVector('time_to', len(req))
  time_fro =  IntVector('time_fro', len(req))
  my_drive_to = IntVector('my_drive_to', len(req))
  my_drive_fro = IntVector('my_drive_fro', len(req))
  
  
  opt = Optimize()
  # Fahrtkosten:
  opt.add([ drive_cost[i] == drive_costs(req[i]) for i in range(len(req)) if req[i]["driver_status"]=="F" ])
  opt.add([ drive_cost[i] == 0 for i in range(len(req)) if req[i]["driver_status"]=="M" ])
  opt.add([ (Or(drive_cost[i] == 0, drive_cost[i] == drive_costs(req[i]))) for i in range(len(req)) if req[i]["driver_status"]=="FM" ])

  # Fahrtzeiten:
  opt.add([ And(time_to[i]<= time_slot(req[i]['time_to']), time_to[i] >= time_slot(req[i]['time_to']) - req[i]['time_to_max_delay'] // 5) for i in range(len(req)) if req[i]["time_to"] != "" ])
  opt.add([ And(time_fro[i] >= time_slot(req[i]['time_fro']) , time_fro[i]<= time_slot(req[i]['time_fro']) + req[i]['time_fro_max_delay'] // 5) for i in range(len(req)) if req[i]["time_fro"] != "" ])
  
  # Fahrer fahren ihr Fahrzeug, Mitfahrer fahren in anderem Fahrzeug
  opt.add([ And(my_drive_to[i] >= 0, my_drive_to[i] < len(req)) for i in range(len(req)) if req[i]["time_to"] != "" ])
  opt.add([ If(drive_cost[i] > 0, my_drive_to[i] == i, my_drive_to[i] != i) for i in range(len(req)) if req[i]["time_to"] != "" ])
  
  opt.add([ And(my_drive_fro[i] >= 0, my_drive_fro[i] < len(req)) for i in range(len(req)) if req[i]["time_fro"] != "" ])
  opt.add([ If(drive_cost[i] > 0, my_drive_fro[i] == i, my_drive_fro[i] != i) for i in range(len(req)) if req[i]["time_fro"] != "" ])

  # Relation Fahrer <=> Mitfahrer:
  opt.add([ Implies(my_drive_to[rider] == driver, And(drive_cost[driver] > 0, drive_cost[rider] == 0, time_to[driver] == time_to[rider])) for driver in range(len(req)) for rider in range(len(req)) if driver != rider ])
  opt.add([ Implies(my_drive_fro[rider] == driver, And(drive_cost[driver] > 0, drive_cost[rider] == 0, time_fro[driver] == time_fro[rider])) for driver in range(len(req)) for rider in range(len(req)) if driver != rider ])

  # Beschränkung der Plätze in einem Fahrzeug: 
  for driver in range(len(req)):
    opt.add(Implies(drive_cost[driver] > 0, AtMost(*[my_drive_to[rider] == driver for rider in range(len(req)) if rider != driver ],req[driver]['max_passengers_to'] )))
    opt.add(Implies(drive_cost[driver] > 0, AtMost(*[my_drive_fro[rider] == driver for rider in range(len(req)) if rider != driver ],req[driver]['max_passengers_fro'] )))
  
  total_costs = Int('cost')
  opt.add(total_costs == Sum(drive_cost) + Sum(time_fro) - Sum(time_to))
  opt.minimize(total_costs)
  
  check = opt.check()
  if check == sat: 
    solution = opt.model()
    drives = []
    for index, r in enumerate(req):
      if solution[drive_cost[index]].as_long() > 0:
        drive = {'date': date, 'user': r['user'], 'max_passengers_to': r['max_passengers_to'], 'max_passengers_fro': r['max_passengers_fro'], 'time_to': time(solution[time_to[index]].as_long()), 'time_fro': time(solution[time_fro[index]].as_long())}
        drive['rides_to'] = [ req[i]['user'] for i in range(len(req)) if i != index and solution[my_drive_to[i]].as_long() == index ]
        drive['rides_fro'] = [ req[i]['user'] for i in range(len(req)) if i != index and solution[my_drive_fro[i]].as_long() == index ]
        drives.append(drive)
    return drives
  else:
    return []
