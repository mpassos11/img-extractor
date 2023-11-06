import os
import uuid
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager

from PIL import Image

def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_all_images(url):
    option = webdriver.ChromeOptions()
    option.add_argument("start-maximized")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)
    driver.get(url)

    timeout = 5
    try:
        element_present = EC.presence_of_element_located((By.TAG_NAME, 'img'))
        WebDriverWait(driver, timeout).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load")

    soup = bs(driver.page_source, "html.parser")
    driver.quit()

    urls = []
    for img in tqdm(soup.find('body').find_all("img"), "Extracting images"):
        img_url = img['src']
        if not img_url:
            # if img does not contain src attribute, just skip
            continue

        img_url = urljoin(url, img_url)

        try:
            pos = img_url.index("?")
            img_url = img_url[:pos]
        except ValueError:
            pass

        if is_valid(img_url):
            urls.append(img_url)

    return urls


def download(url, pathname):
    # if path doesn't exist, make that path dir
    if not os.path.isdir(pathname):
        os.makedirs(pathname)

    # download the body of response by chunk, not immediately
    response = requests.get(url, stream=True)

    # get the total file size
    file_size = int(response.headers.get("Content-Length", 0))

    # get the file name
    file = str(uuid.uuid4().hex) + '.png'
    filename = os.path.join(pathname, file)

    # progress bar, changing the unit to bytes instead of iteration (default by tqdm)
    progress = tqdm(response.iter_content(1024), f"Downloading {filename}", total=file_size, unit="B", unit_scale=True,
                    unit_divisor=1024)
    with open(filename, "wb") as f:
        for data in progress.iterable:
            # write data read to the file
            f.write(data)

            # update the progress bar manually
            progress.update(len(data))

    # check image broken
    try:
        im = Image.open(filename)
        im.verify()
        im.close()
    except:
        # remove image if broken
        os.remove(filename)


def main(url, path):
    # get all images
    imgs = get_all_images(url)

    for img in imgs:
        # for each image, download it
        download(img, path)


if __name__ == '__main__':
    url = 'https://www.google.com/search?q=flamengo&client=firefox-b-d&sca_esv=579833118&tbm=isch&sxsrf=AM9HkKlB8ehrmtVxjvPf2oooMB5oC3XM1A:1699289797673&source=lnms&sa=X&ved=2ahUKEwifzIrm66-CAxV4spUCHRezBM8Q_AUoAnoECAEQBA&biw=1728&bih=840&dpr=1.11'
    pasta = 'flamengo-google-images'
    main(url, pasta)
