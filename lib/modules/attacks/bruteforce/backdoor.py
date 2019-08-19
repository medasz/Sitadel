from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures.thread
from lib.utils.container import Services
from .. import AttackPlugin


class Backdoor(AttackPlugin):
    output = Services.get("output")
    datastore = Services.get("datastore")
    request = Services.get("request_factory")
    logger = Services.get("logger")

    def check_url(self, url):
        try:
            self.output.debug("Testing: %s" % url)
            resp = self.request.send(url=url, method="HEAD", payload=None, headers=None)
            if resp.status_code == 200:
                self.output.finding("Found backdoor at %s" % resp.url)
        except Exception as e:
            self.logger.error(e)
            self.output.error("Error occured\nAborting this attack...\n")
            self.output.debug("Traceback: %s" % e)
            return

    def process(self, start_url, crawled_urls):
        self.output.info("Checking common backdoors...")
        with self.datastore.open("backdoor.txt", "r") as db:
            dbfiles = [x.strip() for x in db.readlines()]
            urls = map(lambda backdoor: urljoin(str(start_url), str(backdoor)), dbfiles)
            # We launch ThreadPoolExecutor with max_workers to None to get default optimization
            # https://docs.python.org/3/library/concurrent.futures.html
            with ThreadPoolExecutor(max_workers=None) as executor:
                futures = [executor.submit(self.check_url, start_url) for url in urls]
                try:
                    for future in as_completed(futures):
                        future.result()
                except KeyboardInterrupt:
                    executor.shutdown(False)
                    raise
