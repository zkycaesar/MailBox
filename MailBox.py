from imaplib import IMAP4
import email
import base64
import sys
import signal
import os
import traceback
import re
import sqlite3
from Crypto.Cipher import AES
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListView, QStyledItemDelegate,\
    QStyle, QStyleOptionButton, QPushButton, QMainWindow
from PyQt5.QtCore import QSize, Qt, QRectF, QPoint, QRect, QEvent
from PyQt5.QtGui import QIcon, QFont, QStandardItemModel, QStandardItem, QPainter, QPen, QFontMetrics
from PyQt5.QtWebEngineWidgets import QWebEngineView

roles = {"from": Qt.UserRole+1, "subject": Qt.UserRole+2, "date": Qt.UserRole+3, "content": Qt.UserRole+4, "checked": Qt.UserRole+5}

class mailViewDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()
        self.iconSize = QSize(40, 40)
        self.padding = 5

    def sizeHint(self, option, index):
        headerFont = QFont("times", 10)
        headerFont.setBold(True)
        subjectFont = QFont("times", 10)
        headerFm = QFontMetrics(headerFont)
        subjectFm = QFontMetrics(subjectFont)

        headerRect = headerFm.boundingRect(0, 0, option.rect.width() - self.iconSize.width(), 0,
                                           Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, index.data(roles['from']))
        subheaderRect = subjectFm.boundingRect(0, 0, option.rect.width() - self.iconSize.width(), 0,
                                               Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                                               index.data(roles['subject']))
        size = QSize(option.rect.width(), headerRect.height() + subheaderRect.height() + 3 * self.padding)

        if size.height() < self.iconSize.height():
            size.setHeight(self.iconSize.height())
        return size

    def paint(self, painter, option, index):
        self.initStyleOption(option, index)
        painter.save()
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        checkBox = QStyleOptionButton()
        checkBox.rect = self.getCheckBoxRect(option)
        checked = bool(index.model().data(index, roles['checked']))
        if checked:
            checkBox.state |= QStyle.State_On
        else:
            checkBox.state |= QStyle.State_Off
        QApplication.style().drawControl(QStyle.CE_CheckBox, checkBox, painter)

        headerText = index.data(roles['from'])
        subjectText = index.data(roles['subject'])

        headerFont = QFont("times", 10)
        headerFont.setBold(True)
        subjectFont = QFont("times", 10)
        headerFm = QFontMetrics(headerFont)
        subjectFm = QFontMetrics(subjectFont)

        headerRect = headerFm.boundingRect(option.rect.left() + self.iconSize.width(), option.rect.top() + self.padding,
                              option.rect.width() - self.iconSize.width(), 0,
                              Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, headerText)
        subjectRect = subjectFm.boundingRect(headerRect.left(), headerRect.bottom() + self.padding,
                                 option.rect.width() - self.iconSize.width(), 0,
                                 Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, subjectText)

        painter.setPen(Qt.black)

        painter.setFont(headerFont)
        painter.drawText(headerRect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, headerText)

        painter.setFont(subjectFont)
        painter.drawText(subjectRect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, subjectText)

        painter.setPen(Qt.gray)
        painter.drawLine(option.rect.left(), option.rect.bottom(), option.rect.right(), option.rect.bottom())


        painter.restore()

    def editorEvent(self, event, model, option, index):
        # Do not change the checkbox-state
        if event.type() == QEvent.MouseButtonRelease or event.type() == QEvent.MouseButtonDblClick:
            if event.button() != Qt.LeftButton or not self.getCheckBoxRect(option).contains(event.pos()):
                return False
            if event.type() == QEvent.MouseButtonDblClick:
                return True
        # elif event.type() == QEvent.KeyPress:
        #     if event.key() != Qt.Key_Space and event.key() !=Qt.Key_Select:
        #         return False
        else:
            return False
        # Change the checkbox-state
        self.setModelData(None, model, index)
        return True

    def setModelData(self, editor, model, index):
        newValue = not bool(index.model().data(index, roles['checked']))
        model.setData(index, newValue, roles['checked'])

    def getCheckBoxRect(self, option):
        check_box_style_option = QStyleOptionButton()
        check_box_rect = QApplication.style().subElementRect(QStyle.SE_CheckBoxIndicator,
                                                                   check_box_style_option, None)
        check_box_point = QPoint(option.rect.x() + check_box_rect.width() / 2,
                                        option.rect.y() + check_box_rect.height() / 2)
        return QRect(check_box_point, check_box_rect.size())


