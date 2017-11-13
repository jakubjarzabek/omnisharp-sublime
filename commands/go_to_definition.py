import sublime
import sublime_plugin

from ..lib import omnisharp
from ..lib import helpers


class OmniSharpGoToDefinition(sublime_plugin.TextCommand):
    def run(self, text):
        self.edit = text
        omnisharp.get_response(
            self.view, '/gotodefinition', self._handle_gotodefinition, params={'WantMetadata': True}, needs_buffer=False)

    def _handle_gotometadata(self, data):
        metadata_view = self.view.window().new_file()
        metadata_view.run_command('omni_sharp_show_metadata', data)
    
    def _handle_gotodefinition(self, data):
        if data is None:
            return

        if data['FileName'] is None:
            metadata = data['MetadataSource']
            if not (metadata is None):
                print('Load metadata')
                omnisharp.get_response(
                self.view, '/metadata', self._handle_gotometadata, params=metadata, needs_buffer=False)
            return

        filename = data['FileName']
        line = data['Line']
        column = data['Column']
        


        sublime.active_window().open_file(
            '{}:{}:{}'.format(filename, line or 0, column or 0),
            sublime.ENCODED_POSITION)

    def is_enabled(self):
        return helpers.is_csharp(self.view)
