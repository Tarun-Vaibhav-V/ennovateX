import json
import pandas as pd
from perfetto.trace_processor import TraceProcessor
trace_path=r"C:\Users\tarun\Desktop\tarunjourney\samsung\trace-kalama-BP2A.250605.031.A3-2026-05-05-11-59-49(2).perfetto-trace"
output_file="ground_truth_v1.json"
app_package_name='com.samsung.android.gallery'
def extract_trace_ground_truth(trace_path, output_file, app_package_name):
    # Initialize Trace Processor
    print(f"Loading trace: {trace_path}...")
    tp = TraceProcessor(trace=trace_path)

    # 1. Metric: App Launch Time (KPI: App Launch & Load Time)
    # Uses android_app_process_started view for reliable launch spans;
    # falls back to slice names seen in diagnostics (launchingActivity, StartModeLaunch)
    launch_query = tp.query(f"""
        SELECT ts, dur / 1e6 AS duration_ms
        FROM slice
        WHERE name LIKE '%launchingActivity%'
           OR name LIKE '%StartModeLaunch%'
           OR name LIKE '%launching%{app_package_name}%'
    """)
    
    # 2. Metric: Memory Utilization (KPI: Memory Utilization Efficiency)
    # Strategy A: Direct app RSS via process join (works if app was running during trace)
    mem_direct = list(tp.query(f"""
        SELECT c.ts, c.value / 1024.0 / 1024.0 AS rss_mb
        FROM counter c
        JOIN process_counter_track pct ON c.track_id = pct.id
        JOIN process p ON pct.upid = p.upid
        WHERE pct.name = 'mem.rss'
          AND p.name LIKE '%{app_package_name}%'
    """))

    if mem_direct:
        # App was active in trace — use its direct RSS readings
        mem_values = [row.rss_mb for row in mem_direct]
        mem_source = f"{app_package_name} direct mem.rss"
        print(f"  [mem] Found {len(mem_values)} direct RSS readings for {app_package_name}")
    else:
        # App was NOT running during capture — use system MemAvailable as proxy.
        # MemAvailable DROP during a launch = RAM consumed by the app.
        # Your KPI target: MemAvailable should drop LESS (by 30%) after optimization.
        print(f"  [mem] '{app_package_name}' not in trace. Falling back to system MemAvailable.")
        mem_sys = list(tp.query("""
            SELECT c.ts, c.value / 1024.0 / 1024.0 AS rss_mb
            FROM counter c
            JOIN counter_track ct ON c.track_id = ct.id
            WHERE ct.name = 'MemAvailable'
        """))
        mem_values = [row.rss_mb for row in mem_sys]
        mem_source = "system MemAvailable (proxy - app not in trace)"

    # 3. Metric: Memory Pressure (KPI: Memory Thrashing Reduction)
    # Diagnostic confirmed the actual name is 'psi.mem.some' (not 'psi.memory.some')
    psi_query = tp.query("""
        SELECT c.ts, c.value AS pressure_val
        FROM counter c
        JOIN counter_track ct ON c.track_id = ct.id
        WHERE ct.name IN ('psi.mem.some', 'psi.mem.full')
    """)

    # 4. Metric: Stability (KPI: System Stability)
    # 'ftrace_event' table not present in this trace; LMK events appear as slices.
    # Also checks android_lmk_kill view if available.
    lmk_query = tp.query("""
        SELECT ts, name
        FROM slice
        WHERE name LIKE '%lmk%'
           OR name LIKE '%lowmemory%'
           OR name LIKE '%low_memory%'
           OR name LIKE '%kill%'
        LIMIT 200
    """)

    # Convert queries to data structures (refined format per KPI review)
    ground_truth = {
        "metadata": {
            "trace_file": trace_path,
            "target_app": app_package_name,
            "duration_limit": "45s",
            "mem_source": mem_source
        },
        "features": {
            "launch_ms": [row.duration_ms for row in launch_query if row.duration_ms > 0],
            "ram_usage_mb": mem_values,
            "pressure_stall": [row.pressure_val for row in psi_query],
            "kill_events": [row.name for row in lmk_query]
        }
    }

    # Save as JSON (Convenient for Model sequences)
    with open(output_file, 'w') as f:
        json.dump(ground_truth, f, indent=4)
    
    print(f"Successfully saved Ground Truth to {output_file}")

# --- EXECUTION ---
# Change 'com.example.app' to your actual app package name
# Ensure your pulled trace file is in the same directory
extract_trace_ground_truth(
    trace_path=trace_path,  # uses the path defined at line 4
    output_file=output_file,
    app_package_name=app_package_name
)