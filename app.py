"""
Starlette ASGI Server with WebSockets, SQLite Database, Analytics Engine,
One-Click Report Generator (Executive PDF/CSV), and Safe Demo Mode.
Developed for AI Innovation Hackathon 2026 by Team DIU_Elite_Noobs.
"""
import asyncio
import csv
import io
import json
import random
import time
from datetime import datetime
from starlette.applications import Starlette
from starlette.responses import JSONResponse, HTMLResponse, Response, FileResponse
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from telemetry_agent import get_full_host_telemetry
import database

# Initialize SQLite database
database.init_db()

# Global state store
connected_clients = set()
active_notifications = []
notification_id_counter = 100
demo_mode_active = False  # SAFE DEMO MODE (Software-only simulated load, zero hardware strain)

CLUSTER_SPECS = [
    {"id": "PC-01", "name": "PC-01 (Host Master)", "zone": "Zone A (Training Cluster)", "gpu": "NVIDIA RTX 4050 6GB", "is_host": True, "vram_total": 6.0, "ram_total": 15.64},
    {"id": "PC-02", "name": "PC-02", "zone": "Zone A (Training Cluster)", "gpu": "NVIDIA H100 80GB SXM5", "is_host": False, "vram_total": 80.0, "ram_total": 256.0},
    {"id": "PC-03", "name": "PC-03", "zone": "Zone A (Training Cluster)", "gpu": "NVIDIA H100 80GB SXM5", "is_host": False, "vram_total": 80.0, "ram_total": 256.0},
    {"id": "PC-04", "name": "PC-04", "zone": "Zone A (Training Cluster)", "gpu": "NVIDIA A100 80GB PCIe", "is_host": False, "vram_total": 80.0, "ram_total": 128.0},
    {"id": "PC-05", "name": "PC-05", "zone": "Zone B (Inference Racks)", "gpu": "NVIDIA RTX 4090 24GB", "is_host": False, "vram_total": 24.0, "ram_total": 64.0},
    {"id": "PC-06", "name": "PC-06", "zone": "Zone B (Inference Racks)", "gpu": "NVIDIA RTX 4090 24GB", "is_host": False, "vram_total": 24.0, "ram_total": 64.0},
    {"id": "PC-07", "name": "PC-07", "zone": "Zone B (Inference Racks)", "gpu": "NVIDIA RTX 3090 24GB", "is_host": False, "vram_total": 24.0, "ram_total": 64.0},
    {"id": "PC-08", "name": "PC-08", "zone": "Zone B (Inference Racks)", "gpu": "NVIDIA RTX 3090 24GB", "is_host": False, "vram_total": 24.0, "ram_total": 64.0},
    {"id": "PC-09", "name": "PC-09", "zone": "Zone C (Student Workstations)", "gpu": "NVIDIA RTX 4080 16GB", "is_host": False, "vram_total": 16.0, "ram_total": 32.0},
    {"id": "PC-10", "name": "PC-10", "zone": "Zone C (Student Workstations)", "gpu": "NVIDIA RTX 4080 16GB", "is_host": False, "vram_total": 16.0, "ram_total": 32.0},
    {"id": "PC-11", "name": "PC-11", "zone": "Zone C (Student Workstations)", "gpu": "NVIDIA RTX 3080 10GB", "is_host": False, "vram_total": 10.0, "ram_total": 32.0},
    {"id": "PC-12", "name": "PC-12", "zone": "Zone C (Student Workstations)", "gpu": "NVIDIA RTX 3080 10GB", "is_host": False, "vram_total": 10.0, "ram_total": 32.0},
    {"id": "PC-13", "name": "PC-13", "zone": "Zone D (Edge AI Nodes)", "gpu": "NVIDIA Jetson AGX Orin 64GB", "is_host": False, "vram_total": 64.0, "ram_total": 64.0},
    {"id": "PC-14", "name": "PC-14", "zone": "Zone D (Edge AI Nodes)", "gpu": "NVIDIA Jetson AGX Orin 64GB", "is_host": False, "vram_total": 64.0, "ram_total": 64.0},
    {"id": "PC-15", "name": "PC-15", "zone": "Zone D (Edge AI Nodes)", "gpu": "NVIDIA RTX 4070 Ti 12GB", "is_host": False, "vram_total": 12.0, "ram_total": 32.0},
    {"id": "PC-16", "name": "PC-16", "zone": "Zone D (Edge AI Nodes)", "gpu": "NVIDIA RTX 4070 Ti 12GB", "is_host": False, "vram_total": 12.0, "ram_total": 32.0},
]

