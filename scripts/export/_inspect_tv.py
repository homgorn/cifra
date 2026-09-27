import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")
c = sqlite3.connect("topvisor/db/topvisor.db")
tabs = [r[0] for r in c.execute("select name from sqlite_master where type='table'")]
print("tables:", tabs)
for t in tabs:
    try:
        n = c.execute('select count(*) from "%s"' % t).fetchone()[0]
        cols = [d[1] for d in c.execute('PRAGMA table_info("%s")' % t)]
        print("  %-24s %5d  %s" % (t, n, cols[:14]))
    except Exception as e:
        print("  ", t, "ERR", e)

for t in tabs:
    try:
        rows = c.execute('select * from "%s" limit 3' % t).fetchall()
        if rows:
            print("\n== %s sample" % t)
            for r in rows:
                print("  ", str(r)[:220])
    except Exception:
        pass
