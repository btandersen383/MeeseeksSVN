import sublime
import sublime_plugin
import os
import re
import json


SETTINGS_FILE = "Meeseeks.sublime-settings"

class Settings:
    """ Used to access the plugin settings """

    plugin_settings = None

    def load_settings():
        Settings.plugin_settings = sublime.load_settings(SETTINGS_FILE)

    def get_settings(name):
        if not Settings.plugin_settings:
            Settings.load_settings()
        return Settings.plugin_settings.get(name)

def get(name):
    """ Gets a value from the plugin settings """
    return Settings.get_settings(name) 
