import sublime_plugin, sublime, json, webbrowser
import re
from time import time
from ..lib import omnisharp
from ..lib import helpers

class OmniSharpTooltipListener(sublime_plugin.EventListener):

    next_run_time = 0

    def on_activated(self, view):
        if not helpers.is_csharp(view):
            return
        self._check_tooltip_after_delay(view)
        view.settings().set('show_definitions', False)

    def on_modified(self, view):
        if not helpers.is_csharp(view):
            return

        self._check_tooltip_after_delay(view)

    def on_hover(self, view, point, hover_zone):
        if not helpers.is_csharp(view):
            return
        if hover_zone != sublime.HOVER_TEXT:
            return

        self._show_documentation_after_delay(view, point)

    def _show_documentation_after_delay(self, view, point):
        timeout_ms = 400
        self.next_run_time = time() + 0.0009 * timeout_ms
        sublime.set_timeout(lambda:self._show_documentation_after_delay_callback(view, point), timeout_ms)

    def _show_documentation_after_delay_callback(self, view, point):
        if self.next_run_time > time():
            return

        if view.window() == None:
            return

        line, column = view.rowcol(point)
        extraParams = {'includeDocumentation': True, 'line': line + 1, 'column': column + 1}
        omnisharp.get_response(view, '/typelookup', lambda data: self._showTooltip(view, point, data), extraParams)

    def on_selection_modified(self, view):
        self._check_tooltip_after_delay(view)

    def _check_tooltip_after_delay(self, view):
        timeout_ms = 400
        self.next_run_time = time() + 0.0009 * timeout_ms
        sublime.set_timeout(lambda:self._check_tooktip_after_delay_callback(view), timeout_ms)

    def _check_tooktip_after_delay_callback(self, view):
        if self.next_run_time <= time():
            self._check_tooltip(view)

    def encode_html(self, html):
        return html.replace('<', '&lt;').replace('>', '&gt;')

    def _showTooltip(self, view, point, data):
        if data == None:
            return
        type = data['Type']

        html = ''
        if type != None:
            html = '<p><strong>{0}</strong></p>'.format(self.encode_html(type))

        documentation = data['Documentation']

        if documentation != None:
            html = html + '<p>' + self.encode_html(documentation) + '</p>'

        if len(html) > 0:
            html = '<html><body id="omnisharp-tooltip"><style>p {margin-top:1px;margin-bottom:1px}</style>' + html + '</body></html>'
            view.show_popup(html, location=point, max_width=600, on_navigate=self.on_navigate)
            print(html)

    def _check_tooltip(self, view):

        view_settings = view.settings()
        if view_settings.get('is_widget'):
            return

        oops_map = view.settings().get("oops")
        if None == oops_map:
            return

        for region in view.sel():

            row_col = view.rowcol(region.begin())
            word_region = view.word(region.begin())
            word = view.substr(word_region)

            key = "%s,%s" % (word_region.a, word_region.b)
            if key not in oops_map:
                key = "%s,%s" % (region.begin(), region.begin() + 1)
                if key not in oops_map:
                    continue
            issue = oops_map[key]

            css = "html {background-color: #232628; color: #CCCCCC; } body {font-size: 12px; } a {color: #6699cc; } b {color: #cc99cc; } h1 {color: #99cc99; font-size: 14px; }"
            html = ['<style>%s</style>' % css]
            html.append(issue)

            view.show_popup(''.join(html), location=-1, max_width=600, on_navigate=self.on_navigate)

            return

        view.hide_popup()

    def on_navigate(self, link):
        return

