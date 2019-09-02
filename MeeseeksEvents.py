import sublime
import sublime_plugin
import re
import subprocess

from .lib import util, settings

################################################################################
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
        # would be used to update gutter
        # slows everything down right now, looking for fix
        #util.debug ('file modified')
