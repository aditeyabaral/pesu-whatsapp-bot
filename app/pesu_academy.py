import os
import time
import logging
import datetime
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument('--ignore-ssl-errors=yes')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-running-insecure-content')


def get_pesu_announcements(username, password):
    if os.path.expanduser("~").startswith("/app"):  # Heroku deployment
        chrome_options.binary_location = "/app/.apt/usr/bin/google-chrome"
        chrome = webdriver.Chrome(
            executable_path="/app/.chromedriver/bin/chromedriver",
            options=chrome_options
        )
    else:
        if "chromedriver" not in os.listdir():
            chrome = webdriver.Chrome(options=chrome_options)
        else:
            chrome = webdriver.Chrome(
                executable_path="./chromedriver", options=chrome_options)
    chrome.execute_cdp_cmd('Emulation.setTimezoneOverride', {
                           'timezoneId': 'Asia/Kolkata'})
    chrome.get("https://pesuacademy.com/Academy")

    try:
        username_box = WebDriverWait(chrome, 20).until(
            EC.presence_of_element_located((By.ID, "j_scriptusername")))
        password_box = WebDriverWait(chrome, 20).until(
            EC.presence_of_element_located((By.NAME, "j_password")))
        login_button = WebDriverWait(chrome, 20).until(EC.presence_of_element_located(
            (By.ID, "postloginform#/Academy/j_spring_security_check")))
    except Exception as e:
        logging.error(e)
        return list()

    username_box.send_keys(username)
    time.sleep(0.3)
    password_box.send_keys(password)
    time.sleep(0.3)
    login_button.click()

    try:
        menu_options = WebDriverWait(chrome, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "menu-name")))
    except Exception as e:
        logging.error(e)
        return list()

    for option in menu_options:
        if option.text == "Announcements":
            chrome.execute_script("arguments[0].click();", option)
            break

    try:
        announcement_boxes = WebDriverWait(chrome, 15).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "elem-info-wrapper")))
    except Exception as e:
        logging.error(e)
        return list()

    data = list()
    for a_box in announcement_boxes:
        header_box = a_box.find_element_by_xpath(r'.//*[@class="text-info"]')
        header = header_box.text

        date_box = a_box.find_element_by_xpath(
            r'.//*[@class="text-muted text-date pull-right"]')
        date = datetime.datetime.strptime(date_box.text, "%d-%B-%Y").date()

        bodies = a_box.find_elements_by_xpath(r'.//*[@class="col-md-12"]')
        all_attachments = list()
        if not bodies:
            bodies = a_box.find_elements_by_xpath(r'.//*[@class="col-md-8"]')
        for b in bodies:
            paragraphs = b.find_elements_by_tag_name("p")
            attachments = b.find_elements_by_xpath(
                r'.//*[@class="pesu-ico-download"]')
            attachment_names = b.find_elements_by_tag_name("a")
            if paragraphs:
                content = '\n'.join([p.text for p in paragraphs])
            if attachments:
                attachment_names = [
                    a_name.text for a_name in attachment_names if a_name.text != "Read more"]
                all_attachments.extend(attachment_names)
                for a in attachments:
                    a.click()
                    time.sleep(1)

        img_base64 = None
        img_box = a_box.find_elements_by_xpath(
            r'.//*[@class="img-responsive"]')
        if img_box:
            img_base64 = img_box[0].get_attribute("src")

        temp = {
            "date": date,
            "header": header,
            "body": content,
            "img": img_base64,
            "attachments": all_attachments
        }

        data.append(temp)

    chrome.quit()
    return data
