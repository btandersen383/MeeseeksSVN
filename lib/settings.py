import sublime
import sublime_plugin
import os
import re
import json


SETTINGS_FILE = "Meeseeks.sublime-settings"

class Settings:
    """ Used to access the plugin settings """

    sett = None

    def load_settings():
        Settings.sett = sublime.load_settings(SETTINGS_FILE)

    def get_settings(name):
        Settings.load_settings()
        return Settings.sett.get(name, False)

def get(name):
    """ Gets a value from the plugin settings """
    return Settings.get_settings(name) 
