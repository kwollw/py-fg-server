from z3 import *
import db

def get_slots(requests,key):
  slots = set(map(lambda x: x[key], requests))
  slots.discard('')
  slots = list(map(lambda x: {key: x, "drives": [], "rides": []}, slots))
  return sorted(slots, key=lambda k: k[key])

requests = db.getactive_requests("2023-03-08")
slots_to = get_slots(requests,"time_to")
slots_fro = get_slots(requests,"time_fro")

x = [ Int("%s_%s" % (s, i)) for i in range(len(requests)) for s in ["drive", "delay_to", "delay_fro"]] 
a = []
for index, request in enumerate(requests):
  cost = max(5*(request['passengers_count']-request['rides_count'])+1000, 500)
  if request["driver_status"]=="F":
    a.append("= drive_%s %s" % (index,cost))
  elif request["driver_status"]=="M":
    a.append("= drive_%s 0" % (index))
  else:
    a.append("or (= drive_%s 0) (drive_%s %s)" % (index,index,cost))
  for slot in slots_to:
    delay = (request['time_to'] - slot['time_to']).to_i/60


print(slots_to)

     
