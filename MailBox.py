from imaplib import IMAP4
import email
import base64
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QListWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView

class UI(QWidget):
    def __init__(self, mails):
        super().__init__()
        self.initUI()

    def initUI(self):
        grid = QHBoxLayout()
        self.setLayout(grid)

        mailList = QListWidget()
        mailList.addItems()


if __name__ == '__main__':
    s = IMAP4('imap.sina.com')
    s.login('zkycaesar', 'em_sina_271828')
    rsp, msg_num = s.select('INBOX', False)
    # rsp, data = s.fetch(str(int(msg_num[0]) - 1), '(BODY[TEXT])')
    # content = base64.b64decode(data[0][1])
    # print(content)
    rsp, data = s.fetch(str(int(msg_num[0])-5), '(BODY[HEADER])')
    print(data[0][1])
    headers = email.message_from_bytes(data[0][1])
    print('To: %s' % headers['to'])
    print('From: %s' % headers['from'])
    print('Subject: %s' % headers['subject'])

    # app = QApplication(sys.argv)
    # view = QWebEngineView()
    # view.setHtml(str(content, encoding="utf-8"));
    # view.show();
    # sys.exit(app.exec_())


