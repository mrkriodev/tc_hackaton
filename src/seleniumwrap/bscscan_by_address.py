import argparse
import json
import sys

import platform
from weakref import proxy
# from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

def get_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--incognito")
    # chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    return chrome_options

def parse_args():
    parser = argparse.ArgumentParser(description='BSCSCAN')
    parser.add_argument(
        '-a', '--address',
        type=str,
        required=True,
        help='Address for found')

    return parser.parse_args()


def driver_initialize():
    # Proxy Options
    proxy_options = {
        'proxy': {
            'http': 'http://misha:VG8MFfQ3@5.44.47.22:4355',
            'https': 'http://misha:VG8MFfQ3@5.44.47.22:4355',
        }
    }

    if platform.system() == 'Linux':
        s = Service(executable_path="/usr/lib/chromium-browser/chromedriver")
        driver = webdriver.Chrome(service=s, options=get_chrome_options())
    else:
        driver = webdriver.Chrome(options=get_chrome_options(), seleniumwire_options=proxy_options)

    ua = UserAgent()
    userAgent = ua.random
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": userAgent})

    return driver

def scrap_holders_of_bsc_token(token_sc_address) -> dict:
    driver = driver_initialize()
    url = f'https://bscscan.com/token/generic-tokenholders2?m=light&a={token_sc_address}'
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    if soup.find('h3', {'class': 'h5'}):
        print("No information about this address")
        return {}
    while soup.find('div', {'class': 'table-responsive'}) is None:
        soup = BeautifulSoup(driver.page_source, 'lxml')
    trs = soup.find_all('tr')
    trs.remove(trs[0])
    data = {token_sc_address: []}
    for tr in trs:
        data_address = {}
        tds = tr.find_all('td')
        quantity = tds[2].text
        if tds[4].find('a') is None:
            addr = tds[5].find('a')['href'].split('?a=')[1].split('#')[0]  # tds[5]
        else:
            addr = tds[4].find('a')['href'].split('?a=')[1].split('#')[0]  # tds[4]
        # data_address[addr] = quantity
        data[token_sc_address].append({"address": addr, "balance": quantity})
    return data


def main():
    args = parse_args()
    address = args.address

    print(f"Address: {address}")
    data = scrap_holders_of_bsc_token(address)
    data_formatted = json.dumps(data, indent=4)
    print(data_formatted)


if __name__ == "__main__":
    main()