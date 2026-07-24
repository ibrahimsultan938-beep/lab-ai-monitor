"""
SQLite Database Layer for AuraLab AI Monitor
Includes normalized tables: PCs, MetricsHistory, Alerts, Recommendations, Users, Logs.
Supports historical telemetry queries for Last Hour, Last 24 Hours & Last 7 Days analytics.
"""
import sqlite3
import json
import random
from datetime import datetime, timedelta

DB_FILE = "database.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pcs (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        zone TEXT NOT NULL,
        location TEXT,
        gpu_name TEXT NOT NULL,
        is_host INTEGER DEFAULT 0,
        vram_total REAL DEFAULT 8.0,
        ram_total REAL DEFAULT 16.0,
        status TEXT DEFAULT 'Healthy',
        temp_threshold INTEGER DEFAULT 85,
        uuid TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Migrations for existing DB tables
    cursor.execute("PRAGMA table_info(pcs)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "temp_threshold" not in columns:
        cursor.execute("ALTER TABLE pcs ADD COLUMN temp_threshold INTEGER DEFAULT 85")
    if "uuid" not in columns:
        cursor.execute("ALTER TABLE pcs ADD COLUMN uuid TEXT")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metrics_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pc_id TEXT NOT NULL,
        gpu_usage REAL,
        gpu_temp INTEGER,
        vram_pct REAL,
        vram_used REAL,
        cpu_usage REAL,
        ram_pct INTEGER,
        ram_used REAL,
        health_score INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pc_id) REFERENCES pcs(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pc_id TEXT NOT NULL,
        severity TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        explanation TEXT,
        acknowledged INTEGER DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pc_id) REFERENCES pcs(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pc_id TEXT NOT NULL,
        recommendation_score INTEGER,
        health_score INTEGER,
        confidence INTEGER,
        reasons_json TEXT,
        explanation TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pc_id) REFERENCES pcs(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        email TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        level TEXT DEFAULT 'INFO',
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM pcs")
    if cursor.fetchone()[0] == 0:
        seed_pcs(conn)
        seed_users(conn)
        seed_historical_metrics(conn)

    conn.close()

def get_pcs_from_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pcs ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def add_pc(pc_id, name, zone, location, gpu_name, is_host=0, vram_total=8.0, ram_total=16.0, status="Healthy", temp_threshold=85, uuid=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO pcs (id, name, zone, location, gpu_name, is_host, vram_total, ram_total, status, temp_threshold, uuid)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pc_id, name, zone, location, gpu_name, is_host, vram_total, ram_total, status, temp_threshold, uuid))
    conn.commit()
    conn.close()

def update_pc(pc_id, name, zone, location, gpu_name, vram_total, ram_total, temp_threshold=85, uuid=None):
    conn = get_connection()
    cursor = conn.cursor()
    if uuid:
        cursor.execute("""
        UPDATE pcs 
        SET name=?, zone=?, location=?, gpu_name=?, vram_total=?, ram_total=?, temp_threshold=?, uuid=?
        WHERE id=?
        """, (name, zone, location, gpu_name, vram_total, ram_total, temp_threshold, uuid, pc_id))
    else:
        cursor.execute("""
        UPDATE pcs 
        SET name=?, zone=?, location=?, gpu_name=?, vram_total=?, ram_total=?, temp_threshold=?
        WHERE id=?
        """, (name, zone, location, gpu_name, vram_total, ram_total, temp_threshold, pc_id))
    conn.commit()
    conn.close()

