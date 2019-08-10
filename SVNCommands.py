import sublime
import sublime_plugin
import re
import subprocess

from .lib import util, settings

class MeeseeksCommand(sublime_plugin.WindowCommand):
    """ Used to fun abstract functions used by all commands """

    def run_command(self, command, files=None, flags=''):
        """ Used to run a basic command line call to svn """
        util.debug('Running cmd: ' + command)

        # chech for user defined svn.exe
        svn_path = settings.get('svn_path')
        if svn_path is False:
            svn_path = 'svn'
        #need double quotes for globbing
        command = svn_path+' '+command+' '+flags+' "'+files+'"'

        # work around to keep console from poping up
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # execute command and return decoded output
        # todo consider replacing Popen with call/run function
        out, err = subprocess.Popen(command, 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    startupinfo=startupinfo).communicate()
        if err:
            util.debug ('command error')
            util.debug (err.decode('utf-8').replace('\r', ''))
            return err.decode('utf-8').replace('\r', ''), False
        return out.decode('utf-8').replace('\r', ''), True
        #todo, add success/fail return


class SvnStatusCommand(MeeseeksCommand):
    """ Used to run a status check on all files in the project """

    def run(self, paths=None):
        """ Callback function for svn_status command """
        util.debug('Run status cmd')

        # get the path to show status
        file, file_name = util.get_files(paths)
        out, status = self.run_command(command='status', files=file)

        # set up and display output
        panel = sublime.active_window().create_output_panel('status')
        panel.set_syntax_file('Packages/MeeseeksSVN/syntax/status.sublime-syntax')
        panel.settings().set('color_scheme', 'Packages/MeeseeksSVN/syntax/status.hidden-tmTheme')
        sublime.active_window().run_command('show_panel',{'panel':'output.status'})
        out = self.format_info(out)
        panel.run_command('append', {'characters': out})

    def format_info(self, message):
        """ Returns html formatted string to display status report """
        message = message.split('\n')
        message.pop() # remove empty end string due to \n
        html_message = ''
        # todo add in settings to show modified/deleted/all/untracked, etc
        print ('mod:' + str(settings.get('show_modified')))
        for mes in message:
            status = mes.split()[0]
            if status is 'M' and settings.get('show_modified'):
                html_message +=(mes + '\n')
            elif status is 'D' and settings.get('show_deleted'):
                html_message +=(mes + '\n')
            elif status is '?' and settings.get('show_untracked'):
                html_message +=(mes + '\n')
            elif status is 'A' and settings.get('show_added'):
                html_message +=(mes + '\n')

        return html_message


class SvnShowDiffCommand(sublime_plugin.TextCommand):
    """ Show a view of the file differences """

    def run(self, edit, paths=None):
        """ Callback to execute command """
        util.debug('Run show diff cmd')

        # get the file/folder path and name
        file, file_name = util.get_files(paths)

        # get settings and run command
        lines = settings.get('context_lines')
        out, status = MeeseeksCommand.run_command(self, 
                                          command='diff', 
                                          files=file, 
                                          flags='--diff-cmd=diff -x -U' + str(lines))

        # yes this is ugly but it works...
        out = out.replace('Index:', '\n\nIndex:')
        out = out.replace('\n', 'Diff for '+file_name, 1)

        # Create new view and give output
        # Note the use of syntax highlighting
        diff_view = sublime.active_window().new_file()
        diff_view.insert(edit, 0, out)
        diff_view.set_name(file_name + ' - Diff View')
        diff_view.set_scratch(True)
        diff_view.set_read_only(True)
        diff_view.set_syntax_file('Packages/MeeseeksSVN/syntax/diff.sublime-syntax')
        diff_view.settings().set('color_scheme', 'Packages/MeeseeksSVN/syntax/diff.hidden-tmTheme')


