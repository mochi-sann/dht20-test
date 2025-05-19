import mh_z19
import time 

def read():
    out = mh_z19.read()
    return str(out)[8:-1]

def read_all():
    out = mh_z19.read_all()
    return str(out)[8:-1]
if __name__=='__main__':
    while True : 

      co2=read()
      co2_all=read_all()
      print(co2)
      print(co2_all)
      time.sleep(2)

