import threading,subprocess,os,time

class Camera(object):
    """ A wrapper for access to the camera, with locking to keep things kosher
    with concurrent access via the webserver.
    """
    fake = False

    transient_states = ['capturing']

    raspistill="raspistill"
    warmup_ms=2000
    
    def __init__(self):
        """ this function is not synchronized.  
        """
        self.state = "uninitialized"
        self.log_stack = []
        self.log_lock = threading.Lock()
        self.lock = threading.Lock()

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
        locked = self.lock.acquire(blocking=False)
        try:
            txt = ["Lock: %s"%locked,
                   self.state ]
            return txt
        finally:
            if locked:
                self.lock.release()

    def update_preview(self,dest='preview.jpg'):
        if os.path.exists(dest):
            os.unlink(dest)
            
        with self.lock:
            if self.state != 'ready':
                print "trying to preview, state is bad: %s"%self.state
                return False
            self.state = "capturing"
            self._capture_preview(dest)
            self.state = "ready"

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

    def shoot_full(self,dest):
        print "Shooting, saving to ",dest
        
        if os.path.exists(dest):
            os.unlink(dest)
        with self.lock:
            print "Acquired camera lock"
            if self.state != 'ready':
                print "State should be 'ready', but it's ",self.state
                return False
            self.state = 'capturing'
            print "Calling capture"
            self._capture_image(dest)
            print "Back from capture"
            self.state = 'ready'
    def transient(self):
        return self.state in self.transient_states
