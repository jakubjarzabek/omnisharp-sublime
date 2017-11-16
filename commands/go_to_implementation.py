import sublime
import sublime_plugin

from ..lib import omnisharp
from ..lib import helpers


class OmniSharpGoToImplementation(sublime_plugin.TextCommand):
    data = None

    def run(self, edit):
        omnisharp.get_response(
                self.view, '/findimplementations', self._show_usage_view)

    def _show_usage_view(self, data):
        if data is None or data["QuickFixes"] is None:
            return

        print('gotoimplementation is :')
        print(data)

        usages = data["QuickFixes"]

        if len(usages) == 0:
            return

        window = self.view.window()

        def on_done(i):
            if i is not -1:
                window.open_file('{}:{}:{}'.format(usages[i]["FileName"], usages[i]["Line"] or 0, usages[i]["Column"] or 0), sublime.ENCODED_POSITION)

        def on_highlight(i):
            if i is not -1:
                window.open_file('{}:{}:{}'.format(usages[i]["FileName"], usages[i]["Line"] or 0, usages[i]["Column"] or 0), sublime.ENCODED_POSITION | sublime.TRANSIENT)

        if len(usages) == 1:
            on_done(0)
            return

        items = [[u["Text"].strip(), u["FileName"] + " Line : " + str(u["Line"])] for u in usages]
        window.show_quick_panel(items, on_done, on_highlight=on_highlight)

    def is_enabled(self):
        return helpers.is_csharp(self.view)
