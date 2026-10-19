import os
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from PIL import Image, ImageEnhance
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

TEMP_DIR = "captcha_temp"
os.makedirs(TEMP_DIR, exist_ok=True)

PROXY_LISTS = [
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
]

SITE_URL = "https://issaold.beltelecom.by/main.html"

PROXY = None



def download_proxies():
    result = []
    for url in PROXY_LISTS:
        try:
            text = requests.get(url, timeout=10).text
            result += text.split()        
        except Exception as e:
            print("Не удалось скачать", url, e)
    return result[:500]                    


def check_proxy(proxy):
    try:
        answer = requests.get(
            SITE_URL,
            proxies={"http": "http://" + proxy, "https": "http://" + proxy},
            timeout=5,
            verify=False,
        )
        if answer.status_code == 200:
            return proxy
    except Exception:
        pass
    return None


def find_proxy():
    proxies = download_proxies()
    print("Скачано прокси:", len(proxies), "- проверяю...")

    with ThreadPoolExecutor(max_workers=50) as pool:
        for result in pool.map(check_proxy, proxies):
            if result:
                print("Рабочий прокси:", result)
                return result

    print("Рабочих прокси нет, работаю без прокси")
    return None



def make_driver():
    options = Options()
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    if PROXY:
        options.add_argument("--proxy-server=http://" + PROXY)
    return webdriver.Chrome(options=options)



class Photo:

    def bright(self):
        img = Image.open(TEMP_DIR + "/secpic4.png").convert("RGB")
        img = ImageEnhance.Brightness(img).enhance(1.2)
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = img.convert("1")
        img.save(TEMP_DIR + "/result.png")


class Captcha:

    def get_text(self):
        driver = make_driver()

        driver.get("https://www.prepostseo.com/ru/image-to-text")
        time.sleep(3)

        path = os.path.abspath(TEMP_DIR + "/result.png")
        driver.find_element(By.XPATH, '//input[@type="file"]').send_keys(path)
        time.sleep(2)

        driver.find_element(By.XPATH, '/html/body/main/section[1]/div[4]/div[3]/div[1]').click()
        time.sleep(10)

        text = driver.find_element(By.XPATH, '//*[@id="result__text0"]').text
        driver.quit()
        return text


class Site:

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.driver = make_driver()

    def start(self):
        self.driver.get(SITE_URL)

        self.driver.find_element(By.XPATH, '//*[@id="capcher"]').screenshot(TEMP_DIR + "/secpic4.png")

        Photo().bright()
        text = Captcha().get_text()
        print("Капча:", text)

        field = self.driver.find_element(By.XPATH, '//*[@id="cap_field"]')
        field.clear()
        field.send_keys(text)

        self.driver.find_element(By.XPATH, '//*[@id="oper_user"]').send_keys(self.login)
        self.driver.find_element(By.XPATH, '//*[@id="wrapper"]/div[2]/div[2]/div[3]/form/div/div[2]/input').send_keys(self.password)
        self.driver.find_element(By.XPATH, '//*[@id="wrapper"]/div[2]/div[2]/div[3]/form/div/div[4]/input').click()

        if os.path.exists(TEMP_DIR + "/result.png"):
            os.remove(TEMP_DIR + "/result.png")

    def close(self):
        time.sleep(100)
        self.driver.quit()



if __name__ == "__main__":
    PROXY = find_proxy()                      
    site = Site("ВАШ_ЛОГИН", "ВАШ_ПАРОЛЬ")   
    site.start()
    site.close()