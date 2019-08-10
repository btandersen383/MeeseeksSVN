import sublime
import os
import re

from . import settings

def project_path():
    """ Return the project path """
    project_data = sublime.active_window().extract_variables()
    project_path = project_data["project_path"].replace('\\', '/')
    return project_path

def debug(message):
    """ Send output to console if debugging is enabled """
    if settings.get("debug"):
        print('Meeseeks: ' + str(message))

def get_files(paths=None):
    """ Get the files and names for the command """
    view = sublime.active_window().active_view()
    if paths is None:
        file = view.file_name().replace('\\', '/')
        file_name = file.split('/').pop()
    else:
        file = paths[0]
        file_name = file.split('\\').pop()

    debug ('File/Folder path' + file)
    debug ('File/Folder name' + file_name)
    return file, file_name

def pop_info(success='Success', fail='Fail', status=False):
    """ Check for success and notify user """
    if not settings.get('popup_message'):
        return

    if status:
        debug (success)
        # todo, add setting for popup
        sublime.active_window().active_view().show_popup(
                content=success, max_width=2000, max_height=3000)
    else:
        debug (fail)
        sublime.active_window().active_view().show_popup(
                content=fail, max_width=2000, max_height=3000)
