import sublime
import sublime_plugin
import re
import subprocess

from .lib import util, settings

STATUS_SYNTAX = 'Packages/MeeseeksSVN/syntax/status.sublime-syntax'
STATUS_THEME = 'Packages/MeeseeksSVN/syntax/status.hidden-tmTheme'
DIFF_SYNTAX = 'Packages/MeeseeksSVN/syntax/diff.sublime-syntax'
DIFF_THEME = 'Packages/MeeseeksSVN/syntax/diff.hidden-tmTheme'
LOG_SYNTAX = 'Packages/MeeseeksSVN/syntax/log.sublime-syntax'
LOG_THEME = 'Packages/MeeseeksSVN/syntax/log.hidden-tmTheme'

INSERTED_PNG = 'Packages/MeeseeksSVN/icons/inserted.png'
DELETED_TOP_PNG = 'Packages/MeeseeksSVN/icons/deleted_top.png'


################################################################################
class MeeseeksCommand(sublime_plugin.WindowCommand):
    """ Used to fun abstract functions used by all commands """

    def run_command(self, command, flags='', message='', files=None):
        """ Used to run a basic command line call to svn """

        # chech for user defined svn.exe
        svn_path = settings.get('svn_path')
        if svn_path is False:
            svn_path = 'svn'

        # build command string, need double quotes for globbing
        command = svn_path+' '+command
        if flags is not '':
            command += ' '+flags
        if message is not '':
            command += ' "'+message+'"'
        if files is not None:
            command += ' "'+files+'"'

        util.debug('Running cmd: ' + command)

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


################################################################################
class SvnStatusCommand(MeeseeksCommand):
    """ Used to run a status check on all files in the project """

    def run(self, paths=None):
        """ Callback function for svn_status command """

        util.debug('Run status cmd')

        # get the path to show status
        file, file_name = util.get_files(paths)
        flags = ''
        if (settings.get('status_set_verbose')):
            flags = '-v'
        out, status = self.run_command(command='status',
                                       files=file, 
                                       flags=flags)

        # set up and display output
        panel = sublime.active_window().create_output_panel('status')
        panel.set_syntax_file(STATUS_SYNTAX)
        panel.settings().set('color_scheme', STATUS_THEME)
        sublime.active_window().run_command('show_panel',
                                            {'panel':'output.status'})
        out = self.format_info(out)
        panel.run_command('append', {'characters': out})

    def format_info(self, message):
        """ Returns html formatted string to display status report """

        message = message.split('\n')
        message.pop() # remove empty end string due to last \n
        html_message = ''
        for mes in message:
            status = mes.split()[0]
            if status is 'M' and settings.get('status_show_modified'):
                html_message +=(mes + '\n')
            elif status is 'D' and settings.get('status_show_deleted'):
                html_message +=(mes + '\n')
            elif status is '?' and settings.get('status_show_untracked'):
                html_message +=(mes + '\n')
            elif status is 'A' and settings.get('status_show_added'):
                html_message +=(mes + '\n')
            elif status is 'U' and settings.get('status_show_updated'):
                html_message +=(mes + '\n')
            elif status is 'C' and settings.get('status_show_conflict'):
                html_message +=(mes + '\n')
            elif status is 'G' and settings.get('status_show_merged'):
                html_message +=(mes + '\n')
        return html_message


################################################################################
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
                                          flags='--diff-cmd=diff -x -U'+str(lines))

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
        diff_view.set_syntax_file(DIFF_SYNTAX)
        diff_view.settings().set('color_scheme', DIFF_THEME)


################################################################################
class SvnGutterDiffCommand(MeeseeksCommand):
    """ Shows in the gutter what changes have been made """

    def run(self):
        """ Callback to run command """

        util.debug('Run gutter diff cmd')
        view = sublime.active_window().active_view()
        file = view.file_name().replace('\\', '/')

        # create variable to change context size for easier processing
        out, status = self.run_command(command='diff', 
                                       files=file, 
                                       flags='--diff-cmd=diff -x -U0')
        added, removed = self.get_regions(out)
        view.add_regions(
            key='inserted', regions=added, 
            scope='markup.inserted', icon=INSERTED_PNG, 
            flags=sublime.HIDDEN | sublime.PERSISTENT)
        # sublime.active_window().active_view().add_regions(
        #     key='inserted', regions=removed, 
        #     scope='markup.deleted', icon=DELETED_TOP_PNG)#, 
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
                        point1 = view.text_point(change[0]-1, 0)
                        region = view.line(point1)#sublime.Region(point1, point1+1)
                        added.append(region)
                        change[0] += 1
                # only one line changed
                else:
                    point1 = view.text_point(change[0]-1, 0)
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

        return added, removed