class UI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mailbox")
        conn = sqlite3.connect('test.db')
        cursor = conn.execute("SELECT COUNT(*) from MAILS")
        self.totalMailCount = cursor.fetchone()[0]
        self.currentPage = 1
        self.mailItemList = []
        self.mailListModel = QStandardItemModel()
        self.fetchFromDB(self.currentPage)
        self.initUI()

    def fetchFromDB(self, page):
        conn = sqlite3.connect('test.db')
        pageOffset = str((page-1)*20+1)
        cursor = conn.execute("SELECT * from MAILS LIMIT 20 OFFSET ?", (pageOffset,))
        self.mailItemList = []
        self.mailListModel.removeRows(0, self.mailListModel.rowCount())
        rowNum = 0
        for row in cursor:
            mailItem = QStandardItem()
            mailItem.setEditable(False)
            mailItem.setData(False, roles['checked'])
            try:
                mailItem.setData(str(DecryptData(row[2]), encoding='utf-8'), roles['from'])
            except:
                mailItem.setData(str(DecryptData(row[2]), encoding='GBK'), roles['from'])
            try:
                mailItem.setData(str(DecryptData(row[1]), encoding='utf-8'), roles['subject'])
            except:
                mailItem.setData(str(DecryptData(row[1]), encoding='GBK'), roles['subject'])
            try:
                mailItem.setData(str(DecryptData(row[6]), encoding='utf-8'), roles['content'])
            except:
                mailItem.setData(str(DecryptData(row[6]), encoding='GBK'), roles['content'])
            try:
                mailItem.setData(str(DecryptData(row[4]), encoding='utf-8'), roles['date'])
            except:
                mailItem.setData(str(DecryptData(row[4]), encoding='GBK'), roles['date'])

            self.mailItemList.append(mailItem)
            self.mailListModel.appendRow(self.mailItemList[rowNum])
            rowNum += 1

    def initUI(self):
        menubar = self.menuBar()
        menubar.addMenu('&File')
        menubar.addMenu('&Edit')
        menubar.addMenu('&View')
        windowLayout = QHBoxLayout()

        self.mailListView = QListView()
        viewDelegate = mailViewDelegate()
        self.mailListView.setModel(self.mailListModel)
        self.mailListView.setItemDelegate(viewDelegate)
        self.mailListView.clicked.connect(self.itemClicked)

        self.lastPageButton = QPushButton()
        self.lastPageButton.setText("上一页")
        self.lastPageButton.clicked.connect(self.lastPageButtonClicked)
        if self.currentPage == 1:
            self.lastPageButton.setEnabled(False)
        self.pageCount = QLabel()
        self.pageCount.setText(str(self.currentPage))
        self.nextPageButton = QPushButton()
        self.nextPageButton.setText("下一页")
        self.nextPageButton.clicked.connect(self.nextPageButtonClicked)
        if self.currentPage * 20 >= self.totalMailCount:
            self.nextPageButton.setEnabled(False)
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.lastPageButton)
        buttonLayout.addWidget(self.pageCount)
        buttonLayout.addWidget(self.nextPageButton)
        buttonBoxView = QWidget()
        buttonBoxView.setLayout(buttonLayout)

        viewLeft = QWidget()
        layoutLeft = QVBoxLayout()
        layoutLeft.addWidget(self.mailListView)
        layoutLeft.addWidget(buttonBoxView)
        viewLeft.setLayout(layoutLeft)
        windowLayout.addWidget(viewLeft)

        self.mailSubject = QLabel()
        self.mailSubject.setText(self.mailItemList[0].data(roles['subject']))
        qFont1 = QFont("Helvetica")
        qFont1.setBold(True)
        qFont1.setPointSize(15)
        self.mailSubject.setFont(qFont1)

        self.mailFrom = QLabel()
        self.mailFrom.setText("发件人："+self.mailItemList[0].data(roles['from']))
        qFont2 = QFont("serif")
        qFont2.setBold(False)
        qFont2.setPointSize(10)
        self.mailFrom.setFont(qFont2)

        self.mailDate = QLabel()
        self.mailDate.setText("时 间：" + self.mailItemList[0].data(roles['date']))
        qFont2 = QFont("serif")
        qFont2.setBold(False)
        qFont2.setPointSize(10)
        self.mailDate.setFont(qFont2)

        self.webView = QWebEngineView()
        self.webView.setHtml(self.mailItemList[0].data(roles['content']))

        layoutRight = QVBoxLayout()
        layoutRight.addWidget(self.mailSubject)
        layoutRight.addWidget(self.mailFrom)
        layoutRight.addWidget(self.mailDate)
        layoutRight.addWidget(self.webView)
        viewRight = QWidget()
        viewRight.setLayout(layoutRight)
        windowLayout.addWidget(viewRight)

        windowView = QWidget()
        windowView.setLayout(windowLayout)
        self.setCentralWidget(windowView)
        # self.setLayout(windowLayout)

    def lastPageButtonClicked(self, checked):
        if self.currentPage > 1:
            self.currentPage -= 1
            self.nextPageButton.setEnabled(True)
            self.pageCount.setText(str(self.currentPage))
            self.fetchFromDB(self.currentPage)
            self.mailListView.repaint()
        if self.currentPage == 1:
            self.lastPageButton.setEnabled(False)

    def nextPageButtonClicked(self, checked):
        if self.currentPage * 20 < self.totalMailCount:
            self.currentPage += 1
            self.lastPageButton.setEnabled(True)
            self.pageCount.setText(str(self.currentPage))
            self.fetchFromDB(self.currentPage)
            self.mailListView.repaint()
        if self.currentPage * 20 >= self.totalMailCount:
            self.nextPageButton.setEnabled(False)

    def itemClicked(self, index):
        if index.model().data(index, roles['subject']) != self.mailSubject.text():
            self.mailSubject.setText(index.model().data(index, roles['subject']))
            self.mailFrom.setText("发件人：" + index.model().data(index, roles['from']))
            self.mailDate.setText("时 间：" + index.model().data(index, roles['date']))
            self.webView.setHtml(index.model().data(index, roles['content']))


