# MeeseeksSVN
An command fulfiller for SVN projects in sublime.

## About
This is my first sublime plugin so I went with something that several others have already done. Thanks to those that have paved the way with excellent examples to teach me a few things.

Specific kudos to:
* [VCS Gutter](https://github.com/bradsokol/VcsGutter/blob/master/vcs_gutter.py) for images and relating API calls
* [HypnotoadSVN](https://github.com/m-hall/HypnotoadSVN) for Sublime API examples and code structure

Due to the existance of multiple other packages that do exaclty the same thing as this one, I will *not* be adding this to Package Control. I will make releases only on this repository in the form of `.sublime-package` files.

## Installing
Option 1.
Clone the repo into your 'Packages' directory under Sublime Text 3 app data.

Option 2.
Download the `.sublime-package` file and install manually.

## Using
Just right click or use the shortcut to get a status report of the project or diff a file/folder. The gutter will update on saving a file. For now updating on modification slows down the editor quite noticably.

## TODO
List of todo's that I want to implement:
* svn log, like with status and associated flags as settings
* svn status, add -v and -u settings to show more info
* svn commit
* svn resolve
    * this would be a new window with 3 groups
    * left and right groups are read only
    * center group is resolution
    * could use phantoms/regions to highlight conflicts
    * how to scroll in sync?
* svn blame
* svn check for updates on file loaded
    * pop up message that remote file has changes
