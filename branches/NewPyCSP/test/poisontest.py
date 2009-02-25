from common import *
from pycsp import *
import random

@choice
def action(ChannelInput=None):
    print '.',

@process
def reader(c, id,  sleeper):
    try:
        while True:
            if sleeper: sleeper()
            got=c.read()
            print '.',
    except Exception:
        print
    
@process
def writer(c, id, cnt, sleeper):
    try:
        for i in range(cnt):
            if sleeper: sleeper()
            c.write((id, i))
        c.poison()
    except:
        pass

@process
def par_reader(c1,c2,c3,c4, cnt, sleeper):
    try:
        while True:
            if sleeper: sleeper()
            Alternation({c1:action(), c2:action(), c3:action(), c4:action()}).execute()
    except ChannelPoisonException, e:
        c1.poison()
        c2.poison()
        c3.poison()
        c4.poison()

@process
def par_writer(c1,c2,c3,c4, cnt, sleeper):
    try:
        for i in range(cnt*4):
            if sleeper: sleeper()
            Alternation({(c1, i):None, (c2,i):None, (c3,i):None, (c4,i):None}).execute()
    except ChannelPoisonException, e:
        pass
    c1.poison()
    c2.poison()
    c3.poison()
    c4.poison()
    
def sleep_one():
    time.sleep(0.5)

def sleep_random():
    time.sleep(random.random())

def One2One_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    Parallel(reader(c1,0, read_sleeper), writer(c1,1,10, write_sleeper))
    print
    
def Any2One_Alting_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(par_reader(c1,c2,c3,c4,cnt, read_sleeper),
             writer(c1,0,cnt, write_sleeper),
             writer(c2,1,cnt, write_sleeper),
             writer(c3,2,cnt, write_sleeper),
             writer(c4,3,cnt, write_sleeper))
    print

def Any2Any_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    cnt = 10

    Parallel(reader(c1,0, read_sleeper), writer(c1,0,cnt, write_sleeper),
             reader(c1,1, read_sleeper), writer(c1,1,cnt, write_sleeper),
             reader(c1,2, read_sleeper), writer(c1,2,cnt, write_sleeper),
             reader(c1,3, read_sleeper), writer(c1,3,cnt, write_sleeper))
    
def Any_Alting2Any_Alting_Test(read_sleeper, write_sleeper):
    c1=Channel('C1')
    c2=Channel('C2')
    c3=Channel('C3')
    c4=Channel('C4')

    cnt = 10
    
    Parallel(par_writer(c1,c2,c3,c4,cnt, write_sleeper),
             par_writer(c1,c2,c3,c4,cnt, write_sleeper),
             par_writer(c1,c2,c3,c4,cnt, write_sleeper),
             par_writer(c1,c2,c3,c4,cnt, write_sleeper),
             par_reader(c1,c2,c3,c4,cnt, read_sleeper),
             par_reader(c1,c2,c3,c4,cnt, read_sleeper),
             par_reader(c1,c2,c3,c4,cnt, read_sleeper),
             par_reader(c1,c2,c3,c4,cnt, read_sleeper))
    print

    
def poisontest():
    for read_sleep in [('Zero', None), ('One',sleep_one), ('Random',sleep_random)]:
        for write_sleep in [('Zero', None), ('One',sleep_one), ('Random',sleep_random)]:
            rname, rsleep = read_sleep
            wname, wsleep = write_sleep

            if not rsleep==wsleep==sleep_one:
                print '***',rname,wname,'***'
                print 'One2One_Test'
                One2One_Test(rsleep, wsleep)
                print 'Any2One_Alting_Test()'
                Any2One_Alting_Test(rsleep, wsleep)
                print 'Any2Any_Test()'
                Any2Any_Test(rsleep, wsleep)
                print 'Any_Alting2Any_Alting_Test()'
                Any_Alting2Any_Alting_Test(None,None)


poisontest()