def EncryptData(plainText):
    file = open("mima.txt")
    key = file.read()
    obj = AES.new(key, AES.MODE_ECB)
    if isinstance(plainText, str):
        ba = bytearray(plainText, encoding='utf-8')
    else:
        ba = bytearray(plainText)
    length = 32 - len(ba) % 16
    byt = bytearray(length)
    for i in range(length):
        byt[i] = length
    result = ba + byt
    return obj.encrypt(bytes(result))

def DecryptData(crypto):
    file = open("mima.txt")
    key = file.read()
    obj = AES.new(key, AES.MODE_ECB)
    br = bytearray(obj.decrypt(crypto))
    br = br[0: (-br[-1])]
    return bytes(br)

def buildDicForParseHeader():
    dic = {}
    for i in range(256):
        i_key1 = hex(i)
        if len(i_key1) == 3:
            i_key1 = i_key1.replace("0x", "=0")
        else:
            i_key1 = i_key1.replace("0x", "=")
        i_key2 = i_key1.upper()
        # i_key1 = bytearray(i_key1, encoding='utf-8')
        # i_key2 = bytearray(i_key2, encoding='utf-8')
        i_value = bytearray(1)
        i_value[0] = i
        dic[i_key1] = i_value
        dic[i_key2] = i_value
    return dic

