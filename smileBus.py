import re, time, random
from datetime import date, timedelta
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CITIES = {"Минск": "minsk", "Мозырь": "mozyr", "Речица": "rechica"}

def find_working_proxy():
    print("\n[ПРОКСИ] Запуск поиска рабочего прокси...")
    
    temp_opts = Options()
    temp_opts.add_argument("--headless=new")
    temp_opts.add_argument("--disable-gpu")
    temp_opts.add_argument("--no-sandbox")
    
    try:
        driver_temp = webdriver.Chrome(options=temp_opts)
        driver_temp.get('https://advanced.name/freeproxy/6ae0494ca762a')
        time.sleep(2)
        
        elements = driver_temp.find_element(By.XPATH, "/html/body/pre")
        text = elements.text
        proxy_list = text.strip().split("\n")
        driver_temp.quit()
    except Exception as e:
        print(f"[ПРОКСИ] Не удалось получить список: {e}")
        try: 
            driver_temp.quit()
        except: 
            pass
        return None

    print(f"[ПРОКСИ] Найдено {len(proxy_list)} адресов. Начинаем проверку...")
    
    for proxy in proxy_list[:15]:
        proxy = proxy.strip()
        if not proxy or ":" not in proxy:
            continue
        
        print(f"[ПРОКСИ] Проверка {proxy}...", end=" ")
        try:
            test_opts = Options()
            test_opts.add_argument("--headless=new")
            test_opts.add_argument("--disable-gpu")
            test_opts.add_argument("--no-sandbox")
            test_opts.add_argument(f"--proxy-server=http://{proxy}")
            
            test_driver = webdriver.Chrome(options=test_opts)
            test_driver.set_page_load_timeout(5)
            test_driver.get("https://www.google.com")
            test_driver.quit()
            print("Работает!")
            return proxy
            
        except Exception:
            print("Не работает")
            try:
                test_driver.quit()
            except:
                pass
            continue
            
    print("[ПРОКСИ] Рабочие прокси в списке не найдены.")
    return None


class Log:
    def __init__(self, file="log.txt"): 
        self.file = file
        open(file, "w", encoding="utf-8").close()

    def add(self, msg, t0=None):
        line = f"{msg} - {time.time() - t0:.2f} сек" if t0 else msg
        with open(self.file, "a", encoding="utf-8") as f: 
            f.write(line + "\n")
        print(line, flush=True)


