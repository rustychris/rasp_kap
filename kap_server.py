"""
bare bones HTML interface to kite-bound raspberry pi with camera board
"""

#################
# web server

# assumes that it's being run from the same directory as this file
import os,time

from BaseHTTPServer import  BaseHTTPRequestHandler, HTTPServer
from mako.template import Template
from mako.lookup import TemplateLookup
from SocketServer import ThreadingMixIn
import urlparse

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass

class MyHandler(BaseHTTPRequestHandler):
    doc_root = "html"
    mako_mods = "mako_mods"
    def content_type_from_name(self,fn):
        """ returns a mimetype based on the extension.
        """
        if fn.endswith('.jpg'):
            return 'image/jpeg'
        elif fn.endswith('.html'):
            return 'text/html'
        else:
            return 'application/unknown'

    def choose_controller(self,path):
        """ a path like /foo.html maps to the function self.foo_controller(...)
        if the file extension is not html, or the controller function doesn't exist,
        the default controller is returned
        """
        print "Choosing controller for path",path
        if path.endswith('.html'):
            parts = path[1:].split('/')
            name,ext = os.path.splitext(parts[0])

            controller_name = name + "_controller"
            if hasattr(self,controller_name):
                return getattr(self,controller_name)
            else: # default
                return self.default_controller
        else:
            return self.default_controller

    def default_controller(self,vals):
        return vals

    def sleep_controller(self,vals):
        """ for testing multithreading
        """ 
        time.sleep(10)
        vals['duration'] = "10"
        return vals

    image_count = -1
    image_subdir = 'photos'
    def next_image_filename(self):
        path_tmpl = "/" + self.image_subdir + "/photo%05d.jpg"
        if self.image_count < 0:
            self.image_count = 0
            while 1:
                fn = path_tmpl%self.image_count
                if not os.path.exists(self.doc_root + fn ):
                    break
                self.image_count += 1
        else:
            self.image_count += 1
        return path_tmpl%self.image_count

    def status_and_actions_controller(self,vals):
        vals['cmd'] = ['none']
        return self.capture_controller(vals)
    
    def capture_controller(self,vals):
        vals['log_stack'] = camera.log_stack
        vals['full_image'] = None
        vals['now'] = time.time()
        vals['now_text'] = time.ctime()
        
        if vals.has_key('cmd'):
            cmd = vals['cmd'][0]
        else:
            cmd = 'none'
            
        if cmd == 'initialize':
            if camera.state == 'uninitialized':
                camera.async_initialize()
        elif camera.state == 'ready':
            if cmd == 'preview':
                camera.update_preview(dest='html/photos/preview.jpg')
            elif cmd == 'capture':
                vals['full_image'] = self.next_image_filename()
                camera.shoot_full(self.doc_root + vals['full_image'])
                
        vals['camera_state'] = camera.state
        print "Cmd is ",cmd
        print "Camera transient",camera.transient
        vals['camera_transient'] = (cmd!='none' or camera.transient())
        
        return vals
    
    def do_GET(self):
        # pre-populate dict for the controller
        vals = {}
        # split self.path into filename and query parts
        parsed = urlparse.urlparse(self.path)
        
        # the filename which will by default be parsed and sent back
        vals['FILENAME'] = self.doc_root+parsed.path
        query = urlparse.parse_qs(parsed.query)
        vals.update( dict( ((k.lower(),query[k]) for k in query.keys()) ) )
        vals['CONTENT_TYPE'] = self.content_type_from_name(vals['FILENAME'] )
        vals['RESPONSE_CODE'] = 200

        controller = self.choose_controller(parsed.path)
        vals = controller(vals) # do the work, update values...
        
        fn = vals['FILENAME']
        
        if not os.path.exists(fn):
            self.send_error(404,'File not found: %s'%fn)
            return
        
        self.send_response(vals['RESPONSE_CODE'])
        self.send_header('Content-type', vals['CONTENT_TYPE'])
        self.end_headers()
        
        if fn.endswith(".html"):
            # assume everything is a mako template
            # setup variables exposed in the template:
            mylookup = TemplateLookup(directories=['.'])
            doc = Template(filename=fn,lookup=mylookup)
            print "About to render, with vals:"
            print vals
            self.wfile.write(doc.render(**vals))
            return
        else:
            # blindly send file
            f=open(fn,'rb')
            self.wfile.write(f.read())
            f.close()
            return

import kap_camera
camera = kap_camera.Camera()

def main():
    try:
        server = ThreadedHTTPServer( ('',8888), MyHandler)
        print 'starting server'
        server.serve_forever()
    except KeyboardInterrupt:
        print "Keyboard interrupt"
        server.socket.close()
        
main()
