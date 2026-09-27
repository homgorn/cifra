import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
p = "reports/cifra18-audit/pages/wm-clusters.html"
t = open(p, encoding="utf-8").read()
print("subnav блоков:", t.count('class="subnav"'))
print("footer:", t.count("<footer"))
print("nav-link-all:", t.count("nav-link-all"))
print("subnav links:", t.count('class="subnav-link'))

idx = "reports/cifra18-audit/index.html"
t2 = open(idx, encoding="utf-8").read()
print("\nindex: карта отчёта раз:", t2.count('id="toc"'))
print("index: карточек:", t2.count('class="toc-card"'))
print("index: групп:", t2.count('class="toc-group"'))
