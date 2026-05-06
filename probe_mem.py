import warnings
warnings.filterwarnings('ignore')
from perfetto.trace_processor import TraceProcessor

tp = TraceProcessor(trace=r"C:\Users\tarun\Desktop\tarunjourney\samsung\trace-kalama-BP2A.250605.031.A3-2026-05-05-11-59-49(2).perfetto-trace")

# 1. Search ALL processes for gallery
print("=== PROCESSES with 'gallery'/'Gallery' ===")
r = tp.query("SELECT pid, name FROM process WHERE name LIKE '%gallery%' OR name LIKE '%Gallery%'")
rows = list(r)
if rows:
    for row in rows:
        print(f"  pid={row.pid}  name={row.name}")
else:
    print("  NOT FOUND in process table")

# 2. All processes that have mem.rss counter data (first 30)
print("\n=== ALL PROCESSES with mem.rss counter data ===")
r2 = tp.query("""
    SELECT p.pid, p.name as proc_name
    FROM process_counter_track pct
    JOIN process p ON pct.upid = p.upid
    WHERE pct.name = 'mem.rss'
    GROUP BY p.pid, p.name
    LIMIT 30
""")
for row in r2:
    print(f"  pid={row.pid}  name={row.proc_name}")

# 3. System MemAvailable (usable as proxy)
print("\n=== System MemAvailable sample (first 5 readings) ===")
r3 = tp.query("""
    SELECT c.ts, c.value / 1024.0 / 1024.0 AS mb
    FROM counter c
    JOIN counter_track ct ON c.track_id = ct.id
    WHERE ct.name = 'MemAvailable'
    LIMIT 5
""")
for row in r3:
    print(f"  ts={row.ts}  MemAvailable={row.mb:.1f} MB")

# 4. Check for HWUI / Bitmap memory for gallery threads
print("\n=== Tracks with 'gallery' anywhere ===")
r4 = tp.query("""
    SELECT DISTINCT name FROM track
    WHERE name LIKE '%gallery%' OR name LIKE '%Gallery%'
    LIMIT 20
""")
rows4 = list(r4)
if rows4:
    for row in rows4:
        print(f"  {row.name}")
else:
    print("  (none)")

print("\nDone.")
