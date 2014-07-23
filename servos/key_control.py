import sys
import tty
import termios

def getch():
    fd=sys.stdin.fileno()
    old_settings=termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while 1:
            ch=sys.stdin.read(1)
            if ch=="\x03":
                # That's control-c
                return
            else:
                yield ch
    finally:
        termios.tcsetattr(fd,termios.TCSADRAIN,old_settings) 

def arrows():
    src=getch()
    try:
        while 1:
            ch=src.next()
            if ord(ch) != 27: # ESC
                print "What?\r"
                continue
            ch=src.next()
            if ord(ch) != 91: # [ 
                print "Huh?\r"
                continue
            ch=ord(src.next())
            if ch==65:
                yield 'up'
            elif ch==66:
                yield 'down'
            elif ch==67:
                yield 'right'
            elif ch==68:
                yield 'left'
    except StopIteration:
        return


# And the part that writes to the servo
fn="/dev/servoblaster"
lr_num=2
ud_num=1
min_val=70
max_val=290

val0=150
lr_val=val0
ud_val=val0
delta=5

def set_servo(num,val):
    with open(fn,'wt') as fp:
        fp.write("%d=%d\n"%(num,val))

for c in arrows():
    if c=='up' and ud_val<max_val:
        ud_val+=delta
        set_servo(ud_num,ud_val)
    elif c=='down' and ud_val>min_val:
        ud_val-=delta
        set_servo(ud_num,ud_val)
    elif c=='left' and lr_val>min_val:
        lr_val-=delta
        set_servo(lr_num,lr_val)
    elif c=='right' and lr_val<max_val:
        lr_val+=delta
        set_servo(lr_num,lr_val)    
    print "LR: %d  UD: %d\r"%(lr_val,ud_val)

set_servo(lr_num,val0)
set_servo(ud_num,val0)
print "Bye"

# the pan servo has a range of roughly 70-290.
# the tilt servo may go below 70, not sure.  and its upper end is 250

