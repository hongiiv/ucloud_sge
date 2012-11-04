import threading
import datetime
import autoscale
        
class ThreadClass(threading.Thread):
   def run(self):
      now = datetime.datetime.now()
      autoscale.run()
      print "%s says Hello World at time: %s" %(self.getName(), now) 
        
for i in range(3):
   t = ThreadClass()
   t.start()
