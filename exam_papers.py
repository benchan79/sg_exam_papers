import os
import time
import logging
import requests
import urllib3
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_RETRIES = 3
RETRY_DELAY = 5


def setup_driver():
    return webdriver.Chrome()


def get_files_info():
    """Scrapes the main page for file links."""
    driver = setup_driver()
    files_information = []
    try:
        driver.get(main_page)
        elements = driver.find_elements(By.CSS_SELECTOR, "ul.lcp_catlist li a")
        with open(f"{file_prefix}_filenames_and_links.txt", "w") as file:
            for idx, element in enumerate(elements):
                filename = element.text
                download_page_link = element.get_attribute("href")
                files_information.append([idx, filename, download_page_link])
                file.write(f"{idx},{filename},{download_page_link}\n")
    finally:
        driver.quit()
    return files_information


def get_google_drive_links(pg_links, drive_links):
    """Extracts Google Drive links from the file download pages."""
    if drive_links:
        next_idx = int(drive_links[-1][0]) + 1
    else:
        next_idx = 0
    try:
        driver = setup_driver()
        for index, fname, link in pg_links[next_idx:]:
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    driver.get(link)
                    break
                except (TimeoutError, urllib3.exceptions.ReadTimeoutError) as e:
                    logging.warning(
                        f"TimeoutError: {e}. Retrying ({retries + 1}/{MAX_RETRIES})..."
                    )
                    driver.quit()
                    retries += 1
                    time.sleep(RETRY_DELAY)
                    driver = setup_driver()
            if retries == MAX_RETRIES:
                logging.error(f"Skipping {fname} due to repeated failures.")
                continue
            try:
                download_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "a.vc_general.vc_btn3")
                    )
                )
                google_drive_link = download_button.get_attribute("href")
                with open(f"{file_prefix}_google_drive_links.txt", "a") as file:
                    file.write(f"{index},{fname},{google_drive_link}\n")
            except Exception as e:
                logging.error(
                    f"Failed to get Google Drive link for {index},{fname}: {e}"
                )

    finally:
        driver.quit()
        with open(f"{file_prefix}_google_drive_links.txt", "r") as file:
            drive_links = [line.strip().split(",") for line in file]

    return drive_links


def download_files(url):
    """Downloads files from Google Drive links."""
    filename = f"{url[0].zfill(3)}_{url[1]}"
    file_url = url[2]
    file_path = os.path.join(file_dir, filename)

    retries = 0
    while retries < MAX_RETRIES + 2:
        try:
            response = requests.get(file_url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(file_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        file.write(chunk)
                # logging.info(f"✅ Download complete: {filename}")
                return
            else:
                logging.error(
                    f"❌ Failed to download {filename}: HTTP {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Download error ({filename}): {e}")

        retries += 1
        logging.warning(f"Retrying ({retries}/{MAX_RETRIES})...")
        time.sleep(RETRY_DELAY)


def suffix_pdf():
    """Adds '.pdf' extension to files if missing."""
    for filename in os.listdir(file_dir):
        file_path = os.path.join(file_dir, filename)
        if os.path.isfile(file_path) and not filename.endswith(".pdf"):
            new_filename = filename + ".pdf"
            os.rename(file_path, os.path.join(file_dir, new_filename))


subjects = ["english", "chinese", "higher-chinese", "maths", "science"]

for level in range(1, 7):
    for subject in subjects:
        if (int(level) < 3) and subject == "science":
            continue
        level = str(level)
        file_prefix = f"primary-{level}-{subject}"
        main_page = f"https://sgexam.com/{file_prefix}/"

        # Change to your own local directory
        file_dir = f"/home/user/projects/exam_papers/{file_prefix}/"

        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        if os.path.exists(f"{file_prefix}_filenames_and_links.txt"):
            logging.info(
                f"Using existing file info: {file_prefix}_filenames_and_links.txt"
            )
            with open(f"{file_prefix}_filenames_and_links.txt", "r") as file:
                files_info = [line.strip().split(",") for line in file]
        else:
            logging.info("Fetching file info...")
            files_info = get_files_info()

        if os.path.exists(f"{file_prefix}_google_drive_links.txt"):
            logging.info(
                f"Using existing Google Drive links: {file_prefix}_google_drive_links.txt"
            )
            with open(f"{file_prefix}_google_drive_links.txt", "r") as file:
                google_drive_links = [line.strip().split(",") for line in file]
        else:
            logging.info("Fetching Google Drive links...")
            google_drive_links = []

        pdf_urls = get_google_drive_links(files_info, google_drive_links)

        num_files = len(
            [
                f
                for f in os.listdir(file_dir)
                if os.path.isfile(os.path.join(file_dir, f))
            ]
        )
        logging.info(f"Total existing files: {num_files}")

        if num_files < len(pdf_urls):
            logging.info("Downloading missing files...")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_url = {
                    executor.submit(download_files, url): url for url in pdf_urls
                }
                for future in concurrent.futures.as_completed(future_to_url):
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"Error in thread execution: {e}")

        suffix_pdf()
        final_num_files = len(
            [
                f
                for f in os.listdir(file_dir)
                if os.path.isfile(os.path.join(file_dir, f))
            ]
        )
        logging.info(
            f"Process completed. {final_num_files}/{len(pdf_urls)} files downloaded."
        )
