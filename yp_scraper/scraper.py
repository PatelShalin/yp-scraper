import argparse
import csv
import os

from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common import by
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def scrape(city: str):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    out_dir = f'{city}@{timestamp}'
    os.makedirs(out_dir, exist_ok=True)

    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    driver.get(f'https://www.yellowpages.ca/locations/Ontario/{city}/')

    categories = driver.find_elements(by.By.CLASS_NAME, "categories-list")

    url_stack = []
    for category in categories[1:]:
        list_elems = category.find_elements(by.By.CLASS_NAME, "resp-list")
        if list_elems[-1].text == "View All":
            view_all = list_elems[-1]
            view_all_a = view_all.find_element(by.By.XPATH, "a")
            url = view_all_a.get_attribute("href")
            url_stack.append(url)
        else:
            for list_elem in list_elems:
                list_elem_a = list_elem.find_element(by.By.XPATH, "a")
                url = list_elem_a.get_attribute("href")
                url_stack.append(url)

    while url_stack:
        url = url_stack.pop(0)
        try:
            driver.get(url)
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((by.By.CLASS_NAME, "categories-list")))
        except TimeoutException:
            print(f"Timed out while trying to scrape {url}")
            
        categories = driver.find_elements(by.By.CLASS_NAME, "categories-list")

        if not categories:
            listings = driver.find_elements(by.By.CLASS_NAME, "listing")
            if not listings:
                continue
            header = driver.find_element(by.By.CLASS_NAME, "page__container-title").text
            csv_path = os.path.join(out_dir, f'{header}.csv')
            with open(csv_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Name", "Phone Number"])
                page = True
                while page:
                    for listing in listings:
                        listing_name = listing.find_element(by.By.CLASS_NAME, "listing__name").text
                        try:
                            listing_phone_bubble = listing.find_element(by.By.CLASS_NAME, "jsMapBubblePhone")
                            listing_phone_bubble.click()
                            listing_phone_items = listing_phone_bubble.find_elements(by.By.CLASS_NAME, "mlr__submenu__item")
                            phone_numbers = ""
                            for listing_phone_item in listing_phone_items:
                                listing_phone_h4 = listing_phone_item.find_element(by.By.XPATH, "h4")
                                phone_numbers += listing_phone_h4.text + " "
                            writer.writerow([listing_name, phone_numbers])
                        except NoSuchElementException:
                            writer.writerow([listing_name, ""])
                    next_page_div = driver.find_element(by.By.CLASS_NAME, "view_more_section_noScroll")
                    next_page_a = next_page_div.find_elements(by.By.XPATH, "a")
                    if next_page_a and next_page_a[-1].text == "Next >>":
                        next_page_url = next_page_a[-1].get_attribute("href")
                        driver.get(next_page_url)
                        listings = driver.find_elements(by.By.CLASS_NAME, "listing")
                        page = True
                    else:
                        page = False

        for category in categories:
            list_elems = category.find_elements(by.By.CLASS_NAME, "resp-list")
            if list_elems[-1].text == "View All":
                view_all = list_elems[-1]
                view_all_a = view_all.find_element(by.By.XPATH, "a")
                url = view_all_a.get_attribute("href")
                url_stack.append(url)
            else:
                for list_elem in list_elems:
                    list_elem_a = list_elem.find_element(by.By.XPATH, "a")
                    url = list_elem_a.get_attribute("href")
                    url_stack.append(url)

    driver.quit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('city', type=str, help='The city in which you would like to scrape business info.')

    args = parser.parse_args()
    scrape(args.city)