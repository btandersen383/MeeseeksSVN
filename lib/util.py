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