def parseMailHeader(header):
    """此函数用于解析email header中的to，from，subject部分.
    """
    dic = {'=CE': bytearray(b'\xce'), '=a5': bytearray(b'\xa5'), '=8B': bytearray(b'\x8b'), '=57': bytearray(b'W'), '=80': bytearray(b'\x80'), '=9d': bytearray(b'\x9d'), '=AE': bytearray(b'\xae'), '=43': bytearray(b'C'), '=09': bytearray(b'\t'), '=bd': bytearray(b'\xbd'), '=D0': bytearray(b'\xd0'), '=E9': bytearray(b'\xe9'), '=0C': bytearray(b'\x0c'), '=55': bytearray(b'U'), '=C8': bytearray(b'\xc8'), '=12': bytearray(b'\x12'), '=1f': bytearray(b'\x1f'), '=23': bytearray(b'#'), '=F9': bytearray(b'\xf9'), '=16': bytearray(b'\x16'), '=1A': bytearray(b'\x1a'), '=2B': bytearray(b'+'), '=3a': bytearray(b':'), '=94': bytearray(b'\x94'), '=0d': bytearray(b'\r'), '=40': bytearray(b'@'), '=74': bytearray(b't'), '=D4': bytearray(b'\xd4'), '=CB': bytearray(b'\xcb'), '=c6': bytearray(b'\xc6'), '=9b': bytearray(b'\x9b'), '=f5': bytearray(b'\xf5'), '=0b': bytearray(b'\x0b'), '=97': bytearray(b'\x97'), '=E5': bytearray(b'\xe5'), '=FD': bytearray(b'\xfd'), '=fa': bytearray(b'\xfa'), '=8A': bytearray(b'\x8a'), '=75': bytearray(b'u'), '=8d': bytearray(b'\x8d'), '=5c': bytearray(b'\\'), '=33': bytearray(b'3'), '=d8': bytearray(b'\xd8'), '=4D': bytearray(b'M'), '=4e': bytearray(b'N'), '=1c': bytearray(b'\x1c'), '=4c': bytearray(b'L'), '=4C': bytearray(b'L'), '=d7': bytearray(b'\xd7'), '=ad': bytearray(b'\xad'), '=ec': bytearray(b'\xec'), '=AD': bytearray(b'\xad'), '=fc': bytearray(b'\xfc'), '=ac': bytearray(b'\xac'), '=24': bytearray(b'$'), '=81': bytearray(b'\x81'), '=a6': bytearray(b'\xa6'), '=4B': bytearray(b'K'), '=5a': bytearray(b'Z'), '=d5': bytearray(b'\xd5'), '=6e': bytearray(b'n'), '=65': bytearray(b'e'), '=A2': bytearray(b'\xa2'), '=F6': bytearray(b'\xf6'), '=F4': bytearray(b'\xf4'), '=1e': bytearray(b'\x1e'), '=90': bytearray(b'\x90'), '=93': bytearray(b'\x93'), '=BB': bytearray(b'\xbb'), '=B5': bytearray(b'\xb5'), '=2e': bytearray(b'.'), '=c3': bytearray(b'\xc3'), '=9D': bytearray(b'\x9d'), '=64': bytearray(b'd'), '=CD': bytearray(b'\xcd'), '=1E': bytearray(b'\x1e'), '=7B': bytearray(b'{'), '=22': bytearray(b'"'), '=04': bytearray(b'\x04'), '=79': bytearray(b'y'), '=7D': bytearray(b'}'), '=2E': bytearray(b'.'), '=8D': bytearray(b'\x8d'), '=ed': bytearray(b'\xed'), '=A6': bytearray(b'\xa6'), '=85': bytearray(b'\x85'), '=e9': bytearray(b'\xe9'), '=2A': bytearray(b'*'), '=47': bytearray(b'G'), '=2b': bytearray(b'+'), '=d9': bytearray(b'\xd9'), '=AF': bytearray(b'\xaf'), '=E3': bytearray(b'\xe3'), '=d6': bytearray(b'\xd6'), '=25': bytearray(b'%'), '=0B': bytearray(b'\x0b'), '=f8': bytearray(b'\xf8'), '=51': bytearray(b'Q'), '=82': bytearray(b'\x82'), '=18': bytearray(b'\x18'), '=F1': bytearray(b'\xf1'), '=C6': bytearray(b'\xc6'), '=91': bytearray(b'\x91'), '=2C': bytearray(b','), '=6F': bytearray(b'o'), '=FF': bytearray(b'\xff'), '=07': bytearray(b'\x07'), '=C9': bytearray(b'\xc9'), '=BE': bytearray(b'\xbe'), '=C3': bytearray(b'\xc3'), '=1d': bytearray(b'\x1d'), '=3c': bytearray(b'<'), '=8E': bytearray(b'\x8e'), '=6f': bytearray(b'o'), '=af': bytearray(b'\xaf'), '=35': bytearray(b'5'), '=B9': bytearray(b'\xb9'), '=4A': bytearray(b'J'), '=6A': bytearray(b'j'), '=60': bytearray(b'`'), '=3d': bytearray(b'='), '=41': bytearray(b'A'), '=c2': bytearray(b'\xc2'), '=3D': bytearray(b'='), '=EA': bytearray(b'\xea'), '=5f': bytearray(b'_'), '=F3': bytearray(b'\xf3'), '=3F': bytearray(b'?'), '=9F': bytearray(b'\x9f'), '=a2': bytearray(b'\xa2'), '=C5': bytearray(b'\xc5'), '=B0': bytearray(b'\xb0'), '=42': bytearray(b'B'), '=84': bytearray(b'\x84'), '=5C': bytearray(b'\\'), '=0E': bytearray(b'\x0e'), '=b7': bytearray(b'\xb7'), '=A5': bytearray(b'\xa5'), '=0f': bytearray(b'\x0f'), '=f7': bytearray(b'\xf7'), '=61': bytearray(b'a'), '=cd': bytearray(b'\xcd'), '=cf': bytearray(b'\xcf'), '=66': bytearray(b'f'), '=2a': bytearray(b'*'), '=ED': bytearray(b'\xed'), '=E7': bytearray(b'\xe7'), '=b8': bytearray(b'\xb8'), '=0D': bytearray(b'\r'), '=b9': bytearray(b'\xb9'), '=bb': bytearray(b'\xbb'), '=a7': bytearray(b'\xa7'), '=53': bytearray(b'S'), '=a9': bytearray(b'\xa9'), '=FA': bytearray(b'\xfa'), '=5d': bytearray(b']'), '=cb': bytearray(b'\xcb'), '=A1': bytearray(b'\xa1'), '=DA': bytearray(b'\xda'), '=54': bytearray(b'T'), '=7C': bytearray(b'|'), '=6c': bytearray(b'l'), '=3b': bytearray(b';'), '=a0': bytearray(b'\xa0'), '=ee': bytearray(b'\xee'), '=d1': bytearray(b'\xd1'), '=B3': bytearray(b'\xb3'), '=2D': bytearray(b'-'), '=30': bytearray(b'0'), '=E6': bytearray(b'\xe6'), '=eb': bytearray(b'\xeb'), '=FE': bytearray(b'\xfe'), '=5F': bytearray(b'_'), '=cc': bytearray(b'\xcc'), '=48': bytearray(b'H'), '=4F': bytearray(b'O'), '=2F': bytearray(b'/'), '=7b': bytearray(b'{'), '=45': bytearray(b'E'), '=e7': bytearray(b'\xe7'), '=e5': bytearray(b'\xe5'), '=e4': bytearray(b'\xe4'), '=c7': bytearray(b'\xc7'), '=9a': bytearray(b'\x9a'), '=7f': bytearray(b'\x7f'), '=1a': bytearray(b'\x1a'), '=72': bytearray(b'r'), '=99': bytearray(b'\x99'), '=58': bytearray(b'X'), '=4E': bytearray(b'N'), '=A7': bytearray(b'\xa7'), '=1D': bytearray(b'\x1d'), '=B2': bytearray(b'\xb2'), '=CF': bytearray(b'\xcf'), '=f1': bytearray(b'\xf1'), '=3f': bytearray(b'?'), '=31': bytearray(b'1'), '=73': bytearray(b's'), '=1b': bytearray(b'\x1b'), '=f9': bytearray(b'\xf9'), '=6d': bytearray(b'm'), '=19': bytearray(b'\x19'), '=c9': bytearray(b'\xc9'), '=C0': bytearray(b'\xc0'), '=B7': bytearray(b'\xb7'), '=2d': bytearray(b'-'), '=d2': bytearray(b'\xd2'), '=aa': bytearray(b'\xaa'), '=3B': bytearray(b';'), '=fe': bytearray(b'\xfe'), '=D1': bytearray(b'\xd1'), '=F7': bytearray(b'\xf7'), '=68': bytearray(b'h'), '=10': bytearray(b'\x10'), '=38': bytearray(b'8'), '=02': bytearray(b'\x02'), '=8b': bytearray(b'\x8b'), '=F2': bytearray(b'\xf2'), '=EF': bytearray(b'\xef'), '=1C': bytearray(b'\x1c'), '=ca': bytearray(b'\xca'), '=d4': bytearray(b'\xd4'), '=56': bytearray(b'V'), '=e1': bytearray(b'\xe1'), '=32': bytearray(b'2'), '=FC': bytearray(b'\xfc'), '=1B': bytearray(b'\x1b'), '=01': bytearray(b'\x01'), '=c0': bytearray(b'\xc0'), '=8f': bytearray(b'\x8f'), '=b6': bytearray(b'\xb6'), '=95': bytearray(b'\x95'), '=15': bytearray(b'\x15'), '=4b': bytearray(b'K'), '=78': bytearray(b'x'), '=b1': bytearray(b'\xb1'), '=f2': bytearray(b'\xf2'), '=c1': bytearray(b'\xc1'), '=A9': bytearray(b'\xa9'), '=39': bytearray(b'9'), '=BD': bytearray(b'\xbd'), '=e0': bytearray(b'\xe0'), '=D2': bytearray(b'\xd2'), '=ce': bytearray(b'\xce'), '=7E': bytearray(b'~'), '=5B': bytearray(b'['), '=ab': bytearray(b'\xab'), '=50': bytearray(b'P'), '=A3': bytearray(b'\xa3'), '=26': bytearray(b'&'), '=BA': bytearray(b'\xba'), '=D8': bytearray(b'\xd8'), '=1F': bytearray(b'\x1f'), '=7c': bytearray(b'|'), '=a1': bytearray(b'\xa1'), '=2c': bytearray(b','), '=86': bytearray(b'\x86'), '=3A': bytearray(b':'), '=E4': bytearray(b'\xe4'), '=9c': bytearray(b'\x9c'), '=A4': bytearray(b'\xa4'), '=F0': bytearray(b'\xf0'), '=6a': bytearray(b'j'), '=f4': bytearray(b'\xf4'), '=3e': bytearray(b'>'), '=E2': bytearray(b'\xe2'), '=AC': bytearray(b'\xac'), '=05': bytearray(b'\x05'), '=c4': bytearray(b'\xc4'), '=AB': bytearray(b'\xab'), '=0c': bytearray(b'\x0c'), '=77': bytearray(b'w'), '=7A': bytearray(b'z'), '=EB': bytearray(b'\xeb'), '=D6': bytearray(b'\xd6'), '=3C': bytearray(b'<'), '=7d': bytearray(b'}'), '=df': bytearray(b'\xdf'), '=D3': bytearray(b'\xd3'), '=D7': bytearray(b'\xd7'), '=5b': bytearray(b'['), '=52': bytearray(b'R'), '=17': bytearray(b'\x17'), '=2f': bytearray(b'/'), '=6B': bytearray(b'k'), '=62': bytearray(b'b'), '=fb': bytearray(b'\xfb'), '=bc': bytearray(b'\xbc'), '=F5': bytearray(b'\xf5'), '=4a': bytearray(b'J'), '=00': bytearray(b'\x00'), '=7a': bytearray(b'z'), '=89': bytearray(b'\x89'), '=6b': bytearray(b'k'), '=a4': bytearray(b'\xa4'), '=f3': bytearray(b'\xf3'), '=6D': bytearray(b'm'), '=BF': bytearray(b'\xbf'), '=dc': bytearray(b'\xdc'), '=71': bytearray(b'q'), '=9f': bytearray(b'\x9f'), '=20': bytearray(b' '), '=08': bytearray(b'\x08'), '=b0': bytearray(b'\xb0'), '=b5': bytearray(b'\xb5'), '=98': bytearray(b'\x98'), '=76': bytearray(b'v'), '=27': bytearray(b"\'"), '=D5': bytearray(b'\xd5'), '=0A': bytearray(b'\n'), '=ff': bytearray(b'\xff'), '=f6': bytearray(b'\xf6'), '=8c': bytearray(b'\x8c'), '=B6': bytearray(b'\xb6'), '=D9': bytearray(b'\xd9'), '=88': bytearray(b'\x88'), '=dd': bytearray(b'\xdd'), '=5D': bytearray(b']'), '=b3': bytearray(b'\xb3'), '=C7': bytearray(b'\xc7'), '=db': bytearray(b'\xdb'), '=9E': bytearray(b'\x9e'), '=92': bytearray(b'\x92'), '=CA': bytearray(b'\xca'), '=11': bytearray(b'\x11'), '=DD': bytearray(b'\xdd'), '=03': bytearray(b'\x03'), '=67': bytearray(b'g'), '=e6': bytearray(b'\xe6'), '=C4': bytearray(b'\xc4'), '=8C': bytearray(b'\x8c'), '=C1': bytearray(b'\xc1'), '=BC': bytearray(b'\xbc'), '=0e': bytearray(b'\x0e'), '=0F': bytearray(b'\x0f'), '=EC': bytearray(b'\xec'), '=6E': bytearray(b'n'), '=DC': bytearray(b'\xdc'), '=e2': bytearray(b'\xe2'), '=28': bytearray(b'('), '=8e': bytearray(b'\x8e'), '=a3': bytearray(b'\xa3'), '=C2': bytearray(b'\xc2'), '=A8': bytearray(b'\xa8'), '=9B': bytearray(b'\x9b'), '=ef': bytearray(b'\xef'), '=d3': bytearray(b'\xd3'), '=06': bytearray(b'\x06'), '=E1': bytearray(b'\xe1'), '=AA': bytearray(b'\xaa'), '=B8': bytearray(b'\xb8'), '=E8': bytearray(b'\xe8'), '=B4': bytearray(b'\xb4'), '=44': bytearray(b'D'), '=34': bytearray(b'4'), '=7F': bytearray(b'\x7f'), '=13': bytearray(b'\x13'), '=5A': bytearray(b'Z'), '=EE': bytearray(b'\xee'), '=49': bytearray(b'I'), '=b2': bytearray(b'\xb2'), '=4f': bytearray(b'O'), '=96': bytearray(b'\x96'), '=F8': bytearray(b'\xf8'), '=c8': bytearray(b'\xc8'), '=da': bytearray(b'\xda'), '=d0': bytearray(b'\xd0'), '=14': bytearray(b'\x14'), '=9C': bytearray(b'\x9c'), '=3E': bytearray(b'>'), '=9e': bytearray(b'\x9e'), '=DB': bytearray(b'\xdb'), '=87': bytearray(b'\x87'), '=7e': bytearray(b'~'), '=70': bytearray(b'p'), '=21': bytearray(b'!'), '=ea': bytearray(b'\xea'), '=6C': bytearray(b'l'), '=37': bytearray(b'7'), '=4d': bytearray(b'M'), '=CC': bytearray(b'\xcc'), '=36': bytearray(b'6'), '=c5': bytearray(b'\xc5'), '=FB': bytearray(b'\xfb'), '=A0': bytearray(b'\xa0'), '=ae': bytearray(b'\xae'), '=59': bytearray(b'Y'), '=a8': bytearray(b'\xa8'), '=ba': bytearray(b'\xba'), '=DF': bytearray(b'\xdf'), '=be': bytearray(b'\xbe'), '=63': bytearray(b'c'), '=fd': bytearray(b'\xfd'), '=9A': bytearray(b'\x9a'), '=de': bytearray(b'\xde'), '=DE': bytearray(b'\xde'), '=B1': bytearray(b'\xb1'), '=29': bytearray(b')'), '=46': bytearray(b'F'), '=5e': bytearray(b'^'), '=5E': bytearray(b'^'), '=e8': bytearray(b'\xe8'), '=83': bytearray(b'\x83'), '=bf': bytearray(b'\xbf'), '=b4': bytearray(b'\xb4'), '=8a': bytearray(b'\x8a'), '=0a': bytearray(b'\n'), '=E0': bytearray(b'\xe0'), '=69': bytearray(b'i'), '=e3': bytearray(b'\xe3'), '=f0': bytearray(b'\xf0'), '=8F': bytearray(b'\x8f')}

    if header == None:
        return " "
    result = bytearray(header, encoding='utf-8')
    match = re.findall(r'(=[?])(GBK|gbk|UTF-8|utf-8|GB2312|gb2312)([?][QqBb][?])(.*?)([?]=)', header)
    encode = ''
    for i in range(len(match)):
        encode = match[i][1]
        form = match[i][2]
        content = match[i][3]
        if form == '?Q?' or form == '?q?':
            ma = re.findall(r'=[0-9a-fA-F][0-9a-fA-F]', content)
            content_ba = bytearray(content, encoding='utf-8')
            for num in ma:
                content_ba = content_ba.replace(bytearray(num, encoding='utf-8'), dic[num])
            result = result.replace(
                bytearray(match[i][0]+match[i][1]+match[i][2]+match[i][3]+match[i][4], encoding='utf-8'),
                content_ba)
        else:
            content = base64.b64decode(content)
            result = result.replace(
                bytearray(match[i][0] + match[i][1] + match[i][2] + match[i][3] + match[i][4], encoding='utf-8'),
                bytearray(content))
    if encode == '':
        encode = 'utf-8'
    try:
        result = str(result.replace(bytearray('\r\n ', encoding=encode), bytearray('', encoding=encode))
                     .replace(bytearray('\r', encoding=encode), bytearray('', encoding=encode))
                     .replace(bytearray('\n', encoding=encode), bytearray('', encoding=encode))
                     .replace(bytearray('\t', encoding=encode), bytearray('', encoding=encode)), encoding=encode)
    except:
        result = str(result.replace(bytearray('\r\n ', encoding="GBK"), bytearray('', encoding="GBK"))
                     .replace(bytearray('\n', encoding="GBK"), bytearray('', encoding="GBK"))
                     .replace(bytearray('\r', encoding="GBK"), bytearray('', encoding="GBK"))
                     .replace(bytearray('\t', encoding="GBK"), bytearray('', encoding="GBK")), encoding="GBK")
        traceback.print_exc()
        print("error str: ")
    print(result)
    return result

