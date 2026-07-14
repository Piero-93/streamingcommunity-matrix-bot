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