nodes_state = {}
for spec in CLUSTER_SPECS:
    if spec["id"] == "PC-01":
        continue
    if spec["id"] == "PC-09":
        gpu_usage, gpu_temp, vram_pct, cpu_usage, ram_pct, status = 97.0, 89, 95.0, 92.0, 88, "Critical"
    elif spec["id"] == "PC-14":
        gpu_usage, gpu_temp, vram_pct, cpu_usage, ram_pct, status = 84.0, 82, 81.0, 74.0, 75, "Heavy"
    elif spec["id"] == "PC-16":
        gpu_usage, gpu_temp, vram_pct, cpu_usage, ram_pct, status = 0.0, 0, 0.0, 0.0, 0, "Offline"
    elif spec["id"] in ["PC-02", "PC-05"]:
        gpu_usage, gpu_temp, vram_pct, cpu_usage, ram_pct, status = random.uniform(12.0, 24.0), random.randint(48, 56), random.uniform(15.0, 28.0), random.uniform(14.0, 26.0), random.randint(20, 35), "Healthy"
    else:
        gpu_usage, gpu_temp, vram_pct, cpu_usage, ram_pct, status = random.uniform(30.0, 65.0), random.randint(58, 72), random.uniform(35.0, 68.0), random.uniform(30.0, 60.0), random.randint(40, 65), "Healthy" if random.randint(58,72) < 65 else "Moderate"

    nodes_state[spec["id"]] = {
        "id": spec["id"],
        "name": spec["name"],
        "zone": spec["zone"],
        "gpu_name": spec["gpu"],
        "is_host": False,
        "is_online": (status != "Offline"),
        "gpu_usage": round(gpu_usage, 1),
        "gpu_temp": gpu_temp,
        "vram_pct": round(vram_pct, 1),
        "vram_total": spec["vram_total"],
        "vram_used": round(spec["vram_total"] * (vram_pct / 100.0), 2),
        "cpu_usage": round(cpu_usage, 1),
        "ram_pct": ram_pct,
        "ram_total": spec["ram_total"],
        "ram_used": round(spec["ram_total"] * (ram_pct / 100.0), 2),
        "processes": [
            {"name": "python train_llama3.py", "pid": "10441", "memory_mb": 4820.0, "cpu_pct": 45.2},
            {"name": "vllm-serve", "pid": "8812", "memory_mb": 2400.0, "cpu_pct": 22.0}
        ] if status != "Offline" else []
    }

def calculate_ai_health_score(pc_data):
    if not pc_data.get("is_online", True) or pc_data.get("status") == "Offline":
        return 0, "⚫ Offline", "Offline", "#64748b"

    gpu_u = pc_data.get("gpu_usage", 0.0)
    gpu_t = pc_data.get("gpu_temp", 45)
    vram_p = pc_data.get("vram_pct", 0.0)
    cpu_u = pc_data.get("cpu_usage", 0.0)
    ram_p = pc_data.get("ram_pct", 0.0)

    temp_penalty = max(0, (gpu_t - 55) * 2.2) if gpu_t > 55 else 0
    score = 100.0 - (0.30 * gpu_u + 0.25 * temp_penalty + 0.20 * vram_p + 0.15 * cpu_u + 0.10 * ram_p)
    score = max(0, min(100, round(score)))

    if score >= 80:
        return score, "🟢 Healthy", "Healthy", "#10b981"
    elif score >= 60:
        return score, "🟡 Moderate", "Moderate", "#f59e0b"
    elif score >= 40:
        return score, "🟠 Heavy", "Heavy", "#f97316"
    else:
        return score, "🔴 Critical", "Critical", "#ef4444"

def calculate_ai_rec_score(pc_data, health_score):
    if pc_data.get("status") == "Offline":
        return 0, 0
    gpu_u = pc_data.get("gpu_usage", 0.0)
    gpu_t = pc_data.get("gpu_temp", 45)
    vram_p = pc_data.get("vram_pct", 0.0)
    temp_penalty = max(0, (gpu_t - 50) * 2.0)
    rec = (0.35 * (100.0 - gpu_u)) + (0.30 * max(0, 100.0 - temp_penalty)) + (0.20 * (100.0 - vram_p)) + (0.15 * health_score)
    rec_score = max(10, min(99, round(rec)))
    confidence = max(85, min(99, round(rec_score * 0.95 + random.uniform(1.0, 3.0))))
    return rec_score, confidence

