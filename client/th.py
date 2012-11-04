#!/usr/bin/python 
import thread, time

i =0

def counter(id): 
     print 'ID %s --> start' % (id)
     time.sleep(30)
     print '%s >>>>>>>> fin'%(id)

while True:
    i=i+1
    thread.start_new_thread(counter, (i,))
    time.sleep(5)

