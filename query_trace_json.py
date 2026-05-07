import json
from perfetto.trace_processor import TraceProcessor

trace_path = r"C:\Users\saikr\Downloads\trace-kalama-BP2A.250605.031.A3-2026-05-05-11-59-49.perfetto-trace"
print(f"Loading trace: {trace_path}...")
tp = TraceProcessor(trace=trace_path)
print("Loaded.\n")

queries = {
    "query1_launch": """
SELECT 
    ts, 
    dur / 1e6 AS duration_ms, 
    name 
FROM slice 
WHERE (name LIKE 'launching:%' OR name LIKE 'StartModeLaunch%')
  AND dur > 0
ORDER BY ts ASC;
    """,
    "query2_mem_available": """
SELECT 
    ts, 
    value / 1024.0 / 1024.0 AS available_mem_mb 
FROM counter c
JOIN counter_track ct ON c.track_id = ct.id
WHERE ct.name = 'mem.memavailable'
ORDER BY ts ASC;
    """,
    "query3_psi_mem_some": """
SELECT 
    ts, 
    value AS psi_val 
FROM counter c
JOIN counter_track ct ON c.track_id = ct.id
WHERE ct.name = 'psi.mem.some'
ORDER BY ts ASC;
    """,
    "query4_lmk_kill": """
SELECT ts, name 
FROM slice 
WHERE name LIKE '%criticalLowMemory%' 
   OR name LIKE '%lmk%'
   OR name LIKE '%kill%'
ORDER BY ts ASC;
    """,
    "query5_mem_available_glob": """
SELECT 
    c.ts, 
    c.value / 1024.0 / 1024.0 AS available_mb, 
    t.name AS counter_name
FROM counter AS c
JOIN counter_track AS t ON c.track_id = t.id
WHERE t.name GLOB 'MemAvailable' 
   OR t.name GLOB 'mem.memavailable'
ORDER BY ts ASC;
    """,
    "query6_gallery_rss": """
SELECT 
    c.ts, 
    c.value / 1024.0 AS value_kb, 
    t.name AS counter_name, 
    p.name AS process_name
FROM counter AS c
JOIN process_counter_track AS t ON c.track_id = t.id
JOIN process AS p USING (upid)
WHERE t.name = 'mem.rss'
ORDER BY ts ASC;
    """
}

output = {}

for q_name, q_sql in queries.items():
    print(f"Running {q_name}...")
    try:
        iterator = tp.query(q_sql)
        # Using iterator.as_pandas() is usually easier, but let's just dump row objects to dicts
        # iterator object is a wrapper, we can iterate over it
        results = []
        for row in iterator:
            row_dict = {}
            for col in row.__dict__._asdict(): # wait, Perfetto's row is usually a named tuple or similar.
                pass # let's see how to dump it properly.
    except Exception as e:
        print(f"Error on {q_name}: {e}")
        output[q_name] = {"error": str(e)}

# Better way: pandas dataframe to dict
for q_name, q_sql in queries.items():
    print(f"Running {q_name} using pandas...")
    try:
        df = tp.query(q_sql).as_pandas_dataframe()
        output[q_name] = df.to_dict(orient="records")
    except Exception as e:
        print(f"Error on {q_name}: {e}")
        output[q_name] = {"error": str(e)}

out_file = "trace_queries_output_11_59_49.json"
with open(out_file, "w") as f:
    json.dump(output, f, indent=2)

print(f"\nDone. Output saved to {out_file}")