#todo this needs to be only a view command?
class SvnGutterDiffCommand(MeeseeksCommand):
    """ Shows in the gutter what changes have been made """

    def run(self):
        """ Callback to run command """
        util.debug('Run gutter diff cmd')
        file = sublime.active_window().active_view().file_name().replace('\\', '/')

        # create variable to change context size for easier processing
        out, status = self.run_command(command='diff', files=file, flags='--diff-cmd=diff -x -U0')
        added, removed = self.get_regions(out)
        sublime.active_window().active_view().add_regions(
            key='inserted', regions=added, 
            scope='markup.inserted', icon='Packages/MeeseeksSVN/icons/inserted.png', 
            flags=sublime.HIDDEN | sublime.PERSISTENT)
        # sublime.active_window().active_view().add_regions(
        #     key='inserted', regions=removed, 
        #     scope='markup.deleted', icon='Packages/MeeseeksSVN/icons/deleted_top.png')#, 
        #     #flags=sublime.HIDDEN | sublime.PERSISTENT)

    def get_regions(self, message):
        """ Gets the added and removed lines to mark """
        message = message.split('\n')
        message.pop() # get rid of empty string at end
        view = sublime.active_window().active_view()
        added = []
        removed = []

        # cycle through each line
        for index, mes in enumerate(message):
            line = message[index]
            # signal for a change
            if line[0] is '@':
                beg = line.index('+')
                end = line.index('@', beg)
                change = [int(a) for a in line[beg+1:end-1].split(',')]
                # multiple lines changed
                if len(change) is 2:
                    for x in range(change[1]):
                        point1 = sublime.active_window().active_view().text_point(change[0]-1, 0)
                        region = view.line(point1)#sublime.Region(point1, point1+1)
                        added.append(region)
                        change[0] += 1
                # only one line changed
                else:
                    point1 = sublime.active_window().active_view().text_point(change[0]-1, 0)
                    region = view.line(point1)#sublime.Region(point1, point1+1)
                    added.append(region)

                    # one day i will get deleted lines working
                # beg = line.index('-')
                # end = line.index('+', beg)
                # change = [int(a) for a in line[beg+1:end-1].split(',')]
                # # multiple lines changed
                # if len(change) is 2:
                #     for x in range(change[1]):
                #         point1 = sublime.active_window().active_view().text_point(change[0]-1, 0)
                #         region = view.line(point1)#sublime.Region(point1, point1+1)
                #         removed.append(region)
                #         change[0] += 1
                # # only one line changed
                # else:
                #     point1 = sublime.active_window().active_view().text_point(change[0]-1, 0)
                #     region = view.line(point1)#sublime.Region(point1, point1+1)
                #     removed.append(region)

        return added, removed # todo set region as whole line


class SvnAddCommand(MeeseeksCommand):
    """ Command to add a file/folder to the svn commit """

    def run(self, paths=None):
        util.debug ('Run add cmd')

        file, file_name = util.get_files(paths)
        out, status = self.run_command(command='add', files=file)

        # check for success
        if status:
            util.debug ('File added')
            # todo, add setting for popup
            sublime.active_window().active_view().show_popup(
                    content='File Added', max_width=2000, max_height=3000)
        else:
            util.debug ('File not added')
            util.debug (out)
            sublime.active_window().active_view().show_popup(
                    content='Add Failed!', max_width=2000, max_height=3000)


class SvnCommitCommand(MeeseeksCommand):
    """ Command to commit the state to the svn repo """

    def run(self, paths=None):
        util.debug ('Run commit cmd')


class SvnUpdateCommand(MeeseeksCommand):
    """ Command to update the local svn copy """

    def run(self, paths=None):
        util.debug ('Run update cmd')


class SvnRevertCommand(MeeseeksCommand):
    """ Revert the file/folder to its unchanged state """

    def run(self, paths=None):
        util.debug ('Run revert cmd')

        file, file_name = util.get_files(paths)
        out, status = self.run_command(command='revert', files=file)

        if status:
            util.debug ('File reverted')
            # todo, add setting for popup
            sublime.active_window().active_view().show_popup(
                    content='File Reverted', max_width=2000, max_height=3000)
        else:
            util.debug ('File not reverted')
            util.debug (out)
            sublime.active_window().active_view().show_popup(
                    content='Revert Failed!', max_width=2000, max_height=3000)

#todo should probably be text command...
class SvnLogCommand(MeeseeksCommand):
    """ Command to show the log of the svn repo """

    def run(self, paths=None):
        util.debug ('Run log cmd')


class MeeseeksEvents(sublime_plugin.EventListener):
    """ Plan to have live updates, need to get run cmd working properly """

    def on_load(self, view):
        """ Set gutter diff on file load """
        util.debug ('file loaded')
        sublime.Window.run_command(view.window(), cmd='svn_gutter_diff')

    def on_post_save(self, view):
        """ Set gutter diff on file save """
        util.debug ('file saved')
        sublime.Window.run_command(view.window(), cmd='svn_gutter_diff')

    def on_modified(self, view):
        """ Set gutter diff on modification """
        # slows everything down right now, looking for fix
        util.debug ('file modified')
