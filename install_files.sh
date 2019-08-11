#!/bin/bash

# used to copy files from staging to sublime package dir
# I do this to keep changes from immediately affecting sublime

echo "copying files..."

DEST=~/.config/sublime-text-3/Packages/MeeseeksSVN
cp -r icons/ $DEST
cp -r keymaps/ $DEST
cp -r lib/ $DEST
cp -r menus/ $DEST
cp -r syntax/ $DEST
cp "Meeseeks.sublime-settings" $DEST
cp "MeeseeksSVN.sublime-commands" $DEST
cp "SVNCommands.py" $DEST
