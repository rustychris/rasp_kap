import os

class KapServo(object):
    # And the part that writes to the servo
    fn="/dev/servoblaster"
    
    lr_num=2
    ud_num=1
    min_val=70
    max_val=290
    val0=150
    
    def __init__(self):
        self.lr_val=self.val0
        self.ud_val=self.val0
        self.set_servo(self.lr_num,self.lr_val)
        self.set_servo(self.ud_num,self.ud_val)

    def set_servo(self,num,val):
        with open(self.fn,'wt') as fp:
            fp.write("%d=%d\n"%(num,val))

    def move_relative(self,direction,delta=2):
        c=direction
        if c=='up' and self.ud_val<self.max_val:
            self.ud_val+=delta
            self.set_servo(self.ud_num,self.ud_val)
        elif c=='down' and self.ud_val>self.min_val:
            self.ud_val-=delta
            self.set_servo(self.ud_num,self.ud_val)
        elif c=='left' and self.lr_val>self.min_val:
            self.lr_val-=delta
            self.set_servo(self.lr_num,self.lr_val)
        elif c=='right' and self.lr_val<self.max_val:
            self.lr_val+=delta
            self.set_servo(self.lr_num,self.lr_val)

    def pos_text(self):
        return "(%d,%d)"%(self.lr_val,self.ud_val)


class FakeServo(KapServo):
    def set_servo(self,num,val):
        print "Would set servo %d to %s"%(num,val)
        
def servo_factory(**kwargs):
    sysname,nodename,release,version,machine = os.uname()
    if machine.startswith('arm'):
        return KapServo(**kwargs)
    else:
        return FakeServo(**kwargs)
    