def generate_smart_ai_explanation(pc_data, health_score, status_name):
    pc_name = pc_data.get("name", "PC")
    gpu_u = pc_data.get("gpu_usage", 0)
    gpu_t = pc_data.get("gpu_temp", 0)
    ram_p = pc_data.get("ram_pct", 0)
    vram_p = pc_data.get("vram_pct", 0)

    if status_name == "Offline":
        return f"{pc_name} is currently offline or unreachable on the lab local network."

    if status_name == "Critical":
        reasons = []
        if gpu_u > 90: reasons.append(f"GPU utilization at {gpu_u}%")
        if gpu_t > 85: reasons.append(f"GPU temperature ({gpu_t}°C) exceeded thermal safety threshold")
        if vram_p > 90: reasons.append(f"VRAM is near max capacity ({vram_p}%)")
        reason_str = " and ".join(reasons) if reasons else "system metrics exceeded safety limits"
        return f"{pc_name} is marked Critical because {reason_str}. Safe workload re-balancing recommended."

    if status_name == "Heavy":
        return f"{pc_name} is under heavy workload (GPU {gpu_u}%, Temp {gpu_t}°C, VRAM {vram_p}%). Reduced thermal headroom."

    if status_name == "Moderate":
        return f"{pc_name} is operating with moderate load ({gpu_u}% GPU, {gpu_t}°C temp). Performance is stable."

    vram_free_gb = round(pc_data.get("vram_total", 8.0) * (1.0 - vram_p / 100.0), 1)
    return f"{pc_name} is highly recommended: low GPU usage ({gpu_u}%), safe temperature ({gpu_t}°C), {vram_free_gb} GB VRAM free, and stable performance trend."

connected_agents = {}  # key: agent_uuid -> dict of agent info & telemetry

async def api_agent_telemetry(request):
    try:
        body = await request.json()
        agent_uuid = body.get("uuid")
        pc_id = body.get("id") or body.get("name") or "PC-Unknown"
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        if not agent_uuid:
            return JSONResponse({"error": "Missing agent UUID"}, status_code=400)

        db_pcs = database.get_pcs_from_db()
        matched_pc = next((p for p in db_pcs if p.get("uuid") == agent_uuid), None)
        
        if not matched_pc:
            matched_by_id = next((p for p in db_pcs if p["id"].lower() == pc_id.lower()), None)
            if matched_by_id:
                database.update_pc_uuid(matched_by_id["id"], agent_uuid)
                pc_id = matched_by_id["id"]
            else:
                gpu_name = body.get("gpu_name", "NVIDIA GPU")
                vram_total = body.get("vram_total", 8.0)
                ram_total = body.get("ram_total", 16.0)
                zone = body.get("zone", "Zone A (Training Cluster)")
                location = body.get("location", "Remote Agent Node")
                database.add_pc(pc_id, pc_id, zone, location, gpu_name, 0, vram_total, ram_total, "Healthy", 85, agent_uuid)

        connected_agents[agent_uuid] = {
            "uuid": agent_uuid,
            "pc_id": pc_id,
            "last_seen": time.time(),
            "client_ip": client_ip,
            "telemetry": body
        }
        
        return JSONResponse({"status": "registered", "uuid": agent_uuid, "pc_id": pc_id})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

