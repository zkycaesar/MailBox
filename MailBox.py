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
    obj = AES.new('1234567812345678', AES.MODE_ECB)
    ba = bytearray(plainText, encoding='utf-8')
    length = 32 - len(ba) % 16
    byt = bytearray(length)
    for i in range(length):
        byt[i] = length
    result = ba + byt
    return obj.encrypt(bytes(result))

def DecryptData(crypto):
    obj = AES.new('1234567812345678', AES.MODE_ECB)
    br = bytearray(obj.decrypt(crypto))
    br = br[0: (-br[-1])]
    return str(br, encoding='utf-8')

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

    result = header
    match1 = re.finditer(r'=[?](UTF-8|utf-8|GB2312|gb2312)[?][QqBb][?].*?[?]=', header)
    for item in match1:
        originStr = item.group()
        match2 = re.findall(r'(=[?])(UTF-8|utf-8|GB2312|gb2312)([?][QqBb][?])(.*?)([?]=)', originStr)
        for i in range(len(match2)):
            encode = match2[i][1]
            form = match2[i][2]
            content = match2[i][3]
            if form == '?Q?' or form == '?q?':
                ma = re.findall(r'=[0-9a-fA-F][0-9a-fA-F]', content)
                content_ba = bytearray(content, encoding='utf-8')
                for num in ma:
                    content_ba = content_ba.replace(bytearray(num, encoding='utf-8'), dic[num])
                result = result.replace(originStr, str(content_ba, encoding=encode))
            else:
                content = base64.b64decode(content)
                result = result.replace(originStr, str(content, encoding=encode))
    result = result.replace('\n', '').replace('\r', '').replace(' ', '')
    return result

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
        print(content)
        print(len(content))
        rsp, data = s.fetch(str(int(msg_num[0]) - i), '(BODY[HEADER])')
        # print(data[0][1])
        headers = email.message_from_bytes(data[0][1])
        # print('To: %s' % headers['to'])
        # print('From: %s' % headers['from'])
        # print('Subject: %s' % headers['subject'])
        # print(parseMailHeader(headers['to']))
        # print(parseMailHeader(headers['from']))
        # print(parseMailHeader(headers['subject']))

        mto = EncryptData(parseMailHeader(headers['to']))
        mfrom = EncryptData(parseMailHeader(headers['from']))
        msubject = EncryptData(parseMailHeader(headers['subject']))
        mcontent = EncryptData(content)

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
    s = IMAP4('imap.sina.com')
    pwd = input("password: ")
    s.login('zkycaesar', pwd)
    rsp, msg_num = s.select('INBOX', False)
    for i in range(10):
        print(i)
        rsp, data = s.fetch(str(int(msg_num[0]) - i), '(RFC822)')
        # print(data)
        content = email.message_from_bytes(data[0][1])
        # print(content.get('from'))
        # print(content.get('to'))
        # print(content.get('subject'))
        if content.is_multipart():
            for part in content.walk():
                ctype = part.get_content_type()
                print(ctype)
                print(part.get_param('name'))
                if ctype == "application/octet-stream":
                    data = part.get_payload(decode=True)  # 解码出附件数据，然后存储到文件中
                    try:
                        f = open("bbb%d" % i, 'wb')  # 注意一定要用wb来打开文件，因为附件一般都是二进制文件
                    except:
                        print('附件名有非法字符，自动换一个')
                        f = open('bb', 'wb')
                    f.write(data)
                    f.close()

                    # 不是附件，是文本内容
                    # print(par.get_payload(decode=True))# 解码出文本内容，直接输出来就可以了。


        # rsp, data = s.fetch(str(int(msg_num[0]) - i), '(BODY[HEADER])')
        # print(data[0][1])
        # headers = email.message_from_bytes(data[0][1])
        # print(email.utils.parseaddr(headers.get("from")))
        # print(email.utils.parseaddr(headers.get("to")))

    # FetchFromMailbox()
    # app = QApplication(sys.argv)
    # sys.exit(app.exec_())

    # conn = sqlite3.connect('test.db')
    # cursor = conn.execute("SELECT subject, mfrom, mto, content  from MAILS")
    # obj = AES.new('1234567812345678', AES.MODE_ECB)
    # for row in cursor:
    #     # print(DecryptData(row[0]))
    #     # print(DecryptData(row[1]))
    #     # print(DecryptData(row[2]))
    #     print(DecryptData(row[3]))
    #     # print(base64.b64decode(DecryptData(row[3])))
    #     print("\n")




