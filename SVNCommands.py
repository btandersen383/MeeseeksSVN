import sublime
import sublime_plugin
import re
import subprocess

from .lib import util, settings

class MeeseeksCommand(sublime_plugin.WindowCommand):
    """ Used to fun abstract functions used by all commands """

    def run_command(self, command, files=None, flags=""):
        """ Used to run a basic command line call to svn """
        util.debug("Running cmd: " + command)
        command = 'svn '+command+' '+flags+' "'+files+'"' #need double quotes on path

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        out, err = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo).communicate()
        return out.decode("utf-8").replace("\r", "")


class SvnStatusCommand(MeeseeksCommand):
    """ Used to run a status check on all files in the project """

    def run(self, paths=None):
        """ Callback function for svn_status command """
        util.debug("Run status cmd")

        # eventually will pass a path to narrow status report
        if paths is None:
            file = util.project_path()
        else:
            file = paths[0]

        out = self.run_command(command='status', files=file)
        # info = self.format_info(out)
        # sublime.active_window().active_view().show_popup(
        #         content=info, max_width=2000, max_height=3000)

        panel = sublime.active_window().create_output_panel("status")
        panel.set_syntax_file('Packages/MeeseeksSVN/syntax/status.sublime-syntax')
        panel.settings().set('color_scheme', 'Packages/MeeseeksSVN/syntax/status.hidden-tmTheme')
        sublime.active_window().run_command('show_panel',{"panel":"output.status"})
        panel.run_command("append", {"characters": out})

    def format_info(self, message):
        """ Returns html formatted string to display status report """
        message = message.split("\n")
        message.pop()
        html_message = ''
        for mes in message:
            if mes[0] is 'M':
                html_message += ('<font style="color:#4455FF;">' + mes + '</font><br>')
            elif mes[0] is 'D':
                html_message +=('<font style="color:#FF5544">' + mes + '</font><br>')
        return html_message

# DEPRECIATED
# class SvnDiffCommand(MeeseeksCommand):

#     def run(self, path=None):
#         view = sublime.active_window().active_view()
#         file = sublime.active_window().active_view().file_name().replace('\\', '/')
        
#         # create variable to change context size
#         out = self.run_command(command='diff', files=file, flags='--diff-cmd=diff -x -U3')

#         diff_view = sublime.active_window().new_file()
#         args = {'diff':out}
#         diff_view.run_command("svn_show_diff", args)

#         # removed, added = self.get_regions(out)
#         # view.add_regions(key="removed", regions=added, icon="dot")


class SvnShowDiffCommand(sublime_plugin.TextCommand):
    """ Show a view of the file differences """

    def run(self, edit, paths=None):
        """ Callback to execute command """
        util.debug("Showing differences")

        view = sublime.active_window().active_view()
        if paths is None:
            file = sublime.active_window().active_view().file_name().replace('\\', '/')
            file_name = file.split('/').pop()
        else:
            file = paths[0]
            file_name = file.split('\\').pop()
        out = MeeseeksCommand.run_command(self, command='diff', files=file, flags='--diff-cmd=diff -x -U3')

        diff_view = sublime.active_window().new_file()
        diff_view.insert(edit, 0, out)
        diff_view.set_name(file_name + " - Diff View")
        diff_view.set_scratch(True)
        diff_view.set_read_only(True)
        diff_view.set_syntax_file('Packages/MeeseeksSVN/syntax/diff.sublime-syntax')
        diff_view.settings().set('color_scheme', 'Packages/MeeseeksSVN/syntax/diff.hidden-tmTheme')


#todo this needs to be only a view command?
class SvnGutterDiffCommand(MeeseeksCommand):
    """ Shows in the gutter what changes have been made """

    def run(self):
        """ Callback to run command """
        util.debug("Updating gutter with changes")
        file = sublime.active_window().active_view().file_name().replace('\\', '/')

        # create variable to change context size
        out = self.run_command(command='diff', files=file, flags='--diff-cmd=diff -x -U0')
        regions = self.get_regions(out)
        sublime.active_window().active_view().add_regions(
            key="mark", regions=regions, 
            scope="markup.inserted", icon="Packages/MeeseeksSVN/icons/inserted.png", 
            flags=sublime.HIDDEN | sublime.PERSISTENT)

    def get_regions(self, message):
        """ Gets the added and removed lines to mark """
        message = message.split("\n")
        message.pop()
        added = []
        for index, mes in enumerate(message):
            line = message[index]
            if line[0] is '@':
                beg = line.index('+')
                end = line.index('@', beg)
                change = [int(a) for a in line[beg+1:end-1].split(',')]
                if len(change) is 2:
                    for x in range(change[1]):
                        point1 = sublime.active_window().active_view().text_point(change[0]-1, 0)
                        region = sublime.Region(point1, point1+1)
                        added.append(region)
                        change[0] += 1
                else:
                    point1 = sublime.active_window().active_view().text_point(change[0]-1, 0)
                    region = sublime.Region(point1, point1+1)
                    added.append(region)

        return added # todo set region as whole line


class MeeseeksEvents(sublime_plugin.EventListener):
    """ Plan to have live updates, need to get run cmd working properly """

    def on_load(self, view):
        """ Set gutter diff on file load """
        util.debug ("file loaded")
        sublime.Window.run_command(view.window(), cmd="svn_gutter_diff")

    def on_post_save(self, view):
        """ Set gutter diff on file save """
        util.debug ("file saved")
        sublime.Window.run_command(view.window(), cmd="svn_gutter_diff")

    def on_modified(self, view):
        """ Set gutter diff on modification """
        # slows everything down right now, looking for fix
        util.debug ("file modified")