def FetchFromMailbox(numMails = 0):
    s = IMAP4('imap.sina.com')
    pwd = input("password: ")
    s.login('zkycaesar', pwd)
    rsp, msg_num = s.select('INBOX', False)
    conn = sqlite3.connect('test.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS MAILS
                   (MAILID       INT     NOT NULL,
                   SUBJECT       TEXT    NOT NULL,
                   MFROM          TEXT    NOT NULL,
                   MTO            TEXT     NOT NULL,
                   MDATE          TEXT     NOT NULL,
                   CONTENTPLAIN   TEXT,
                   CONTENTHTML    TEXT,
                   ATTACHNAMES    TEXT);''')
    conn.execute("DELETE FROM MAILS")
    conn.commit()
    if numMails == 0:
        numMails = int(msg_num[0])
    for i in range(numMails):
        print(i)
        try_num = 0
        mail_id = int(msg_num[0]) - i
        while True:
            try:
                rsp, data = s.fetch(str(mail_id), '(RFC822)')
            except:
                if try_num < 2:
                    continue
                    try_num += 1
                else:
                    break
            break
        emailData = email.message_from_bytes(data[0][1])

        # print(emailData.get('to'))
        mto = EncryptData(parseMailHeader(emailData.get('to')))
        # print(emailData.get('from'))
        mfrom = EncryptData(parseMailHeader(emailData.get('from')))
        # print(emailData.get('subject'))
        msubject = EncryptData(parseMailHeader(emailData.get('subject')))
        mdate = EncryptData(emailData.get('date'))
        mcontent_html = ""
        mcontent_plain = ""
        mattach_names = ""

        if emailData.is_multipart():
            partNum = 0
            for part in emailData.walk():
                partNum += 1
                ctype = part.get_content_type()
                # print(ctype)
                name = part.get_param('name')
                if name:
                    dir_name = "attachment/sina/mail#%d/" % mail_id
                    if not os.path.isdir(dir_name):
                        os.makedirs(dir_name)
                    name = parseMailHeader(name)
                    data = part.get_payload(decode=True)  # 解码出附件数据，然后存储到文件中
                    f = open(dir_name + name, 'wb')  # 注意一定要用wb来打开文件，因为附件一般都是二进制文件
                    mattach_names += "\r\n%s" % name
                    f.write(data)
                    f.close()
                elif ctype == 'text/html':
                    mcontent_html = part.get_payload(decode=True)
                elif ctype == 'text/plain':
                    mcontent_plain = part.get_payload(decode=True)
        else:
            mcontent_html = emailData.get_payload(decode=True)

        mcontent_html = EncryptData(mcontent_html)
        mcontent_plain = EncryptData(mcontent_plain)
        mattach_names = EncryptData(mattach_names)

        conn.execute("INSERT INTO MAILS (MAILID,SUBJECT,MFROM,MTO,MDATE,CONTENTPLAIN,CONTENTHTML,ATTACHNAMES) \
                      VALUES (?,?,?,?,?,?,?,?)", (mail_id, msubject, mfrom, mto, mdate, mcontent_plain, mcontent_html, mattach_names));

    conn.commit()

if __name__ == '__main__':
    # conn = sqlite3.connect('test.db')
    # conn.execute("drop table MAILS")
    # conn.commit()
    # FetchFromMailbox(50)
    app = QApplication(sys.argv)
    window = UI()
    window.show()
    sys.exit(app.exec_())

    # conn = sqlite3.connect('test.db')
    # cursor = conn.execute("SELECT SUBJECT,MFROM,MTO,MDATE,CONTENTPLAIN,CONTENTHTML,ATTACHNAMES  from MAILS")
    # for row in cursor:
    #     for i in range(7):
    #         try:
    #             print(str(DecryptData(row[i]), encoding='utf-8'))
    #         except:
    #             print(str(DecryptData(row[i]), encoding='GBK'))
    #     print("\n")




