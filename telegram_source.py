# Copyright (C) 2026 The streamingcommunity-matrix-bot contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import requests
import re

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def  verify_domain(domain: str) -> bool:
    try:
        status = requests.get(f"https://{domain}", timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if(status.status_code < 400): # 2xx -> OK, 3xx -> Redirects
            logger.info(f"Domain {domain} OK: {status.status_code}")
            return True
        else:
            logger.warning(f"Domain {domain} not working: {status.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"Domain {domain} not reachable: {e}")
        return False

def fetch_latest_domain():
    try:
        html = requests.get("https://t.me/s/Streaming_community_sito", timeout=10)
    except requests.exceptions.RequestException as e:
        logger.warning(f"Cannot reach Telegram channel: {e}")
        return None
    matches = re.findall(r"<b>Nuovo:</b><br/>\s*<code>([^<]+)</code>", html.text)
    if matches:
        url = matches[-1]
        if verify_domain(url):
            logger.info(f"Resolved domain {url}")
            return url
        else:
            logger.warning("Cannot find a valid domain")
            return None
    else:
        logger.warning("Cannot find a valid domain")
        return None

def main():
    fetch_latest_domain()

if __name__ == "__main__":
    main()
