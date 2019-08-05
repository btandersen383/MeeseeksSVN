import sublime
import sublime_plugin
import os
import os.path
import re
import subprocess

class MeeseeksCommand(sublime_plugin.WindowCommand):
    """Used to fun abstract functions used by all commands"""

    def run_command(self, command, files=None, flags=""):
        """Used to run a basic command line call to svn"""
        command = 'svn '+command+' '+flags+' "'+files+'"' #need double quotes on path
        out, err = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return out.decode("utf-8").replace("\r", "")

    def project_path(self):
        """Used to the the current project path, should be moved to util.py"""
        project_data = sublime.active_window().extract_variables()
        project_path = project_data["project_path"].replace('\\', '/')
        return project_path

    def debug(self, message):
        """Send output to console if debugging is enabled"""
        # if settings.get("debug", default=False):
        print('Meeseeks: ' + str(message))


class SvnStatusCommand(MeeseeksCommand):
    """Used to run a status check on all files in the project"""

    def run(self, path=None):
        """Callback function for svn_status command"""
        self.debug("run status cmd")

        # eventually will pass a path to narrow status report
        if path is None:
            path = self.project_path()

        out = self.run_command('status', path)
        # info = self.format_info(out)
        # sublime.active_window().active_view().show_popup(
        #         content=info, max_width=2000, max_height=3000)

        panel = sublime.active_window().create_output_panel("status")
        panel.set_syntax_file('Packages/MyFirstPlugin/syntax/status.sublime-syntax')
        panel.settings().set('color_scheme', 'Packages/MyFirstPlugin/syntax/status.hidden-tmTheme')
        sublime.active_window().run_command('show_panel',{"panel":"output.status"})
        panel.run_command("append", {"characters": out})

    def format_info(self, message):
        """Returns html formatted string to display status report"""
        message = message.split("\n")
        message.pop()
        html_message = ''
        for mes in message:
            if mes[0] is 'M':
                html_message += ('<font style="color:#4455FF;">' + mes + '</font><br>')
            elif mes[0] is 'D':
                html_message +=('<font style="color:#FF5544">' + mes + '</font><br>')
        return html_message


class SvnDiffCommand(MeeseeksCommand):

    def run(self):
        view = sublime.active_window().active_view()
        file = sublime.active_window().active_view().file_name().replace('\\', '/')
        
        # create variable to change context size
        out = self.run_command(command='diff', files=file, flags='--diff-cmd=diff -x -U3')

        diff_view = sublime.active_window().new_file()
        args = {'diff':out}
        diff_view.run_command("svn_show_diff", args)

        # removed, added = self.get_regions(out)
        # view.add_regions(key="removed", regions=added, icon="dot")


#todo this needs to be only a view command?
class SvnDiffGutterCommand(MeeseeksCommand):

    def run(self):
        file = sublime.active_window().active_view().file_name().replace('\\', '/')
                
        # create variable to change context size
        out = self.run_command(command='diff', files=file, flags='--diff-cmd=diff -x -U0')
        regions = self.get_regions(out)
        sublime.active_window().active_view().add_regions(
            key="mark", regions=regions, scope="string", icon="dot", flags=sublime.HIDDEN | sublime.PERSISTENT)

    def get_regions(self, message):
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

        return added


class SvnShowDiffCommand(sublime_plugin.TextCommand):

    def run(self, edit, diff):
        self.view.insert(edit, 0, diff)
        self.view.set_name("Diff View")
        self.view.set_scratch(True)
        self.view.set_read_only(True)
        self.view.set_syntax_file('Packages/MyFirstPlugin/syntax/diff.sublime-syntax')
        self.view.settings().set('color_scheme', 'Packages/MyFirstPlugin/syntax/diff.hidden-tmTheme')

        # removed, added = self.get_regions(diff)
        # print (added)
        # self.view.add_regions(key="mark", regions=added, scope="comment")

    # def get_regions(self, message):
    #     return message

    def get_regions(self, diff):
        diff = diff.split("\n")
        diff.pop()
        online = 0
        removed = []
        added = []
        for line in diff:
            if line[0] is '-':
                print (line)
                removed.append(self.view.text_point(online, 1))
            elif line[0] is '+':
                print(line)
                point = self.view.text_point(online, 1)
                added.append(self.view.line(point))
            online = online + 1

        return removed, added
