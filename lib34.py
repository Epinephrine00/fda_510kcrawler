from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

chrome_options = Options()
#chrome_options.add_argument('headless')
chrome_options.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=chrome_options)
driver.implicitly_wait(5)

click = lambda x : driver.find_element(by=By.XPATH, value=x).click()
send = lambda x, y : driver.find_element(by=By.XPATH, value=x).send_keys(y)
text = lambda x : driver.find_element(by=By.XPATH, value=x).text
clear = lambda x : driver.find_element(by=By.XPATH, value=x).clear()