class Parser:
    def __init__(self, routes=None, proxy=None):
        opt = Options()
        opt.add_argument("--start-maximized")
        
        if proxy:
            opt.add_argument(f"--proxy-server=http://{proxy}")
            print(f"\n[INFO] Основной парсер запущен с прокси: {proxy}\n")
        else:
            print("\n[INFO] Основной парсер запущен БЕЗ прокси (не удалось найти рабочий).\n")
        
        self.drive = webdriver.Chrome(options=opt)
        self.w = WebDriverWait(self.drive, 30)
        self.log = Log("log.txt")
        self.routes = routes or [("Минск", "Мозырь"), ("Минск", "Речица")]
        self.data_rows = []

    def close_cook(self):
        for word in ("Принять", "Согласен", "Отклонить"):
            buttons = self.drive.find_elements(By.XPATH, f"//button[contains(., '{word}')]")
            if buttons:
                try: 
                    buttons[0].click()
                    time.sleep(0.3)
                except: 
                    pass
                break

    def open_page(self, c_from, c_to):
        self.drive.get(f"https://smilebus.by/routes/{CITIES[c_from]}/{CITIES[c_to]}")
        self.w.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".date-pick__wrapper input, button")))
        time.sleep(1.5)
        self.close_cook()
        print("Маршрут:", self.drive.current_url, flush=True)

    def pick_date(self, d):
        t0, cell, ok = time.time(), f"{d.year}-{d.month}-{d.day}", False
        inp = self.drive.find_element(By.CSS_SELECTOR, ".date-pick__wrapper input[readonly]")
        for _ in range(3):
            ActionChains(self.drive).move_to_element(inp).click().perform()
            try: 
                self.w.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".vdpOuterWrap, .vdpComponent")))
                ok = True
                break
            except: 
                time.sleep(1)
        
        if not ok: 
            self.log.add("pick_date (календарь не открылся)", t0)
            return False

        done = False
        for _ in range(8):
            cells = self.drive.find_elements(By.CSS_SELECTOR, f'td.vdpCell[data-id="{cell}"]:not(.outOfRange)')
            if not cells: 
                cells = self.drive.find_elements(By.CSS_SELECTOR, f'td[data-id="{cell}"]')
            
            if cells:
                cl = cells[0].get_attribute("class") or ""
                if "disabled" in cl or "outOfRange" in cl: 
                    break
                cells[0].click()
                done = True
                break
            
            arrows = self.drive.find_elements(By.CSS_SELECTOR, ".vdpArrowNext")
            if not arrows: 
                break
            ActionChains(self.drive).move_to_element(arrows[0]).click().perform()
            time.sleep(0.4)

        self.log.add("pick_date", t0)
        return done

    def press_find(self):
        t0 = time.time()
        btn = self.w.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Найти')]")))
        self.w.until(lambda x: btn.is_enabled() and "loading" not in (btn.get_attribute("class") or "") and btn.get_attribute("disabled") is None)
        time.sleep(0.3)
        
        try: 
            ActionChains(self.drive).move_to_element(btn).click().perform()
        except: 
            self.drive.execute_script("arguments[0].click();", btn)

        try: 
            self.w.until(lambda x: "loading" not in (x.find_element(By.XPATH, "//button[contains(., 'Найти')]").get_attribute("class") or ""))
        except: 
            pass
        
        time.sleep(random.uniform(2, 4))
        self.log.add("press_find", t0)

    def find_tickets(self, c_from, c_to, d):
        t0 = time.time()
        self.open_page(c_from, c_to)
        if not self.pick_date(d): 
            self.log.add(f"find_tickets (даты {d} нет)", t0)
            return None
        self.press_find()
        self.log.add("find_tickets", t0)
        return self.drive.find_element(By.TAG_NAME, "body").text

    def get_trips(self, page_text, c_from, c_to, d, direction):
        t0, cnt, used = time.time(), 0, set()
        for part in re.split(r"\n{2,}", page_text):
            tm = re.findall(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", part)
            if len(tm) < 2: 
                continue

            pr = re.findall(r"(?:Цена\s*[:\s]*)?(\d+[.,]\d+|\d+)\s*(?:руб\.?|BYN|р\.)", part, flags=re.I)
            price = None
            if pr:
                try:
                    val = float(pr[0].replace(",", "."))
                    if 1 <= val <= 200: 
                        price = val
                except ValueError: 
                    pass

            dep, arr = f"{int(tm[0][0]):02d}:{tm[0][1]}", f"{int(tm[1][0]):02d}:{tm[1][1]}"
            key = (dep, arr, price)
            if key in used: 
                continue
            used.add(key)

            self.data_rows.append({"route": f"{c_from}-{c_to}", "direction": direction, "date": d, "departure_time": dep, "arrival_time": arr, "price": price})
            cnt += 1

        print(f"{d} {direction} {c_from}-{c_to}: +{cnt}", flush=True)
        self.log.add("get_trips", t0)

    def run(self):
        t0, today, last_day, d = time.time(), date.today(), date.today() + timedelta(days=30), date.today()
        while d <= last_day:
            for a, b in self.routes:
                try:
                    pt = self.find_tickets(a, b, d)
                    if pt: 
                        self.get_trips(pt, a, b, d, "туда")
                except Exception as e: 
                    print(f"Пропуск {a}-{b} туда {d}: {e}", flush=True)
                    self.log.add(f"ошибка {a}-{b} туда {d}: {e}")

                back_day = d + timedelta(days=7)
                if (back_day - today).days <= 30:
                    try:
                        pt = self.find_tickets(b, a, back_day)
                        if pt: 
                            self.get_trips(pt, b, a, back_day, "обратно")
                    except Exception as e: 
                        print(f"Пропуск {b}-{a} обратно {back_day}: {e}", flush=True)
                        self.log.add(f"ошибка {b}-{a} обратно {back_day}: {e}")
            d += timedelta(days=1)

        try: 
            self.drive.quit()
        except: 
            pass
        
        self.log.add("run", t0)
        return pd.DataFrame(self.data_rows)


class DataWork:
    def __init__(self, log): 
        self.log = log

    def clear_data(self, df):
        t0 = time.time()
        if df.empty: 
            return df
        df = df.drop_duplicates()
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df = df.dropna(subset=["departure_time", "date"])
        df = df[(df["price"].isna()) | ((df["price"] > 0) & (df["price"] < 500))]
        df = df.drop_duplicates(subset=["route", "direction", "date", "departure_time"])
        self.log.add("clear_data", t0)
        return df

    def prepare(self, df):
        t0 = time.time()
        if df.empty: 
            return df
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["weekday"], df["month"], df["date"] = df["date"].dt.day_name(), df["date"].dt.month, df["date"].dt.date
        self.log.add("prepare", t0)
        return df

    def save_to_csv(self, df, name):
        t0 = time.time()
        df.to_csv(name, index=False, encoding="utf-8-sig")
        self.log.add(f"save_to_csv {name}", t0)


if __name__ == "__main__":
    all_time = time.time()
    
    working_proxy = find_working_proxy()
    
    bot = Parser(proxy=working_proxy)
    dw = DataWork(bot.log)

    try: 
        data = bot.run()
    except Exception as e: 
        print("Ошибка сбора:", e, flush=True)
        data = pd.DataFrame(bot.data_rows)

    if data.empty: 
        print("Данных нет")
    else:
        dw.save_to_csv(data, "raw_data.csv")
        dw.save_to_csv(dw.prepare(dw.clear_data(data)), "tickets.csv")

    print(f"\nГотово за {time.time() - all_time:.1f} сек, строк: {len(data)}")
    print("Файлы: raw_data.csv, tickets.csv, log.txt")
