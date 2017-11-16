import os
import sublime
import threading
import json
import urllib
import urllib.parse
import socket
import subprocess
import traceback
import sys
import signal
import codecs

from .helpers import *
from .urllib3 import PoolManager

IS_EXTERNAL_SERVER_ENABLE = False

launcher_procs = {
}

server_ports = {
}

pool = PoolManager(headers={'Content-Type': 'application/json; charset=UTF-8'})

readycount = 0


class WorkerThread(threading.Thread):
    def __init__(self, url, data, callback, timeout):
        threading.Thread.__init__(self)
        self.url = url
        self.data = data
        self.callback = callback
        self.timeout = timeout

    def run(self):
        try:
            print('======== request ======== \n Url: %s \n Data: %s' % (self.url, self.data))

            response = pool.urlopen('POST', self.url, body=self.data, timeout=self.timeout).data

            if not response:
                print('======== response ======== \n response is empty')
                self.callback(None)
            else:
                if response.startswith(codecs.BOM_UTF8):
                    decodeddata = response.decode('utf-8-sig')
                else:
                    decodeddata = response.decode('utf-8')

                print('======== response ======== \n %s' % decodeddata)
                self.callback(json.loads(decodeddata))

            print('======== end ========')
        except Exception as ex:
            if "checkalivestatus" not in self.url:
                print(str(ex))
                set_omnisharp_status("Error talking to " + self.url)
            else:
                set_omnisharp_status("Server Not Running")
            self.callback(None)


def get_response(view, endpoint, callback, params=None, timeout=None, needs_buffer=True):
    solution_path = current_solution_filepath_or_project_rootpath(view)

    if solution_path is None or solution_path not in server_ports:
        callback(None)
        return

    location = view.sel()[0]
    cursor = view.rowcol(location.begin())

    parameters = {}
    parameters['line'] = str(cursor[0] + 1)
    parameters['column'] = str(cursor[1] + 1)
    if needs_buffer:
        parameters['buffer'] = view.substr(sublime.Region(0, view.size()))
    parameters['filename'] = view.file_name()

    if params is not None:
        parameters.update(params)

    if timeout is None:
        timeout = int(get_settings(view, 'omnisharp_response_timeout'))

    host = 'localhost'
    port = server_ports[solution_path]

    url = "http://%s:%s%s" % (host, port, endpoint)
    data = json.dumps(parameters)

    thread = WorkerThread(url, data, callback, timeout)
    thread.start()


def _available_port():
    if IS_EXTERNAL_SERVER_ENABLE:
        return 2000

    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()

    return port


def restart_omnisharp_server_subprocess(view):
    def omnisharp_onclose_cb():
        create_omnisharp_server_subprocess(view)

    close_omnisharp_server_subprocess(view, omnisharp_onclose_cb)

def start_process(args):
    server_proc = None
    if os.name == "nt":
        # linux subprocess module does not have STARTUPINFO
        # so only use it if on Windows
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.SW_HIDE | subprocess.STARTF_USESHOWWINDOW
        server_proc = subprocess.Popen(args,
                                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=si, bufsize=-1)
    else:
        print("opening " + node_path + " " + script_path)
        server_proc = subprocess.Popen(args,
                                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, bufsize=-1)
    return server_proc

def create_omnisharp_server_subprocess(view):
    set_omnisharp_status("Server Starting")

    solution_path = current_solution_filepath_or_project_rootpath(view)
    if solution_path in launcher_procs:
        print("already_bound_solution:%s" % solution_path)
        return

    print("solution_path:%s" % solution_path)

    omni_port = _available_port()
    print('omni_port:%s' % omni_port)

    if IS_EXTERNAL_SERVER_ENABLE:
        launcher_proc = None
        omni_port = 2000
    else:
        try:
            omni_exe_path = get_omni_path(view)
            config_file = get_config_path(view)

            args = [
                omni_exe_path,
                '-s', solution_path,
                '-p', str(omni_port),
                '--hostPID', str(os.getpid())
            ]

            if config_file is not None:
                args.append('-config')
                args.append(quote_path(config_file))

            cmd = ' '.join(args)
            print(cmd)

            start_process(args)
            view.window().run_command("hide_panel", {"panel": "output.exec"})

            fn = view.file_name()
            file_name = '' if fn is None else fn
            print('Starting server: ' + view.name() + ' ' + file_name)

            set_omnisharp_status("Loading Project")
            sublime.set_timeout(lambda: check_solution_ready_status(view), 5000)

        except Exception as e:
            print('RAISE_OMNI_SHARP_LAUNCHER_EXCEPTION:%s' % repr(e))
            set_omnisharp_status("Error Launching Server")
            return

    launcher_procs[solution_path] = True
    server_ports[solution_path] = omni_port


def close_omnisharp_server_subprocess(view, cb=None):
    def close_omnishar_handler(statusmsg):
        print(statusmsg)

        solution_path = current_solution_filepath_or_project_rootpath(active_view())
        if solution_path in server_ports:
            server_ports.pop(solution_path)
        if solution_path in launcher_procs:
            launcher_procs.pop(solution_path)

        if cb:
            cb()

    get_response(view, "/stopserver", close_omnishar_handler)
    set_omnisharp_status("Server Shutting Down")


def set_omnisharp_status(statusmsg):
    sublime.active_window().active_view().set_status("OmniSharp", "OmniSharp : " + statusmsg)


def check_solution_ready_status(view):
    get_response(view, "/checkreadystatus", ready_status_handler, needs_buffer=False)


def ready_status_handler(data):
    global readycount
    if data == False:
        readycount += 1
        if readycount < 5:
            sublime.set_timeout(lambda: check_solution_ready_status(sublime.active_window().active_view()), 5000)
        else:
            set_omnisharp_status("Error Loading Project")
            readycount = 0
    elif data == True:
        readycount = 0
        set_omnisharp_status("Project Loaded")
        sublime.set_timeout(lambda: check_server_alive_status(sublime.active_window().active_view()), 5000)


def check_server_alive_status(view):
    get_response(view, "/checkalivestatus", alive_status_handler)


def alive_status_handler(data):
    if data == False:
        # I don't expect this to get hit because if its not running it wil throw exception
        set_omnisharp_status("Server Not Running")
    elif data == True:
        set_omnisharp_status("Server Running")
        sublime.set_timeout(lambda: check_server_alive_status(sublime.active_window().active_view()), 5000)
