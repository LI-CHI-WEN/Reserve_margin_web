# keep_alive.py
import requests
import time

URL = "https://reservemarginweb-y39du43bpf2duyqhq2jf4a.streamlit.app/"

while True:
    try:
        res = requests.get(URL)
        print(f"Pinged {URL} - Status {res.status_code}")
    except Exception as e:
        print(f"Failed to ping: {e}")
    time.sleep(600)  # 每10分鐘 ping 一次
    