def update_pc_uuid(pc_id, uuid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pcs SET uuid=? WHERE id=?", (uuid, pc_id))
    conn.commit()
    conn.close()

def delete_pc(pc_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pcs WHERE id=?", (pc_id,))
    cursor.execute("DELETE FROM metrics_history WHERE pc_id=?", (pc_id,))
    conn.commit()
    conn.close()

def get_pc_by_uuid(uuid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pcs WHERE uuid=?", (uuid,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def seed_pcs(conn):
    cluster = [
        ("PC-01", "PC-01 (Host Master)", "Zone A (Training Cluster)", "Row 1 - Rack 01", "NVIDIA GeForce RTX 4050 Laptop GPU", 1, 6.0, 15.64, "Healthy"),
        ("PC-02", "PC-02", "Zone A (Training Cluster)", "Row 1 - Rack 02", "NVIDIA H100 80GB SXM5", 0, 80.0, 256.0, "Healthy"),
        ("PC-03", "PC-03", "Zone A (Training Cluster)", "Row 1 - Rack 03", "NVIDIA H100 80GB SXM5", 0, 80.0, 256.0, "Healthy"),
        ("PC-04", "PC-04", "Zone A (Training Cluster)", "Row 1 - Rack 04", "NVIDIA A100 80GB PCIe", 0, 80.0, 128.0, "Healthy"),
        ("PC-05", "PC-05", "Zone B (Inference Racks)", "Row 2 - Rack 01", "NVIDIA RTX 4090 24GB", 0, 24.0, 64.0, "Healthy"),
        ("PC-06", "PC-06", "Zone B (Inference Racks)", "Row 2 - Rack 02", "NVIDIA RTX 4090 24GB", 0, 24.0, 64.0, "Healthy"),
        ("PC-07", "PC-07", "Zone B (Inference Racks)", "Row 2 - Rack 03", "NVIDIA RTX 3090 24GB", 0, 24.0, 64.0, "Healthy"),
        ("PC-08", "PC-08", "Zone B (Inference Racks)", "Row 2 - Rack 04", "NVIDIA RTX 3090 24GB", 0, 24.0, 64.0, "Healthy"),
        ("PC-09", "PC-09", "Zone C (Student Workstations)", "Desk 01", "NVIDIA RTX 4080 16GB", 0, 16.0, 32.0, "Critical"),
        ("PC-10", "PC-10", "Zone C (Student Workstations)", "Desk 02", "NVIDIA RTX 4080 16GB", 0, 16.0, 32.0, "Healthy"),
        ("PC-11", "PC-11", "Zone C (Student Workstations)", "Desk 03", "NVIDIA RTX 3080 10GB", 0, 10.0, 32.0, "Healthy"),
        ("PC-12", "PC-12", "Zone C (Student Workstations)", "Desk 04", "NVIDIA RTX 3080 10GB", 0, 10.0, 32.0, "Moderate"),
        ("PC-13", "PC-13", "Zone D (Edge AI Nodes)", "Cluster Node 01", "NVIDIA Jetson AGX Orin 64GB", 0, 64.0, 64.0, "Healthy"),
        ("PC-14", "PC-14", "Zone D (Edge AI Nodes)", "Cluster Node 02", "NVIDIA Jetson AGX Orin 64GB", 0, 64.0, 64.0, "Heavy"),
        ("PC-15", "PC-15", "Zone D (Edge AI Nodes)", "Cluster Node 03", "NVIDIA RTX 4070 Ti 12GB", 0, 12.0, 32.0, "Healthy"),
        ("PC-16", "PC-16", "Zone D (Edge AI Nodes)", "Cluster Node 04", "NVIDIA RTX 4070 Ti 12GB", 0, 12.0, 32.0, "Offline"),
    ]
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT INTO pcs (id, name, zone, location, gpu_name, is_host, vram_total, ram_total, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, cluster)
    conn.commit()

def seed_users(conn):
    users = [
        ("admin", "Administrator", "admin@auralab.edu"),
        ("lab_tech", "Lab Technician", "tech@auralab.edu"),
        ("researcher", "AI Researcher", "researcher@auralab.edu")
    ]
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO users (username, role, email) VALUES (?, ?, ?)", users)
    conn.commit()

def seed_historical_metrics(conn):
    cursor = conn.cursor()
    now = datetime.now()

    # Generate 7 days of historical telemetry (samples every 2 hours)
    for i in range(84, 0, -1):
        ts = (now - timedelta(hours=i * 2)).strftime("%Y-%m-%d %H:%M:%S")
        for pc_id in [f"PC-{n:02d}" for n in range(1, 17)]:
            if pc_id == "PC-16":
                continue

            if pc_id == "PC-09":
                gpu_usage = round(random.uniform(88.0, 99.0), 1)
                gpu_temp = random.randint(84, 91)
                vram_pct = round(random.uniform(85.0, 96.0), 1)
                cpu_usage = round(random.uniform(82.0, 95.0), 1)
                ram_pct = random.randint(80, 92)
                health = random.randint(18, 38)
            elif pc_id == "PC-14":
                gpu_usage = round(random.uniform(75.0, 86.0), 1)
                gpu_temp = random.randint(78, 83)
                vram_pct = round(random.uniform(70.0, 84.0), 1)
                cpu_usage = round(random.uniform(65.0, 78.0), 1)
                ram_pct = random.randint(70, 82)
                health = random.randint(42, 58)
            else:
                gpu_usage = round(random.uniform(15.0, 55.0), 1)
                gpu_temp = random.randint(46, 68)
                vram_pct = round(random.uniform(20.0, 60.0), 1)
                cpu_usage = round(random.uniform(20.0, 50.0), 1)
                ram_pct = random.randint(30, 60)
                health = random.randint(75, 98)

            cursor.execute("""
            INSERT INTO metrics_history (pc_id, gpu_usage, gpu_temp, vram_pct, vram_used, cpu_usage, ram_pct, ram_used, health_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pc_id, gpu_usage, gpu_temp, vram_pct, 4.0, cpu_usage, ram_pct, 8.0, health, ts))

    conn.commit()

def record_metric(pc_id, gpu_u, gpu_t, vram_p, vram_u, cpu_u, ram_p, ram_u, health):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO metrics_history (pc_id, gpu_usage, gpu_temp, vram_pct, vram_used, cpu_usage, ram_pct, ram_used, health_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pc_id, gpu_u, gpu_t, vram_p, vram_u, cpu_u, ram_p, ram_u, health))
    conn.commit()
    conn.close()

def get_analytics(timeframe="hour"):
    conn = get_connection()
    cursor = conn.cursor()

    if timeframe == "hour":
        minutes = 60
        interval_format = "%H:%M"
    elif timeframe == "day":
        minutes = 1440
        interval_format = "%m-%d %H:00"
    else: # 7 days
        minutes = 10080
        interval_format = "%m-%d"

    time_limit = (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    SELECT 
        AVG(gpu_usage) as avg_gpu,
        MAX(gpu_usage) as peak_gpu,
        AVG(cpu_usage) as avg_cpu,
        AVG(gpu_temp) as avg_temp,
        AVG(ram_pct) as avg_ram,
        AVG(health_score) as avg_health,
        COUNT(id) as total_samples
    FROM metrics_history
    WHERE timestamp >= ?
    """, (time_limit,))
    summary = cursor.fetchone()

    # Most / Least Active PC
    cursor.execute("""
    SELECT pc_id, AVG(gpu_usage) as avg_u
    FROM metrics_history
    WHERE timestamp >= ?
    GROUP BY pc_id
    ORDER BY avg_u DESC
    LIMIT 1
    """, (time_limit,))
    most_active = cursor.fetchone()

    cursor.execute("""
    SELECT pc_id, AVG(gpu_usage) as avg_u
    FROM metrics_history
    WHERE timestamp >= ? AND gpu_usage > 0
    GROUP BY pc_id
    ORDER BY avg_u ASC
    LIMIT 1
    """, (time_limit,))
    least_active = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM alerts WHERE timestamp >= ?", (time_limit,))
    alert_count = cursor.fetchone()[0]

    cursor.execute(f"""
    SELECT 
        strftime('{interval_format}', timestamp) as time_label,
        ROUND(AVG(gpu_usage), 1) as avg_gpu,
        ROUND(AVG(cpu_usage), 1) as avg_cpu,
        ROUND(AVG(gpu_temp), 1) as avg_temp,
        ROUND(AVG(ram_pct), 1) as avg_ram,
        ROUND(AVG(health_score), 1) as avg_health
    FROM metrics_history
    WHERE timestamp >= ?
    GROUP BY time_label
    ORDER BY timestamp ASC
    """, (time_limit,))
    trend_rows = cursor.fetchall()

    conn.close()

    return {
        "timeframe": timeframe,
        "avg_gpu": round(summary["avg_gpu"] or 0, 1),
        "peak_gpu": round(summary["peak_gpu"] or 0, 1),
        "avg_cpu": round(summary["avg_cpu"] or 0, 1),
        "avg_temp": round(summary["avg_temp"] or 0, 1),
        "avg_ram": round(summary["avg_ram"] or 0, 1),
        "avg_health": round(summary["avg_health"] or 0, 1),
        "total_alerts": alert_count,
        "most_active_pc": most_active["pc_id"] if most_active else "PC-09",
        "least_active_pc": least_active["pc_id"] if least_active else "PC-01",
        "trends": [dict(r) for r in trend_rows]
    }

if __name__ == "__main__":
    init_db()
    print("Database ready.")
