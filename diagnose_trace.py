import json
from perfetto.trace_processor import TraceProcessor

trace_path = r"C:\Users\tarun\Desktop\tarunjourney\samsung\trace-kalama-BP2A.250605.031.A3-2026-05-05-11-59-49(2).perfetto-trace"
app = 'com.samsung.android.gallery'

print(f"Loading trace...")
tp = TraceProcessor(trace=trace_path)
print("Loaded.\n")

diag = {}

# --- 1. Check all available tables ---
print("=" * 60)
print("1. ALL TABLES IN TRACE")
print("=" * 60)
tables = tp.query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
table_names = [r.name for r in tables]
diag["tables"] = table_names
for t in table_names:
    print(f"  {t}")

# --- 2. Sample slice names (app launch candidates) ---
print("\n" + "=" * 60)
print("2. SLICE NAMES containing 'launch' or 'gallery'")
print("=" * 60)
try:
    slices = tp.query("""
        SELECT DISTINCT name FROM slice
        WHERE name LIKE '%launch%' OR name LIKE '%gallery%' OR name LIKE '%com.samsung%'
        LIMIT 50
    """)
    launch_slices = [r.name for r in slices]
    diag["launch_slice_names"] = launch_slices
    if launch_slices:
        for s in launch_slices:
            print(f"  {s}")
    else:
        print("  (none found)")
except Exception as e:
    print(f"  ERROR: {e}")
    diag["launch_slice_error"] = str(e)

# --- 3. Sample ALL slice names (first 30) ---
print("\n" + "=" * 60)
print("3. SAMPLE SLICE NAMES (first 30 distinct)")
print("=" * 60)
try:
    slices_all = tp.query("SELECT DISTINCT name FROM slice LIMIT 30")
    sample_slices = [r.name for r in slices_all]
    diag["sample_slice_names"] = sample_slices
    for s in sample_slices:
        print(f"  {s}")
except Exception as e:
    print(f"  ERROR: {e}")

# --- 4. Counter track names (memory candidates) ---
print("\n" + "=" * 60)
print("4. COUNTER TRACK NAMES containing 'mem' or 'gallery' or 'rss'")
print("=" * 60)
try:
    tracks = tp.query("""
        SELECT DISTINCT name FROM counter_track
        WHERE name LIKE '%mem%' OR name LIKE '%rss%' OR name LIKE '%gallery%' OR name LIKE '%samsung%'
        LIMIT 50
    """)
    track_names = [r.name for r in tracks]
    diag["counter_track_names"] = track_names
    if track_names:
        for t in track_names:
            print(f"  {t}")
    else:
        print("  (none found)")
except Exception as e:
    print(f"  ERROR: {e}")
    diag["counter_track_error"] = str(e)

# --- 5. PSI / pressure counter tracks ---
print("\n" + "=" * 60)
print("5. COUNTER TRACK NAMES containing 'psi' or 'pressure'")
print("=" * 60)
try:
    psi = tp.query("""
        SELECT DISTINCT name FROM counter_track
        WHERE name LIKE '%psi%' OR name LIKE '%pressure%' OR name LIKE '%memory%'
        LIMIT 30
    """)
    psi_names = [r.name for r in psi]
    diag["psi_track_names"] = psi_names
    if psi_names:
        for p in psi_names:
            print(f"  {p}")
    else:
        print("  (none found)")
except Exception as e:
    print(f"  ERROR: {e}")

# --- 6. Check ftrace_event or equivalent ---
print("\n" + "=" * 60)
print("6. LMK / lowmemory event candidates")
print("=" * 60)
for tbl in ['ftrace_event', 'raw', 'instants']:
    if tbl in table_names:
        try:
            lmk = tp.query(f"""
                SELECT DISTINCT name FROM {tbl}
                WHERE name LIKE '%lmk%' OR name LIKE '%lowmem%' OR name LIKE '%kill%'
                LIMIT 20
            """)
            lmk_names = [r.name for r in lmk]
            diag[f"lmk_from_{tbl}"] = lmk_names
            print(f"  [{tbl}]: {lmk_names if lmk_names else '(none found)'}")
        except Exception as e:
            print(f"  [{tbl}] ERROR: {e}")
    else:
        print(f"  [{tbl}]: table not present in this trace")

# --- 7. Process table - check if app is even present ---
print("\n" + "=" * 60)
print("7. PROCESS TABLE - app presence check")
print("=" * 60)
try:
    procs = tp.query(f"""
        SELECT pid, name FROM process
        WHERE name LIKE '%gallery%' OR name LIKE '%samsung%'
        LIMIT 20
    """)
    proc_list = [(r.pid, r.name) for r in procs]
    diag["processes"] = [{"pid": p[0], "name": p[1]} for p in proc_list]
    if proc_list:
        for pid, name in proc_list:
            print(f"  PID {pid}: {name}")
    else:
        print("  (app not found in process table)")
except Exception as e:
    print(f"  ERROR: {e}")

# --- Save diagnostics ---
with open("trace_diagnostics.json", "w") as f:
    json.dump(diag, f, indent=2)

print("\n" + "=" * 60)
print("Diagnostics saved to trace_diagnostics.json")
