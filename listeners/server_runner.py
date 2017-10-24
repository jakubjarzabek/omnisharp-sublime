import sublime_plugin

from ..lib import helpers
from ..lib import omnisharp


class OmniSharpServerRunnerEventListener(sublime_plugin.EventListener):

    def __init__(self):
        self.initialized = False

    def on_activated(self, view):
        if not helpers.is_csharp(view):
            return
        if self.initialized:
            print('Server already initialized')
            return
        print('Starting server: ' + view.name() + ' ' + view.file_name() + ' ' + str(self.initialized))
        self.initialized = True
        omnisharp.create_omnisharp_server_subprocess(view)

