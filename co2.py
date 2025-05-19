import mh_z19

def read():
    out = mh_z19.read()
    return str(out)[8:-1]
if __name__=='__main__':
    co2=read()
    print(co2)
