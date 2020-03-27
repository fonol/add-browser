#!/usr/bin/env python
# -*- coding: utf-8 -*-

# anki-webbrowse
# Copyright (C) 2020 Tom Z.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import re

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.editor import Editor
from anki.hooks import wrap, addHook
from aqt.addcards import AddCards

sys.path.insert(0, os.path.dirname(__file__))

from .browser import AddCardsTabbedBrowser

browser_displayed = False
browser = None
menu = None

nightmode = False

def display_browser(web):
    global browser_displayed, browser, menu


    # first init
    if browser is None:
        # layout = editor.web.parent().layout()
        # web = layout.takeAt(0).widget()
        # hbox = QHBoxLayout()

        # browser = AddCardsTabbedBrowser()
        # hbox.addWidget(web, 15)
        # hbox.addWidget(browser, 85)
        # layout.insertLayout(0, hbox, 1)

        config = mw.addonManager.getConfig(__name__)

        addcards = web.parent().parent()
        assert(isinstance(addcards, AddCards))
    

        layout = addcards.layout()
        hbox = QHBoxLayout()
        vbox = QVBoxLayout()
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget() is None or isinstance(item, QBoxLayout):
                vbox.addLayout(item.layout())
            else:
                vbox.addWidget(item.widget())
        temp = QWidget()
        temp.setLayout(layout)

        flds = QWidget()
        flds.setLayout(vbox)
        hbox.setSpacing(0)
        hbox.setContentsMargins(0, 0, 0, 0)
        flds_width = config["fields_area_width_in_percent"]
        flds_width = min(95, max(1, flds_width))
        hbox.addWidget(flds, flds_width)

        menu = QWidget()
        menu_vbox = QVBoxLayout()

        # build bookmarks list
        btree = QTreeWidget()
        btree.itemClicked.connect(bookmark_clicked)
        bookmarks = config["bookmarks"]
        expand = config["expand_bookmark_folders_by_default"]
        for k, blist in bookmarks.items():
            folder = QTreeWidgetItem(btree, [k])
            folder.setExpanded(expand)
            for b in blist:
                b = re.sub("(https?://)?(www2?\\.)?", "", b)
                if b.endswith("/"):
                    b = b[:-1]
                item = QTreeWidgetItem([b])
                folder.addChild(item)
        btree.setHeaderLabels(["Bookmarks"])
        btree.setIconSize(QSize(0,0))
        menu_vbox.addWidget(btree, 2)
        menu.setLayout(menu_vbox)

        menu.setVisible(False)

        browser = AddCardsTabbedBrowser(flds, menu, web, nightmode)
        hbox.addWidget(browser, 90-flds_width)
        
        hbox.addWidget(menu, 10) 

        addcards.setLayout(hbox)

        shortcut = QShortcut(QKeySequence(config["toggle_fields_shortcut"]), browser)
        shortcut.activated.connect(toggle_sidebar)

        addcards.form.deckArea.setMinimumWidth(35)
        addcards.form.modelArea.setMinimumWidth(35)

        addcards.form.deckArea.setMaximumWidth(125)
        addcards.form.modelArea.setMaximumWidth(125)
        addcards.helpButton.setVisible(False)

    else:
        browser.setVisible(True)
    
    web.eval("""
        document.getElementById('toggleBrowserBtn').style.color = `#2496dc`;
        if (document.getElementById('switchBtn')) {
            document.getElementById('switchBtn').setAttribute('style', 'display:none !important');
        }
    """)
        
    browser_displayed = True

def hide_browser(web):
    global browser_displayed, browser, menu
    browser.setVisible(False)
    menu.setVisible(False)
    browser_displayed = False
    addcards = web.parent().parent().parent()
    # bad but works
    addcards.form.deckArea.setMaximumWidth(3000)
    addcards.form.modelArea.setMaximumWidth(3000)
    
    web.eval("""
        document.getElementById('toggleBrowserBtn').style.color = `inherit`;
        if (document.getElementById('switchBtn') ) {
            document.getElementById('switchBtn').setAttribute('style', 'display:inline-block');
        }
    """)


def bookmark_clicked(item):
    if item.parent() is None:
        return
    browser.load(item.text(0))

def on_editor_did_init(editor):
    if editor.addMode:
        def cb(info):
            global browser, nightmode
            rendered = info[0]
            nightmode = info[1]
            print(f"was rendered: {rendered}")
            if not rendered:
                browser = None
                if browser_displayed:
                    display_browser(editor.web)

        editor.web.evalWithCallback("""
                    (() => {
                        let rendered = false;
                        if (!document.getElementById('toggleBrowserBtn')) {
                            document.getElementById('topbutsleft').innerHTML += `<button id='toggleBrowserBtn' onclick='pycmd("toggle_browser")'>&#127760;</button> `; 
                        } else {
                            rendered = true;
                        }
                        let nightmode = document.body.classList.contains("nightMode");
                        return [rendered, nightmode];
                    })();
                """, cb)

def toggle_sidebar():
    if not browser_displayed:
        return
    browser.toggle()

def expanded_on_bridge(self, cmd, _old):
    if cmd == "toggle_browser":
        if browser_displayed:
            hide_browser(self.web)
        else:
            display_browser(self.web)
    else:
        return _old(self, cmd)


def on_keypress(addcards, evt, _old):
    if evt.key() in (Qt.Key_Enter, Qt.Key_Return) and browser.url.hasFocus():
        return
    return _old(addcards, evt)

def init_addon():
    gui_hooks.editor_did_load_note.append(on_editor_did_init)
    Editor.onBridgeCmd = wrap(Editor.onBridgeCmd, expanded_on_bridge, "around")

init_addon()