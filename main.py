
from PyQt5.QtWidgets import *      
from PyQt5.QtCore import Qt as Qt
from PyQt5.QtCore import QDate as QDate
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from epinephrineMacroUtils.killableThread import th
from ui import Ui_MainWindow as ui
from datetime import datetime, timedelta
import telegram
import pickle as pk
import sys
import os
import schedule as sch
import time


if not os.path.isdir('./data'):
    os.mkdir('./data')
if not os.path.isfile('./data/telegramData.dat'):
    sys.exit(1)

with open('./data/telegramData.dat', 'r') as f:
    tg_token = f.readline().strip()
    chat_id = int(f.readline().strip())


bot = telegram.Bot(token=tg_token)

def sendMessageInMarkdown(msg):
    bot.sendMessage(chat_id=chat_id, text=msg, parse_mode='Markdown', disable_web_page_preview=True)


class MainWindow(QMainWindow, ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.closing = False
        self.macroStatus = False
        self.schTh = None

        
        self.loadParameters()

        self.pushButton.clicked.connect(self.macro)
        self.pushButton_2.clicked.connect(self.macroHandler)

        self.show()

    def closeEvent(self, event):
        print('closing...')
        if not self.schTh==None:
            self.macroStatus = False
            self.schTh.kill()
            self.schTh.join()
        self.saveParameters()
        event.accept()

    def saveParameters(self):
        applicantName = self.lineEdit.text()
        timePeriod1 = self.spinBox.value()
        timePeriod2 = self.spinBox_2.value()
        timePeriod3 = self.spinBox_3.value()
        with open('./data/usr.bin', 'wb') as f:
            pk.dump(applicantName, f)
            pk.dump(timePeriod1, f)
            pk.dump(timePeriod2, f)
            pk.dump(timePeriod3, f)
    def loadParameters(self):
        print(os.path.isfile('./data/usr.bin'))
        if not os.path.isfile('./data/usr.bin'):
            self.saveParameters()
            return
        with open('./data/usr.bin', 'rb') as f:
            applicantName = pk.load(f)
            timePeriod1 = pk.load(f)
            timePeriod2 = pk.load(f)
            timePeriod3 = pk.load(f)
        self.lineEdit.setText(applicantName)
        self.spinBox.setValue(timePeriod1)
        self.spinBox_2.setValue(timePeriod2)
        self.spinBox_3.setValue(timePeriod3)
    def saveCachedData(self, data):
        with open('./data/cache.bin', 'wb') as f:
            pk.dump(data, f)
    def loadCachedData(self):
        if not os.path.isfile('./data/cache.bin'):
            self.saveCachedData({})
            return {}
        with open('./data/cache.bin', 'rb') as f:
            r = pk.load(f)
        return r

    def macro(self):
        applicantName = self.lineEdit.text()
        chrome_options = Options()
        #chrome_options.add_argument('headless')
        chrome_options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(10, 0)
        driver.implicitly_wait(0.1)

        driver.get('https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm')
        driver.find_element(By.XPATH, '//*[@id="Applicant"]').send_keys(applicantName)
        driver.find_element(By.XPATH, '//*[@id="pmn-form"]/form/table[2]/tbody/tr/td/table/tbody/tr[9]/td[2]/input').click()

        while True:
            try:
                driver.find_element(By.XPATH, '//*[@id="pmn-form"]/form/table[2]/tbody/tr/td/table/tbody/tr[9]/td[2]/input').click()
                continue
            except NoSuchElementException:
                break
        print('done!')


        listicData = False
        if driver.current_url == 'https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm':
            listicData = True
        
        if listicData:
            data = self.crawlData(driver)
        else:
            data = []
            applicant = driver.find_element(By.XPATH, '//*[@id="user_provided"]/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[4]/td/table/tbody/tr[1]/td').text
            deviceName = driver.find_element(By.XPATH, '//*[@id="user_provided"]/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[3]/td').text
            number510k = driver.find_element(By.XPATH, '//*[@id="user_provided"]/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[2]/td').text
            #url = f'https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm?ID={number510k}'
            data.append((deviceName, applicant, number510k))

        cache = self.loadCachedData()
        data = list(set(data)-set(cache[applicantName] if applicantName in cache else []))
        cache[applicantName] = list(set(data + (cache[applicantName] if applicantName in cache else [])))
        self.saveCachedData(cache)
        print(cache)
        if len(data)>0:
            message = f"*{applicantName} 검색결과* \n\n"
            for i in data:
                url = f'https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm?ID={i[2]}'
                item = f'[{i[0]}]({url})  {i[1]}'
                message += f'{item}\n'
            print(message)
            sendMessageInMarkdown(message)


        driver.quit()

    def crawlData(self, driver:WebDriver) -> list:
        r = []
        driver.find_element(By.XPATH, '//*[@id="rpp"]/option[6]').click()

        table = driver.find_element(By.XPATH,'//*[@id="user_provided"]/table[2]/tbody/tr/td/table/tbody')
        trs = table.find_elements(By.TAG_NAME, 'tr')
        index = 0
        for tr in trs[4:]:
            tds = tr.find_elements(By.TAG_NAME, 'td')
            print(f'{index}  : '+' | '.join([i.text for i in tds]))
            index += 1
            if len(tds)==4:
                r.append((tds[0].text, tds[1].text, tds[2].text))
        return r

    def macroHandler(self):

        if self.schTh==None or self.macroStatus==False:
            sch.clear()
            sch.every(self.spinBox.value()).seconds.do(self.macro)
            if self.spinBox_2.value()<24:
                sch.every().day.at("%02d:%02d:00"%(self.spinBox_2.value(), self.spinBox_3.value())).do(self.macro2)

            self.macroStatus = True
            self.pushButton_2.setText('중지')
            self.pushButton.setEnabled(False)
            self.schTh = th(target = self.scheduleThread)
            self.schTh.start()
        else:
            self.macroStatus = False
            self.pushButton.setEnabled(True)
            self.pushButton_2.setText('시작')
            self.schTh.kill()
            self.schTh.join()

    
    def scheduleThread(self):
        while (not self.closing) and self.macroStatus:
            sch.run_pending()
            time.sleep(1)
            

    def macro2(self):
        chrome_options = Options()
        #chrome_options.add_argument('headless')
        chrome_options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(10, 0)
        driver.implicitly_wait(0.1)
        dayPointer = datetime.today()
        while True:
            today = dayPointer.strftime("%m/%d/%Y")
            dayPointer = dayPointer - timedelta(1)
            yesterday = dayPointer.strftime("%m/%d/%Y")

            driver.get('https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm')
            driver.find_element(By.XPATH, '//*[@id="DecisionDateFrom"]').send_keys(yesterday)
            driver.find_element(By.XPATH, '//*[@id="DecisionDateTo"]').send_keys(today)
            driver.find_element(By.XPATH, '//*[@id="pmn-form"]/form/table[2]/tbody/tr/td/table/tbody/tr[9]/td[2]/input').click()

            while True:
                try:
                    driver.find_element(By.XPATH, '//*[@id="pmn-form"]/form/table[2]/tbody/tr/td/table/tbody/tr[9]/td[2]/input').click()
                    continue
                except NoSuchElementException:
                    break
            print('done!')

            try:
                listicData = False
                if driver.current_url == 'https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm':
                    listicData = True
                
                if listicData:
                    data = self.crawlData(driver)
                else:
                    data = []
                    applicant = driver.find_element(By.XPATH, '//*[@id="user_provided"]/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[4]/td/table/tbody/tr[1]/td').text
                    deviceName = driver.find_element(By.XPATH, '//*[@id="user_provided"]/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[3]/td').text
                    number510k = driver.find_element(By.XPATH, '//*[@id="user_provided"]/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[2]/td').text
                    #url = f'https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm?ID={number510k}'
                    data.append((deviceName, applicant, number510k))
                break
            except:
                continue

        cache = self.loadCachedData()
        if len(data)>0:
            message = f"*{yesterday}-{today} 검색결과* \n\n"
            for i in data:
                url = f'https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm?ID={i[2]}'
                item = f'[{i[0]}]({url})  {i[1]}'
                message += f'{item}\n'
            print(message)
            sendMessageInMarkdown(message)


        driver.quit()
        




if __name__ == "__main__":
    isDebuging = True
    
    app = QApplication(sys.argv)
    myWindow = MainWindow()
    app.exec_()