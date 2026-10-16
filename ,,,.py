from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image, ImageEnhance
from selenium.webdriver.chrome.options import Options
import time
import os

TEMP_DIR = "captcha_temp"
os.makedirs(TEMP_DIR, exist_ok=True)


class Photo:

    def bright(self):
        img = Image.open(TEMP_DIR + "/secpic4.png").convert("RGB")
        img = ImageEnhance.Brightness(img).enhance(1.2)
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = img.convert("1")
        img.save(TEMP_DIR + "/result.png")


class Captcha:

    def get_text(self):
        proxy = ChangeCountry()
        driver = webdriver.Chrome(options=proxy.get_proxy())
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
        proxy = ChangeCountry()
        self.driver = webdriver.Chrome(options=proxy.get_proxy())

    def start(self):
        self.driver.get("https://whatmyuseragent.com/")

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


class ChangeCountry:
    def get_proxy(self):
        options = Options()
        options.add_argument("--user-agent=Godzilla/5.0 (Windows NT 666.0; Win864; x864) AppleWebKit/537.36 (KHTML, like Gecko) Shrone/120.0.0.0 Safari/537.36")
        options.add_argument("--proxy-server=http://193.181.35.205:8118")
        return options

if __name__ == '__main__':
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()

    options.add_argument(f"--proxy-server='221.221.150.139:8888'")

    driver = webdriver.Chrome(options=options)
    driver.get('https://whatmyuseragent.com/')
    time.sleep(10)
    driver.quit()
