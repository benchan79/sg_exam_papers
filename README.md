# Brief description
An easy implementation of selenium and ThreadPoolExecutor to download files quickly and ad-free.

## Problem
I wanted to download files from a website but it was slow as each file has its own link. 
I would also have to keep closing ads even after turning off the pop-ups.

## Solution 
I used Selenium to automatically scrape the actual download links first before using ThreadPoolExecutor to download multiple files concurrently.

## Libraries and Modules used
Python = 3.12.9  
Selenium = 4.28.1  
Requests = 2.32.3  
Google Chrome = 133.0.6943.126  
ChromeDriver = 133.0.6943.126  

## Additional information that may be helpful

### Install Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb  
sudo apt install ./google-chrome-stable_current_amd64.deb  

### Download Chromedriver
wget https://storage.googleapis.com/chrome-for-testing-public/133.0.6943.126/linux64/chromedriver-linux64.zip   

### Move the Chromedriver to the user's local bin.
sudo mv chromedriver /usr/local/bin/  
sudo chmod +x /usr/local/bin/chromedriver  