import requests
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
r = requests.get('https://www.cse.lk', headers=headers, timeout=10)
scripts = re.findall(r'src=["\']([^"\']+\.js)["\']', r.text)

for s in scripts:
    url = s if s.startswith('http') else f"https://www.cse.lk/{s.lstrip('/')}"
    try:
        txt = requests.get(url, headers=headers, timeout=10).text
        if 'companyInfoSummery' in txt:
            print("Found companyInfoSummery in", s)
            for m in re.findall(r'.{0,100}companyInfoSummery.{0,100}', txt):
                print("   Snippet:", m)
    except Exception as e:
        pass