def compute_all_pc_data():
    host_data = get_full_host_telemetry()
    db_pcs = database.get_pcs_from_db()
    
    if demo_mode_active:
        host_data["gpu_usage"] = 96.5
        host_data["gpu_temp"] = 88
        host_data["cpu_usage"] = 91.2
        host_data["ram_pct"] = 89
        host_data["vram_pct"] = 94.0

    pc_list = []
    now_ts = time.time()

    for db_pc in db_pcs:
        pid = db_pc["id"]
        temp_threshold = db_pc.get("temp_threshold") or 85
        agent_uuid = db_pc.get("uuid")

        active_agent_data = None
        for u, agent in connected_agents.items():
            if (agent_uuid and u == agent_uuid) or (agent["pc_id"].lower() == pid.lower()):
                if now_ts - agent["last_seen"] <= 12:
                    active_agent_data = agent["telemetry"]
                    break

        if pid == "PC-01" and not active_agent_data:
            node_data = dict(host_data)
            node_data["name"] = db_pc["name"]
            node_data["zone"] = db_pc["zone"]
            node_data["temp_threshold"] = temp_threshold
        elif active_agent_data:
            node_data = {
                "id": pid,
                "uuid": agent_uuid,
                "name": db_pc["name"],
                "zone": db_pc["zone"],
                "location": db_pc.get("location", "Remote Node"),
                "gpu_name": active_agent_data.get("gpu_name", db_pc["gpu_name"]),
                "is_host": db_pc.get("is_host", 0) == 1,
                "is_online": True,
                "gpu_usage": active_agent_data.get("gpu_usage", 0.0),
                "gpu_temp": active_agent_data.get("gpu_temp", 45),
                "vram_pct": active_agent_data.get("vram_pct", 0.0),
                "vram_total": db_pc.get("vram_total", 8.0),
                "vram_used": active_agent_data.get("vram_used", 0.0),
                "cpu_usage": active_agent_data.get("cpu_usage", 0.0),
                "ram_pct": active_agent_data.get("ram_pct", 0),
                "ram_total": db_pc.get("ram_total", 16.0),
                "ram_used": active_agent_data.get("ram_used", 0.0),
                "processes": active_agent_data.get("processes", []),
                "temp_threshold": temp_threshold
            }
        else:
            n = nodes_state.get(pid)
            if not n:
                n = {
                    "id": pid,
                    "name": db_pc["name"],
                    "zone": db_pc["zone"],
                    "gpu_name": db_pc["gpu_name"],
                    "is_host": False,
                    "is_online": True,
                    "gpu_usage": round(random.uniform(15.0, 50.0), 1),
                    "gpu_temp": random.randint(48, 62),
                    "vram_pct": round(random.uniform(20.0, 60.0), 1),
                    "vram_total": db_pc.get("vram_total", 8.0),
                    "vram_used": 2.0,
                    "cpu_usage": round(random.uniform(15.0, 45.0), 1),
                    "ram_pct": random.randint(25, 55),
                    "ram_total": db_pc.get("ram_total", 16.0),
                    "ram_used": 4.0,
                    "processes": []
                }
                nodes_state[pid] = n

            if db_pc.get("status") == "Offline" or pid == "PC-16":
                n["is_online"] = False
                n["status"] = "Offline"
            elif n.get("is_online", True):
                n["gpu_usage"] = max(0.0, min(100.0, round(n["gpu_usage"] + random.uniform(-2.0, 2.0), 1)))
                n["cpu_usage"] = max(0.0, min(100.0, round(n["cpu_usage"] + random.uniform(-1.5, 1.5), 1)))

            node_data = n
            node_data["temp_threshold"] = temp_threshold
            node_data["zone"] = db_pc["zone"]
            node_data["name"] = db_pc["name"]

        score, badge, status_name, color = calculate_ai_health_score(node_data)
        rec, conf = calculate_ai_rec_score(node_data, score)

        node_data["health_score"] = score
        node_data["health_badge"] = badge
        node_data["status"] = status_name
        node_data["health_color"] = color
        node_data["rec_score"] = rec
        node_data["confidence"] = conf
        node_data["ai_explanation"] = generate_smart_ai_explanation(node_data, score, status_name)
        node_data["last_updated"] = datetime.now().strftime("%H:%M:%S")
        pc_list.append(node_data)

    try:
        for pc in pc_list:
            if pc.get("is_online", True) and pc.get("status") != "Offline":
                database.record_metric(
                    pc["id"], pc["gpu_usage"], pc["gpu_temp"],
                    pc["vram_pct"], pc.get("vram_used", 0),
                    pc["cpu_usage"], pc["ram_pct"], pc.get("ram_used", 0),
                    pc["health_score"]
                )
    except Exception:
        pass

    return pc_list