################################################################################
class SvnAddCommand(MeeseeksCommand):
    """ Command to add a file/folder to the svn commit """

    def run(self, paths=None):
        """ Callback to run command """

        util.debug ('Run add cmd')

        file, file_name = util.get_files(paths)
        out, status = self.run_command(command='add', files=file)

        util.pop_info('File Added', 'Add Failed!', status)


################################################################################
class SvnCommitCommand(MeeseeksCommand):
    """ Command to commit the state to the svn repo """

    file = None
    file_name = None

    def run(self, paths=None):
        """ Callback to run command """

        util.debug ('Run commit cmd')

        # save the file/folder to be committed
        self.file, self.file_name = util.get_files(paths)
        sublime.active_window().show_input_panel(caption='Commit Message: ', 
                                              initial_text='Updates to project',
                                              on_done=self.commit,
                                              on_change=None,
                                              on_cancel=self.cancel_commit)

    def commit(self, message):
        """ Called when commit message is ready """
        path = util.project_path()
        out, status = self.run_command(command='commit', 
                                       flags='-m', 
                                       message=message, 
                                       files=path)
        util.pop_info('File Committed', 'Commit Failed!', status)

    def cancel_commit(self):
        """ Called if commit is cancelled """
        util.debug ('Commit Cancelled')
        util.pop_info('Commit Cancelled', 'Commit Cancelled', True)


################################################################################
class SvnUpdateCommand(MeeseeksCommand):
    """ Command to update the local svn copy """

    def run(self, paths=None):
        """ Callback to run command """

        util.debug ('Run update cmd')

        file, file_name = util.get_files(paths)
        out, status = self.run_command(command='update', files=file)

        util.pop_info('File Updated', 'Update Failed!', status)


################################################################################
class SvnRevertCommand(MeeseeksCommand):
    """ Revert the file/folder to its unchanged state """

    def run(self, paths=None):
        """ Callback to run command """

        util.debug ('Run revert cmd')

        file, file_name = util.get_files(paths)
        out, status = self.run_command(command='revert', files=file)

        util.pop_info('File Updated', 'Update Failed!', status)


################################################################################
class SvnLogCommand(sublime_plugin.TextCommand):
    """ Command to show the log of the svn repo """

    def run(self, edit, paths=None):
        """ Callback to run command """

        util.debug ('Run log cmd')

        file, file_name = util.get_files(paths)
        flags = ''
        if settings.get('log_set_verbose'):
            flags = '-v'
        out, status = MeeseeksCommand.run_command(self, 
                                                  command='log', 
                                                  files=file, 
                                                  flags=flags)

        log_view = sublime.active_window().new_file()
        log_view.insert(edit, 0, out)
        log_view.set_name(file_name + ' - Log View')
        log_view.set_scratch(True)
        log_view.set_read_only(True)
        log_view.set_syntax_file(LOG_SYNTAX)
        log_view.settings().set('color_scheme', LOG_THEME)


################################################################################
class SvnBlameCommand(sublime_plugin.TextCommand):
    """ Command to show the blame log of the svn repo """

    def run(self, edit, paths=None):
        """ Callback to run command """

        util.debug ('Run blame cmd')

        file, file_name = util.get_files(paths)
        flags = ''
        if settings.get('blame_set_verbose'):
            flags = '-v'
        out, status = MeeseeksCommand.run_command(self, 
                                                  command='blame', 
                                                  files=file, 
                                                  flags=flags)

        log_view = sublime.active_window().new_file()
        log_view.insert(edit, 0, out)
        log_view.set_name(file_name + ' - Log View')
        log_view.set_scratch(True)
        log_view.set_read_only(True)


################################################################################
class SvnCheckRemoteCommand(sublime_plugin.TextCommand):
    """ Checks the remote copy for changes """

    util.debug ('Check for remote updates')
