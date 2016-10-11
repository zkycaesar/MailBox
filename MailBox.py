from imaplib import IMAP4
import email
import base64
import sys
import re
import sqlite3
from Crypto.Cipher import AES
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QListView
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView

class UI(QWidget):
    def __init__(self, mails):
        super().__init__()
        self.initUI(mails)

    def initUI(self, mails):
        grid = QHBoxLayout()
        self.setLayout(grid)

        mailList = QListView()
        model = QStandardItemModel(list)
        mailList.addItems()

        # view = QWebEngineView()
        # view.setHtml(str(content, encoding="utf-8"));

def EncryptData(plainText):
    length = 32 - len(plainText) % 16
    byt = bytearray(length)
    for i in range(length):
        byt[i] = length
    result = plainText + str(bytes(byt), encoding='utf-8')
    return bytes(result, encoding='utf-8')

def FetchFromMailbox():
    s = IMAP4('imap.sina.com')
    pwd = input("password: ")
    s.login('zkycaesar', pwd)
    rsp, msg_num = s.select('INBOX', False)
    conn = sqlite3.connect('test.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS MAILS
                   (SUBJECT       TEXT    NOT NULL,
                   MFROM          TEXT    NOT NULL,
                   MTO            TEXT     NOT NULL,
                   CONTENT        TEXT);''')
    conn.execute("DELETE FROM MAILS")
    conn.commit()
    for i in range(10):
        print(i)
        rsp, data = s.fetch(str(int(msg_num[0]) - i), '(BODY[TEXT])')
        content = str(data[0][1])
        # print(content)
        rsp, data = s.fetch(str(int(msg_num[0]) - i), '(BODY[HEADER])')
        # print(data[0][1])
        headers = email.message_from_bytes(data[0][1])
        # print('To: %s' % headers['to'])
        # print('From: %s' % headers['from'])
        # print('Subject: %s' % headers['subject'])

        obj = AES.new('1234567812345678', AES.MODE_ECB)
        mto = obj.encrypt(EncryptData(headers['to']))
        mfrom = obj.encrypt(EncryptData(headers['from']))
        msubject = obj.encrypt(EncryptData(headers['subject']))
        mcontent = obj.encrypt(EncryptData(content))

        conn.execute("INSERT INTO MAILS (SUBJECT,MFROM,MTO,CONTENT) \
                      VALUES (?,?,?,?)", (msubject, mfrom, mto, mcontent));

        # cursor = conn.execute("SELECT subject, mfrom, mto, content  from MAILS")
        # for row in cursor:
        #     print(obj.decrypt(row[0]))
        #     print(obj.decrypt(row[1]))
        #     print(obj.decrypt(row[2]))
        #     print(obj.decrypt(row[3]))
    conn.commit()

if __name__ == '__main__':
    # FetchFromMailbox()
    # app = QApplication(sys.argv)
    # sys.exit(app.exec_())

    conn = sqlite3.connect('test.db')
    cursor = conn.execute("SELECT subject, mfrom, mto, content  from MAILS")
    obj = AES.new('1234567812345678', AES.MODE_ECB)
    for row in cursor:
        print(obj.decrypt(row[0]))
        br = bytearray(obj.decrypt(row[0]))
        br = br[0 : (-br[-1])]
        st = str(bytes(br))
        print(st)

        pattern = re.compile(r'=[?](UTF-8|utf-8|GB2312|gb2312)[?][QqBb][?].+?[?]=')
        match = pattern.finditer(st)
        for m in match:
            print(m.group())
        # print(obj.decrypt(row[1]))
        # print(obj.decrypt(row[2]))
        # print(obj.decrypt(row[3]))
        print("\n")



