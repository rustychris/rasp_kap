import os
import glob
import flask
import kap_camera
import time
from werkzeug.debug import DebuggedApplication

static_dir="static"
capture_dir=os.path.join(static_dir,'capture')
os.path.exists(capture_dir) or os.makedirs(capture_dir)

def gen_capture_filename():
    i=0
    while 1:
        fn=os.path.join(capture_dir,"img%04d.jpg"%i)
        if not os.path.exists(fn):
            yield fn
        i+=1
        
next_filename=gen_capture_filename().next            
last_capture=None


camera=kap_camera.camera_factory()

app = flask.Flask(__name__)

@app.route("/")
@app.route("/index.html")
def index():
    return flask.render_template('index.html')

@app.route("/capture/")
def capture():
    print "Top of capture"
    params=dict(full_image=last_capture,
                now_text="no now_text",
                camera_state=camera.state)
    print "Rendering template"
    return flask.render_template('capture.html',**params)

@app.route('/capture/action')
def cmd():
    a = flask.request.args.get('cmd', "nop", type=str)

    print flask.request.args
    
    if a=='initialize':
        camera.initialize()
    elif a=='preview':
        camera.shoot_preview(next_filename())
    elif a=='capture':
        camera.shoot_full(next_filename())
    elif a=='refresh':
        pass
    else:
        print "Command was ",a

    return status()

@app.route('/capture/status_and_actions')
def status():
    params=dict(now_text=time.asctime(),
                camera_state=camera.state,
                status_transient=camera.transient())

    last_capture=camera.last_capture
    if last_capture:
        last_capture=last_capture.replace(static_dir+"/","")
    params['last_capture']=last_capture
    
    s=flask.render_template('status_and_actions.html',**params)
    return s
    

if __name__ == "__main__":
    app.run(host="0.0.0.0",debug=True)
