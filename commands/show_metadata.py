import sublime
import sublime_plugin

from os import path


class OmniSharpShowMetadata(sublime_plugin.TextCommand):
    def run(self, edit, SourceName, Source):
        self.view.set_name(path.basename(SourceName))
        self.view.insert(edit, 0, Source)
        self.view.set_read_only(True)
        self.view.set_scratch(True)