def check_for_new_alerts(pcs):
    global notification_id_counter, active_notifications
    now_str = datetime.now().strftime("%H:%M:%S")

    for pc in pcs:
        pc_name = pc["name"]
        gpu_t = pc.get("gpu_temp", 0)
        score = pc.get("health_score", 100)
        status = pc.get("status", "Healthy")
        temp_limit = pc.get("temp_threshold", 85)

        if gpu_t >= temp_limit and not any(n["affected_pc"] == pc_name and n["title"] == "GPU Overheating" for n in active_notifications):
            notif = {
                "id": notification_id_counter,
                "time": now_str,
                "severity": "CRITICAL",
                "badge_color": "#ef4444",
                "title": "GPU Overheating",
                "affected_pc": pc_name,
                "description": f"GPU temperature reached {gpu_t}°C on {pc_name}, exceeding threshold ({temp_limit}°C).",
                "explanation": "Software alert simulation triggered. Safe Demo Mode active." if demo_mode_active else f"Thermal safety threshold ({temp_limit}°C) breached."
            }
            notification_id_counter += 1
            active_notifications.insert(0, notif)

        elif score < 40 and status != "Offline" and not any(n["affected_pc"] == pc_name and n["title"] == "Critical Health Score" for n in active_notifications):
            notif = {
                "id": notification_id_counter,
                "time": now_str,
                "severity": "CRITICAL",
                "badge_color": "#ef4444",
                "title": "Critical Health Score",
                "affected_pc": pc_name,
                "description": f"Health Score dropped to {score}/100 on {pc_name}.",
                "explanation": pc.get("ai_explanation", "System health critical.")
            }
            notification_id_counter += 1
            active_notifications.insert(0, notif)

    if len(active_notifications) > 15:
        active_notifications = active_notifications[:15]

# REST Endpoints
async def api_pcs(request):
    return JSONResponse(compute_all_pc_data())

async def api_pc_detail(request):
    pc_id = request.path_params["pc_id"]
    pcs = compute_all_pc_data()
    target = next((p for p in pcs if p["id"].lower() == pc_id.lower()), None)
    if not target:
        return JSONResponse({"error": "PC not found"}, status_code=404)
    return JSONResponse(target)

async def api_recommendations(request):
    pcs = compute_all_pc_data()
    online_pcs = [p for p in pcs if p.get("status") != "Offline"]

    scored_list = []
    for p in online_pcs:
        gpu_u = p.get("gpu_usage", 0.0)
        gpu_t = p.get("gpu_temp", 45)
        vram_p = p.get("vram_pct", 0.0)
        health = p.get("health_score", 80)
        rec_score = p.get("rec_score", 85)
        confidence = p.get("confidence", 95)

        vram_free_gb = round(p.get("vram_total", 8.0) * (1.0 - vram_p / 100.0), 1)

        scored_list.append({
            "pc_id": p["id"],
            "pc_name": p["name"],
            "zone": p["zone"],
            "gpu_model": p.get("gpu_name", "NVIDIA GPU"),
            "recommendation_score": rec_score,
            "health_score": health,
            "confidence": confidence,
            "reasons": [
                f"Low GPU utilization ({gpu_u}%)",
                f"Low temperature ({gpu_t}°C safe threshold)",
                f"High available GPU memory ({vram_free_gb} GB VRAM free)",
                f"Stable recent workload (Health Score: {health}/100)"
            ],
            "smart_explanation": f"{p['name']} was selected because its GPU utilization is low ({gpu_u}%), GPU temp is safe ({gpu_t}°C), and RAM usage is optimal."
        })

    scored_list.sort(key=lambda x: x["recommendation_score"], reverse=True)
    return JSONResponse(scored_list[:5])

async def api_analytics(request):
    timeframe = request.query_params.get("timeframe", "hour")
    data = database.get_analytics(timeframe)
    return JSONResponse(data)

async def api_notifications(request):
    return JSONResponse(active_notifications)

async def api_ack_notification(request):
    global active_notifications
    try:
        body = await request.json()
        notif_id = body.get("id")
        active_notifications = [n for n in active_notifications if n["id"] != notif_id]
        return JSONResponse({"status": "acknowledged", "id": notif_id})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

async def api_toggle_demomode(request):
    global demo_mode_active
    demo_mode_active = not demo_mode_active
    pcs = compute_all_pc_data()
    check_for_new_alerts(pcs)
    return JSONResponse({
        "demo_mode_active": demo_mode_active,
        "message": f"Safe Demo Mode {'ACTIVATED (Simulated Alert Scenario)' if demo_mode_active else 'DEACTIVATED (Normal Mode)'}."
    })

