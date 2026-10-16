from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image, ImageEnhance
import time
import os

# папка для картинок
TEMP_DIR = "captcha_temp"
os.makedirs(TEMP_DIR, exist_ok=True)


class Photo:
    """Делает капчу почётче"""

    def bright(self):
        img = Image.open(TEMP_DIR + "/secpic4.png").convert("RGB")
        img = ImageEnhance.Brightness(img).enhance(1.2)
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = img.convert("1")
        img.save(TEMP_DIR + "/result.png")


class Captcha:
    """Читает текст с картинки через сайт"""

    def get_text(self):
        driver = webdriver.Chrome()
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
    """Заходит на сайт"""

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.driver = webdriver.Chrome()

    def start(self):
        self.driver.get("https://issaold.beltelecom.by/main.html")

        # скриншот капчи
        self.driver.find_element(By.XPATH, '//*[@id="capcher"]').screenshot(TEMP_DIR + "/secpic4.png")

        # обработка и распознавание
        Photo().bright()
        text = Captcha().get_text()
        print("Капча:", text)

        # вводим данные
        field = self.driver.find_element(By.XPATH, '//*[@id="cap_field"]')
        field.clear()
        field.send_keys(text)

        self.driver.find_element(By.XPATH, '//*[@id="oper_user"]').send_keys(self.login)
        self.driver.find_element(By.XPATH, '//*[@id="wrapper"]/div[2]/div[2]/div[3]/form/div/div[2]/input').send_keys(self.password)
        self.driver.find_element(By.XPATH, '//*[@id="wrapper"]/div[2]/div[2]/div[3]/form/div/div[4]/input').click()

        # удаляем лишний файл
        if os.path.exists(TEMP_DIR + "/result.png"):
            os.remove(TEMP_DIR + "/result.png")

    def close(self):
        input("Нажми Enter, чтобы закрыть...")
        self.driver.quit()


site = Site("unkown5325", "parol12345")
site.start()
site.close()
