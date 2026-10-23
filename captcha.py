import os
import time
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageEnhance
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

TEMP_DIR = "captcha_temp"
os.makedirs(TEMP_DIR, exist_ok=True)

SITE_URL = "https://issaold.beltelecom.by/main.html"
PROXY_SOURCE = "https://advanced.name/freeproxy/6ad1dfbbc360d?type=http?type=https"
PROXY_FILE = "proxy_list.txt"

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

TEST_COUNT = 10      # сколько прокси из списка проверять
CHECK_WORKERS = 3    # сколько Chrome одновременно (каждый - отдельный браузер)

PROXY = None


def make_driver(proxy=None, headless=False):
    options = Options()
    options.add_argument("--user-agent=" + USER_AGENT)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    if headless:
        options.add_argument("--headless=new")
    if proxy:
        options.add_argument("--proxy-server=http://" + proxy)
    return webdriver.Chrome(options=options)


# ---------- прокси (аналог get_proxy.py, но на Chrome) ----------

def get_proxies():
    """Берёт список ip:port со страницы advanced.name."""
    driver = make_driver(headless=True)
    result = []
    try:
        driver.get(PROXY_SOURCE)
        text = driver.find_element(By.XPATH, "/html/body/pre").text
        for line in text.strip().split("\n"):
            line = line.strip().strip("'\",[]() ")
            if line and ":" in line:
                result.append(line)
    except Exception as e:
        print("Не удалось получить список прокси:", e)
    finally:
        driver.quit()
    return result


def check_proxy(proxy):
    """Открывает сайт через прокси в headless Chrome. Рабочий -> proxy, иначе None."""
    driver = None
    try:
        driver = make_driver(proxy, headless=True)
        driver.set_page_load_timeout(20)
        driver.get(SITE_URL)
        driver.find_element(By.XPATH, '//*[@id="capcher"]')  # капча есть -> сайт реально открылся
        print("Works:", proxy)
        return proxy
    except Exception:
        print("Not works:", proxy)
        return None
    finally:
        if driver:
            driver.quit()


def find_proxy():
    proxies = get_proxies()[:TEST_COUNT]
    print("Получено прокси для проверки:", len(proxies))

    with ThreadPoolExecutor(max_workers=CHECK_WORKERS) as pool:
        working = [p for p in pool.map(check_proxy, proxies) if p]

    with open(PROXY_FILE, "w") as f:
        f.write("\n".join(working))

    if working:
        print("Рабочих прокси:", len(working), "- беру", working[0])
        return working[0]
    print("Рабочих прокси нет, работаю без прокси")
    return None


# ---------- капча ----------

class Photo:

    def bright(self):
        img = Image.open(TEMP_DIR + "/secpic4.png").convert("RGB")
        img = ImageEnhance.Brightness(img).enhance(1.2)
        img = ImageEnhance.Contrast(img).enhance(1.5)
        img = img.convert("1")
        img.save(TEMP_DIR + "/result.png")


class Captcha:

    def get_text(self):
        driver = make_driver()  # без прокси

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
        self.driver = make_driver(PROXY)

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
