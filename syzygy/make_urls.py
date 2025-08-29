from html.parser import HTMLParser
base = "http://tablebase.sesse.net/syzygy/3-4-5/"
class H(HTMLParser):
    def __init__(self):
        super().__init__()
        self.u = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for k,v in attrs:
                if k.lower() == "href" and v:
                    lv = v.lower()
                    if lv.endswith(".rtbw") or lv.endswith(".rtbz"):
                        if v.startswith("http://") or v.startswith("https://"):
                            self.u.append(v)
                        else:
                            self.u.append(base + v)
p = H()
with open("index.html", "r", errors="ignore") as f:
    p.feed(f.read())
with open("urls.txt","w") as out:
    for x in p.u:
        out.write(x+"\n")
print("found", len(p.u), "urls")
