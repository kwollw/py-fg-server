from z3 import *
import db


def get_slots(requests,key):
  slots = set(map(lambda x: x[key], requests))
  slots.discard('')
  slots = list(map(lambda x: {key: x, "drives": [], "rides": []}, slots))
  return sorted(slots, key=lambda k: k[key])

def minute_diff(fro,to):
  f = fro.split(":")
  t = to.split(":")
  return int(t[0])*60 + int(t[1]) - (int(f[0])*60 + int(f[1]))

requests = db.getactive_requests("2023-03-07")
slots_to = get_slots(requests,"time_to")
slots_fro = get_slots(requests,"time_fro")

drive = [ Int("drive_%s" % (i)) for i in range(len(requests))]
delay_to = [ Int("delay_to_%s" % (i)) for i in range(len(requests))]
delay_fro = [ Int("delay_fro_%s" % (i)) for i in range(len(requests))]


a = []
for index, req in enumerate(requests):
  cost = max(5*(req['passengers_count']-req['rides_count'])+1000, 500)
  if req["driver_status"]=="F":
    a.append(drive[index] == cost)
  elif req["driver_status"]=="M":
    a.append(drive[index] == 0)
  else:
    a.append(Or(drive[index]== 0, drive[index] == cost))
  if req['time_to'] != "":
    delays = []
    for slot in slots_to:
      delay = minute_diff(req['time_to'],slot['time_to'])
      if (req['driver_status'] == "M" or delay <= req['time_to_max_delay']) and delay >= 0:
        delays.append(delay_to[index] == delay)
    a.append(Or (delays))
  if req['time_fro'] != "":
    delays = []
    for slot in slots_fro:
      delay = minute_diff(slot['time_fro'], req['time_fro'])
      if (req['driver_status'] == "M" or delay <= req['time_to_max_delay']) and delay >= 0:
        delays.append(delay_fro[index] == delay)
    a.append(Or (delays))


for slot in slots_to:
  seats = []
  for index, req in enumerate(requests):
    if req['time_to'] != "":
      delay = minute_diff(req['time_to'],slot['time_to'])
      if (req['driver_status'] == "M" or delay <= req['time_to_max_delay']) and delay >= 0:
        seats.append(If(delay_to[index] == delay, If(drive[index] == 0, -1, req['max_passengers_to']), 0))
  a.append(Sum(seats) <= 0)

for slot in slots_fro:
  seats = []
  for index, req in enumerate(requests):
    if req['time_fro'] != "":
      delay = minute_diff(slot['time_fro'],req['time_fro'])
      if (req['driver_status'] == "M" or delay <= req['time_fro_max_delay']) and delay >= 0:
        seats.append(If(delay_fro[index] == delay, If(drive[index] == 0, -1, req['max_passengers_fro']), 0))
  a.append(Sum(seats) <= 0)

cost = Int('cost') 

opt = Optimize()
opt.add(a)
opt.add(cost == sum(drive) + sum(delay_to) + sum(delay_fro))
opt.minimize(cost)
print(opt.check())
solution = opt.model()
print((cost,solution[cost]))
print([(var,solution[var]) for var in drive])
print([(var,solution[var]) for var in delay_to])
print([(var,solution[var]) for var in delay_fro])
