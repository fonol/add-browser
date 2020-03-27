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

import sip
import time
from aqt.qt import *
from aqt import mw

class AddCardsTabbedBrowser(QWidget):
    def __init__(self, flds, menu, flds_web, nightmode, parent=None):

        QWidget.__init__(self, parent)
        config = mw.addonManager.getConfig(__name__)
        self.auto_focus_field = config["auto_focus_first_field_after_toggle_fields"]

        self.flds = flds
        self.flds_web = flds_web
        self.menu = menu
        self.nightmode = nightmode

        self.layout = QVBoxLayout()
        self.toplayout = QHBoxLayout()

        toggle_btn = QPushButton("|-|")
        toggle_btn.setMaximumWidth(25)
        toggle_btn.clicked.connect(self.toggle)
        toggle_btn.setToolTip(config["toggle_fields_shortcut"])

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        back_btn = QPushButton(" < ")
        back_btn.setMaximumWidth(25)
        back_btn.clicked.connect(self.back)
        forward_btn = QPushButton(" > ")
        forward_btn.setMaximumWidth(25)
        forward_btn.clicked.connect(self.forward)
        reload_btn = QPushButton(u"\u21BB")        
        reload_btn.setMaximumWidth(25)
        reload_btn.clicked.connect(self.page_refresh)
        self.toplayout.addWidget(toggle_btn, 0)
        self.toplayout.addWidget(line, 0)
        self.toplayout.addWidget(back_btn, 0)
        self.toplayout.addWidget(forward_btn, 0)
        self.toplayout.addWidget(reload_btn, 0)

        self.url = UrlInput(self.load_url)
        self.url.returnPressed.connect(self.load_url)
        self.toplayout.addWidget(self.url, 2)

        zoom_out = QPushButton(" - ")
        zoom_out.setMaximumWidth(20)
        zoom_out.clicked.connect(self.zoom_out)
        zoom_out.setShortcut("Ctrl+-")
        zoom_in = QPushButton(" + ")
        zoom_in.setMaximumWidth(20)
        zoom_in.clicked.connect(self.zoom_in)
        zoom_in.setShortcut("Ctrl++")
        self.toplayout.addWidget(zoom_out)
        self.toplayout.addWidget(zoom_in)

        menu = QPushButton("...")
        menu.clicked.connect(self.toggle_menu)
        self.toplayout.addWidget(menu)

        self.tabs = AddCardsBrowserTabs(self)

        self.layout.addLayout(self.toplayout)
        self.layout.addWidget(self.tabs)
        # self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,4,4,4)
        self.setLayout(self.layout)
        self.show()

    def load_url(self):
        url = self.url.text()
        if url is not None and len(url) > 0:
            url = QUrl(url)
            url.setScheme("http")
            self.tabs.load(url)

    def update_url(self, url):
        self.url.setText(url)

    def page_refresh(self):
        self.tabs.page_refresh()

    def back(self):
        self.tabs.back()

    def forward(self):
        self.tabs.forward()

    def toggle(self):
        """
            Toggle fields visibility.
        """
        if self.flds.isHidden():
            self.flds.setVisible(True)
            if self.auto_focus_field:
                self.flds_web.setFocus(True)
                self.flds_web.eval("$('.field').first().focus();")
        else:
            self.flds.setVisible(False)

    def toggle_menu(self):
        """
            Toggle bookmarks visibility.
        """
        if self.menu.isHidden():
            self.menu.setVisible(True)
        else:
            self.menu.setVisible(False)

    def zoom_in(self):
        self.tabs.zoom_in()

    def zoom_out(self):
        self.tabs.zoom_out()

    def load(self, url):
        if url is not None and len(url) > 0:
            url = QUrl(url)
            url.setScheme("http")
            self.tabs.load(url)

class AddCardsBrowserTabs(QTabWidget):
    def __init__(self, parent = None):
        self.parent = parent
        QTabWidget.__init__(self, parent)

        self.setTabsClosable(True)
        config = mw.addonManager.getConfig(__name__)
    
        self.start = QUrl(config["new_tab_default_page"])
        self.views = []

        self._add_tab()
        self.addTab(QWidget(), "+")
        self.tabBar().tabButton(1, QTabBar.RightSide).resize(0,0)

        self.currentChanged.connect(self._tab_clicked)
        self.tabCloseRequested.connect(self._tab_close)


    def _add_tab(self):
        v = self._new_view()
        self.insertTab(max(0, self.count() -1), v, "...")

    def _new_view(self):
        view = AddCardsWebView()
        view.titleChanged.connect(self._view_title_changed)
        view.urlChanged.connect(self._view_url_changed)
        view.setWindowTitle(str(int(time.time() * 1000)))
        self.views.append(view)
        view.load(self.start)

        return view
    
    def _tab_clicked(self, ix):
        if ix == self.count() - 1:
            self._add_tab()
            self.setCurrentIndex(ix)
        else:
            self.parent.update_url(self.views[self.currentIndex()].url().toDisplayString())

    def _tab_close(self, ix):
        if self.count() == 2:
            return
        self.blockSignals(True)

        self.removeTab(ix)
        sip.delete(self.views[ix])
        del self.views[ix]
        self.blockSignals(False)
        if self.count() == 2:
            self.setCurrentIndex(0)
        elif self.currentIndex() == self.count()- 1:
            self.setCurrentIndex(self.count() -2)

    def _view_title_changed(self, title):
        self.setTabText(self.currentIndex(), title)

    def _view_url_changed(self, url):
        self.parent.update_url(url.toDisplayString())

    def load(self, qurl):
        self.active_view().load(qurl)

    def page_refresh(self):
        self.load(self.active_view().url())

    def back(self):
        self.active_view().back()

    def forward(self):
        self.active_view().forward()

    def zoom_out(self):
        z = self.active_view().zoomFactor()
        if z > 0.1:
            z = z - 0.1
        self.active_view().setZoomFactor(z)

    def zoom_in(self):
        z = self.active_view().zoomFactor()
        z = z + 0.1
        self.active_view().setZoomFactor(z)

    def active_view(self):
        return self.views[self.currentIndex()]

class AddCardsWebView(QWebEngineView):
    def __init__(self, *args, **kwargs):
        QWebEngineView.__init__(self, *args, **kwargs)
        self.settings().setAttribute(QWebEngineSettings.PluginsEnabled,True)
        self.tab = self.parent()

class UrlInput(QLineEdit):
    def __init__(self, cb, parent=None):
        QLineEdit.__init__(self, parent)
        self.cb = cb
        self.suggestions = [] 
        self.completer = QCompleter(self.suggestions, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self.completer)
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.cb()
            self._refresh_completer()
            e.accept()
        else:
            QLineEdit.keyPressEvent(self, e)

    def _refresh_completer(self):
        t = QUrl(self.text()).toDisplayString()
        if len(t) > 0 and not t in self.suggestions:
            self.suggestions.append(t)
            self.completer = QCompleter(self.suggestions, self)
            self.completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.setCompleter(self.completer)