import sys
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow
import requests
import time
from bs4 import BeautifulSoup

from Ui_MainWindow import *


# 1. 创建信号 Message = QtCore.pyqtSignal(str)
# 2. 主线程连接对应函数
# 3. 从子线程发送信号

class MainWindow(QMainWindow, Ui_MainWindow):
    # 信号量 互斥
    Message = QtCore.pyqtSignal(str)
    SetRange = QtCore.pyqtSignal(int)
    SetProcess = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.getTXT)
        self.pushButton_2.clicked.connect(self.setBrowerPath)
        self.Message.connect(self.textEdit.append)
        self.SetRange.connect(self.setProcessRange)
        self.SetProcess.connect(self.progressBar.setValue)

    # 选择路径
    def setBrowerPath(self):
        download_path = QtWidgets.QFileDialog.getExistingDirectory(self, "位置", "D:")
        self.lineEdit.setText(download_path)

    # 设置进度条的总长度 章节N
    def setProcessRange(self, chapterNum):
        self.progressBar.setRange(1, chapterNum)

    # 显示文本
    def DisplayMessage(self, str):
        self.Message.emit(str)

    # 子线程建立
    def getTXT(self):
        self.t1 = threading.Thread(target=self.kp)  # 新建 爬虫子线程
        self.t1.setDaemon(True)  # Daemon 守护进程
        self.t1.start()

    # 爬虫
    def kp(self):
        self.pushButton.setEnabled(False)
        self.path = self.lineEdit_2.text()
        self.download_path = self.lineEdit.text()
        times = 0
        while times < 3:
            try:
                r = requests.get(self.path)
                self.DisplayMessage("连接 :" + self.path)
                times = 3
            except Exception as e:
                self.DisplayMessage("重试" + str(times) + "次，错误：" + str(e))
                time.sleep(1)
                times = times + 1
                if times == 10:
                    self.DisplayMessage("失败")
                    return
        self.DisplayMessage("连接成功")
        soup = BeautifulSoup(r.content, 'html.parser')
        totalChapter = soup.find_all('tr', {"itemtype": "http://schema.org/Chapter"})
        tds = totalChapter[-1].find_all('td')
        totalChapterNum = int(tds[0].get_text())
        self.SetRange.emit(totalChapterNum)  # emit发送信号
        self.DisplayMessage("全部章节： " + str(totalChapterNum))
        self.path = self.path + '&chapterid='
        with open(self.download_path+'/test.txt', 'w+', encoding='utf-8') as f:
            for i in range(1, totalChapterNum + 1):
                self.SetProcess.emit(i)
                times = 0
                while times < 10:
                    try:
                        r = requests.get(self.path + str(i))
                        self.DisplayMessage("连接 :" + self.path + str(i))
                        times = 10
                    except Exception as e:
                        self.DisplayMessage("重试" + str(times) + "次，错误：" + str(e))
                        time.sleep(1)
                        times = times + 1
                        if times == 3:
                            self.DisplayMessage("失败")
                            return
                soup = BeautifulSoup(r.content, 'lxml')
                header = soup.select('.noveltext > div:nth-child(2) > h2:nth-child(1)')
                text = soup.find('div', class_='noveltext')
                text = text.get_text()  # 清除html标签部分，得到需要的内容
                text = text.split('查看收藏列表')
                text = text[1].split('插入书签')
                text = text[0].strip()
                text = text.replace('　　', '\n    ')
                text = text + '\r\n\r\n\r\n---------章节分割线--------\r\n\r\n\r\n'
                f.write(text)
                self.DisplayMessage("章节" + str(i) + "完成   " + str(header[0]).strip('<h2>').strip('</h2>'))
            self.pushButton.setEnabled(True)
            self.DisplayMessage("已完成")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mywin = MainWindow()
    mywin.show()
    sys.exit(app.exec_())
