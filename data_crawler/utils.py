import hashlib
import re
def hash_str(s):
    hl = hashlib.md5() # 如果是同一个 md5 对象然后多次 update 则得到的结果不同
    hl.update(s.encode())
    return hl.hexdigest()

def remove_html(string):
    html_tag_pattern = re.compile(r'<[^>]+>')
    alt_tag_pattern = re.compile(r'<alternatives>.*</alternatives>')
    str_no_alt = re.sub(alt_tag_pattern, '', string)
    return (re.sub(html_tag_pattern, '', str_no_alt).replace('\n', '').replace('  ', '')).strip()
