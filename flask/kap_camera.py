import threading,subprocess,os,time

class Camera(object):
    """ A wrapper for access to the camera, with locking to keep things kosher
    with concurrent access via the webserver.
    """
    fake = False

    transient_states = ['capturing']

    raspistill="raspistill"
    warmup_ms=2000
    
    def __init__(self,**kwargs):
        """ this function is not synchronized.  
        """
        self.state = "uninitialized"
        self.log_stack = []
        self.log_lock = threading.Lock()
        self.lock = threading.Lock()
        self.last_capture=None # relative path to the last completed image capture
        self.__dict__.update(kwargs)

    max_log_entries = 10
    def log(self,msg):
        with self.log_lock:
            self.log_stack.append( (msg,time.time()) )
            if len(self.log_stack) > self.max_log_entries:
                self.log_stack = self.log_stack[-self.max_log_entries:]
        
    def initialize(self):
        with self.lock:
            if self.state != 'uninitialized':
                return False

            self.state = 'ready'
            print "Initialized"
            return True

    def async_initialize(self):
        """ Call initialize in a separate thread, and return immediately
        """
        thr = threading.Thread(target=self.initialize)
        thr.start()
        
    def state_description(self):
        locked = self.lock.acquire(False)
        try:
            txt = ["Lock: %s"%locked,
                   self.state ]
            return txt
        finally:
            if locked:
                self.lock.release()

    def shoot(self,dest,mode='preview'):
        print "Shooting mode=%s saving to %s"%(mode,dest)
        
        if os.path.exists(dest):
            os.unlink(dest)
            
        with self.lock:
            print "Acquired camera lock"
            if self.state != 'ready':
                print "trying to shoot, yet state is not ready, but %s"%self.state
                return False
            self.state = "capturing"
            if mode=='full':
                self._capture_image(dest)
                self.last_capture=dest
            elif mode=='preview':
                self._capture_preview(dest)
                self.last_capture=dest
            else:
                print "Bad mode %s"%mode
                
            self.state = "ready"
        
    def shoot_preview(self,dest='preview.jpg'):
        return self.shoot(dest=dest,mode='preview')
    def shoot_full(self,dest):
        return self.shoot(dest=dest,mode='full')

    def _capture_preview(self,dest):
        print "Calling raspistill"
        retcode = subprocess.call([self.raspistill,
                                   "-o",dest,"-e","jpg","-n","-t","%i"%self.warmup_ms,
                                   "-w","320","-h","240"])
        print "Retcode is ",retcode
        return retcode == 0

    def _capture_image(self,dest):
        retcode = subprocess.call([self.raspistill,
                                   "-o",dest,"-e","jpg","-n","-t","%i"%self.warmup_ms,
                                   "-w","1024","-h","768"])
        return retcode == 0

    def transient(self):
        return self.state in self.transient_states


class FakeCamera(Camera):
    """ Simulate the camera for local development
    """
    fake = True

    def _gen_image(self,dest,px,py):
        import matplotlib.pyplot as plt
        res=100
        fig=plt.figure(figsize=(float(px)/res,float(py)/res))
        plt.text(0.1,0.8,time.asctime(),
                 transform=plt.gca().transAxes)
        plt.plot([0,10],[0,10],'r--')
        plt.savefig(dest,res=res)
        plt.close(fig)
        return True
        
    def _capture_preview(self,dest):
        print "Generating preview"
        return self._gen_image(dest,320,240)

    def _capture_image(self,dest):
        print "Generating preview"
        return self._gen_image(dest,1024,768)


def camera_factory(**kwargs):
    sysname,nodename,release,version,machine = os.uname()
    if machine.startswith('arm'):
        return Camera(**kwargs)
    else:
        return FakeCamera(**kwargs)
    
