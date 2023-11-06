import os
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
    for img in tqdm(soup.find_all("img"), "Extracting images"):
        img_url = img.attrs.get("src")
        if not img_url:
            # if img does not contain src attribute, just skip
            continue

        img_url = urljoin(url, img_url)

        try:
            pos = img_url.index("?")
            img_url = img_url[:pos]
        except ValueError:
            pass

        path, extension = os.path.splitext(img_url)
        if extension != '':
            if '.png' not in extension or '.jpg' not in extension or '.gif' not in extension:
                continue

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
    filename = os.path.join(pathname, url.split("/")[-1])

    path, extension = os.path.splitext(filename)
    if extension == '':
        filename += '.png'

    # progress bar, changing the unit to bytes instead of iteration (default by tqdm)
    progress = tqdm(response.iter_content(1024), f"Downloading {filename}", total=file_size, unit="B", unit_scale=True,
                    unit_divisor=1024)
    with open(filename, "wb") as f:
        for data in progress.iterable:
            # write data read to the file
            f.write(data)

            # update the progress bar manually
            progress.update(len(data))


def main(url, path):
    # get all images
    imgs = get_all_images(url)

    for img in imgs:
        # for each image, download it
        download(img, path)


if __name__ == '__main__':
    url = 'https://unsplash.com/pt-br'
    pasta = 'unsplash-images'
    main(url, pasta)
