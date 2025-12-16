from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

class HomePageTest(StaticLiveServerTestCase):

    def setUp(self):
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service("/usr/bin/chromedriver")

        self.browser = webdriver.Chrome(
            service=service,
            options=options
        )

    def tearDown(self):
        try:
            self.browser.quit()
        except:
            pass

    def test_home_page_loads(self):
        self.browser.get(self.live_server_url)
        time.sleep(2)
        self.assertIn("CafeITO", self.browser.title)
