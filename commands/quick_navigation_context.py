import sublime
import sublime_plugin

from ..lib import helpers

class OmniSharpQuickNavigationMenu(sublime_plugin.TextCommand):
    def run(self, edit):
        cmds = ['omni_sharp_find_usages', 'omni_sharp_go_to_definition', 'omni_sharp_go_to_implementation']
        def on_done(idx):
            if idx < 0 or idx > len(cmds):
                return
            sublime.active_window().run_command(cmds[idx])
            
        self.view.show_popup_menu(['Find Usages', 'Go to definition', 'Go to implementation'], on_done)

    def is_enabled(self):
        return helpers.is_csharp(self.view)