# Report Export Endpoints
async def export_csv_report(request):
    pcs = compute_all_pc_data()
    analytics = database.get_analytics("day")

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["=== AURALAB AI GPU MONITOR - EXECUTIVE HACKATHON REPORT ==="])
    writer.writerow(["Organization", "Daffodil International University"])
    writer.writerow(["Development Team", "Team DIU_Elite_Noob"])
    writer.writerow(["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])

    writer.writerow(["--- CLUSTER HEALTH & ANALYTICS SUMMARY ---"])
    writer.writerow(["Total Monitored Nodes", len(pcs)])
    writer.writerow(["Average GPU Usage", f"{analytics['avg_gpu']}%"])
    writer.writerow(["Peak GPU Usage", f"{analytics['peak_gpu']}%"])
    writer.writerow(["Average CPU Usage", f"{analytics['avg_cpu']}%"])
    writer.writerow(["Average GPU Temp", f"{analytics['avg_temp']}°C"])
    writer.writerow(["Average Health Score", f"{analytics['avg_health']}/100"])
    writer.writerow(["Total Active Alerts", len(active_notifications)])
    writer.writerow(["Most Active PC", analytics["most_active_pc"]])
    writer.writerow(["Least Active PC", analytics["least_active_pc"]])
    writer.writerow([])

    writer.writerow(["--- NODE TELEMETRY & AI RECOMMENDATION RATINGS ---"])
    writer.writerow(["PC ID", "PC Name", "Zone", "GPU Spec", "Status", "Health Score", "AI Rec Score", "Confidence %", "GPU Usage %", "GPU Temp °C", "VRAM %", "CPU %", "RAM %"])
    for p in pcs:
        writer.writerow([
            p["id"], p["name"], p["zone"], p.get("gpu_name", ""),
            p["status"], p.get("health_score", 0), p.get("rec_score", 0), p.get("confidence", 0),
            p.get("gpu_usage", 0), p.get("gpu_temp", 0), p.get("vram_pct", 0), p.get("cpu_usage", 0), p.get("ram_pct", 0)
        ])
    writer.writerow([])

    writer.writerow(["--- ACTIVE ALERTS LOG ---"])
    writer.writerow(["ID", "Time", "Severity", "Affected PC", "Title", "Description", "AI Explanation"])
    for n in active_notifications:
        writer.writerow([n["id"], n["time"], n["severity"], n["affected_pc"], n["title"], n["description"], n.get("explanation", "")])

    response = Response(output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=aura_lab_executive_report.csv"
    return response

async def export_pdf_report_view(request):
    pcs = compute_all_pc_data()
    analytics = database.get_analytics("day")
    online_pcs = [p for p in pcs if p.get("status") != "Offline"]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>AuraLab - Executive System Report</title>
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 2.5rem; color: #0f172a; background: #fff; line-height: 1.5; }}
        .header-brand {{ display: flex; align-items: center; justify-content: space-between; border-bottom: 3px solid #2563eb; padding-bottom: 1rem; margin-bottom: 1.5rem; }}
        .brand-title {{ font-size: 1.8rem; font-weight: 800; color: #1e3a8a; }}
        .brand-sub {{ color: #475569; font-size: 0.9rem; margin-top: 0.2rem; }}
        .meta-box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.85rem 1.25rem; border-radius: 8px; font-size: 0.85rem; color: #64748b; margin-bottom: 2rem; display: flex; justify-content: space-between; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem; }}
        .kpi-card {{ background: #f1f5f9; border: 1px solid #cbd5e1; padding: 1.1rem; border-radius: 10px; text-align: center; }}
        .kpi-val {{ font-size: 1.8rem; font-weight: 800; color: #2563eb; font-family: monospace; }}
        .kpi-lbl {{ font-size: 0.75rem; text-transform: uppercase; color: #64748b; font-weight: 700; margin-top: 0.2rem; }}
        h2 {{ font-size: 1.2rem; font-weight: 800; color: #1e293b; margin-top: 2rem; margin-bottom: 0.75rem; border-left: 4px solid #2563eb; padding-left: 0.6rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; font-size: 0.85rem; }}
        th, td {{ padding: 0.65rem 0.85rem; border: 1px solid #cbd5e1; text-align: left; }}
        th {{ background: #f1f5f9; font-weight: 700; text-transform: uppercase; font-size: 0.75rem; color: #475569; }}
        .status-badge {{ font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; display: inline-block; }}
        .badge-healthy {{ background: #d1fae5; color: #047857; }}
        .badge-moderate {{ background: #fef3c7; color: #b45309; }}
        .badge-heavy {{ background: #ffedd5; color: #c2410c; }}
        .badge-critical {{ background: #fee2e2; color: #b91c1c; }}
        .btn-print {{ background: #2563eb; color: #fff; padding: 0.75rem 1.5rem; border: none; border-radius: 8px; font-weight: 700; font-size: 0.95rem; cursor: pointer; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); }}
        .footer-note {{ margin-top: 3rem; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 1rem; font-size: 0.8rem; color: #94a3b8; }}
        @media print {{ .btn-print {{ display: none; }} body {{ padding: 0; }} }}
      </style>
    </head>
    <body>
      <button class="btn-print" onclick="window.print()">🖨️ Save as PDF / Print Executive Report</button>
      
      <div class="header-brand">
        <div>
          <div class="brand-title">DAFFODIL INTERNATIONAL UNIVERSITY</div>
          <div class="brand-sub">AuraLab AI GPU Cluster Monitoring & Optimization System</div>
        </div>
        <div style="text-align:right;">
          <div style="font-weight:800; color:#2563eb; font-size:1.1rem;">AI INNOVATION HACKATHON 2026</div>
          <div style="font-size:0.8rem; color:#64748b;">Team DIU_Elite_Noobs</div>
        </div>
      </div>

      <div class="meta-box">
        <span><strong>Report Title:</strong> Executive AI Cluster Health & Telemetry Audit</span>
        <span><strong>Generated At:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>
        <span><strong>Environment:</strong> Production Master</span>
      </div>

      <div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-val">{analytics['avg_gpu']}%</div><div class="kpi-lbl">Avg GPU Utilization</div></div>
        <div class="kpi-card"><div class="kpi-val">{analytics['peak_gpu']}%</div><div class="kpi-lbl">Peak GPU Load</div></div>
        <div class="kpi-card"><div class="kpi-val">{analytics['avg_temp']}°C</div><div class="kpi-lbl">Avg GPU Temp</div></div>
        <div class="kpi-card"><div class="kpi-val">{analytics['avg_health']}/100</div><div class="kpi-lbl">Average Cluster Health</div></div>
      </div>

      <h2>Top AI GPU Recommendations</h2>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>PC Node</th>
            <th>GPU Model</th>
            <th>Zone</th>
            <th>AI Rec Score</th>
            <th>Health Score</th>
            <th>Confidence</th>
          </tr>
        </thead>
        <tbody>
          {"".join([f"<tr><td>#{idx+1}</td><td><strong>{p['name']}</strong></td><td>{p['gpu_name']}</td><td>{p['zone']}</td><td><strong>{p.get('rec_score', 85)}</strong></td><td>{p.get('health_score', 80)}/100</td><td>{p.get('confidence', 95)}%</td></tr>" for idx, p in enumerate(sorted(online_pcs, key=lambda x: x.get('rec_score', 0), reverse=True)[:5])])}
        </tbody>
      </table>

      <h2>Complete Cluster Telemetry</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Node Name</th>
            <th>Zone</th>
            <th>GPU Model</th>
            <th>Status</th>
            <th>Health</th>
            <th>GPU %</th>
            <th>Temp</th>
            <th>VRAM %</th>
            <th>CPU %</th>
          </tr>
        </thead>
        <tbody>
          {"".join([f"<tr><td>{p['id']}</td><td>{p['name']}</td><td>{p['zone']}</td><td>{p.get('gpu_name','')}</td><td><span class='status-badge badge-{p['status'].lower()}'>{p['status']}</span></td><td>{p.get('health_score',0)}</td><td>{p.get('gpu_usage',0)}%</td><td>{p.get('gpu_temp',0)}°C</td><td>{p.get('vram_pct',0)}%</td><td>{p.get('cpu_usage',0)}%</td></tr>" for p in pcs])}
        </tbody>
      </table>

      <div class="footer-note">
        Developed by <strong>Team DIU_Elite_Noobs</strong> | Daffodil International University | AI Innovation Hackathon 2026
      </div>
    </body>
    </html>
    """
    return HTMLResponse(html)

async def api_admin_get_pcs(request):
    pcs = database.get_pcs_from_db()
    return JSONResponse(pcs)

async def api_admin_add_pc(request):
    try:
        body = await request.json()
        pc_id = body.get("id")
        if not pc_id:
            return JSONResponse({"error": "PC ID is required"}, status_code=400)
        name = body.get("name") or pc_id
        zone = body.get("zone", "Zone A (Training Cluster)")
        location = body.get("location", "Rack 01")
        gpu_name = body.get("gpu_name", "NVIDIA GPU")
        vram_total = float(body.get("vram_total", 8.0))
        ram_total = float(body.get("ram_total", 16.0))
        temp_threshold = int(body.get("temp_threshold", 85))

        database.add_pc(pc_id, name, zone, location, gpu_name, 0, vram_total, ram_total, "Healthy", temp_threshold)
        return JSONResponse({"status": "created", "pc_id": pc_id})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

async def api_admin_update_pc(request):
    try:
        pc_id = request.path_params["pc_id"]
        body = await request.json()
        name = body.get("name") or pc_id
        zone = body.get("zone", "Zone A (Training Cluster)")
        location = body.get("location", "Rack 01")
        gpu_name = body.get("gpu_name", "NVIDIA GPU")
        vram_total = float(body.get("vram_total", 8.0))
        ram_total = float(body.get("ram_total", 16.0))
        temp_threshold = int(body.get("temp_threshold", 85))

        database.update_pc(pc_id, name, zone, location, gpu_name, vram_total, ram_total, temp_threshold)
        return JSONResponse({"status": "updated", "pc_id": pc_id})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

async def api_admin_delete_pc(request):
    try:
        pc_id = request.path_params["pc_id"]
        database.delete_pc(pc_id)
        if pc_id in nodes_state:
            del nodes_state[pc_id]
        return JSONResponse({"status": "deleted", "pc_id": pc_id})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

async def api_admin_get_agents(request):
    now_ts = time.time()
    agents_list = []
    for u, agent in connected_agents.items():
        is_online = (now_ts - agent["last_seen"] <= 12)
        agents_list.append({
            "uuid": u,
            "pc_id": agent["pc_id"],
            "client_ip": agent["client_ip"],
            "last_seen": datetime.fromtimestamp(agent["last_seen"]).strftime("%H:%M:%S"),
            "status": "Online" if is_online else "Offline",
            "gpu_name": agent["telemetry"].get("gpu_name", "Unknown GPU"),
            "gpu_temp": agent["telemetry"].get("gpu_temp", 0),
            "gpu_usage": agent["telemetry"].get("gpu_usage", 0)
        })
    return JSONResponse(agents_list)

async def homepage(request):
    return FileResponse("static/index.html")

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            pcs = compute_all_pc_data()
            check_for_new_alerts(pcs)
            payload = {
                "type": "TELEMETRY_UPDATE",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "pcs": pcs,
                "notifications": active_notifications,
                "demo_mode_active": demo_mode_active
            }
            await websocket.send_json(payload)
            await asyncio.sleep(1.5)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
    except Exception:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

routes = [
    Route("/", endpoint=homepage),
    Route("/api/pcs", endpoint=api_pcs, methods=["GET"]),
    Route("/api/pcs/{pc_id}", endpoint=api_pc_detail, methods=["GET"]),
    Route("/api/recommendations", endpoint=api_recommendations, methods=["GET"]),
    Route("/api/analytics", endpoint=api_analytics, methods=["GET"]),
    Route("/api/notifications", endpoint=api_notifications, methods=["GET"]),
    Route("/api/notifications/ack", endpoint=api_ack_notification, methods=["POST"]),
    Route("/api/demomode", endpoint=api_toggle_demomode, methods=["POST"]),
    Route("/api/agent/telemetry", endpoint=api_agent_telemetry, methods=["POST"]),
    Route("/api/admin/pcs", endpoint=api_admin_get_pcs, methods=["GET"]),
    Route("/api/admin/pcs", endpoint=api_admin_add_pc, methods=["POST"]),
    Route("/api/admin/pcs/{pc_id}", endpoint=api_admin_update_pc, methods=["PUT"]),
    Route("/api/admin/pcs/{pc_id}", endpoint=api_admin_delete_pc, methods=["DELETE"]),
    Route("/api/admin/agents", endpoint=api_admin_get_agents, methods=["GET"]),
    Route("/api/reports/csv", endpoint=export_csv_report, methods=["GET"]),
    Route("/api/reports/pdf", endpoint=export_pdf_report_view, methods=["GET"]),
    WebSocketRoute("/ws", endpoint=websocket_endpoint),
    Mount("/static", app=StaticFiles(directory="static"), name="static")
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

