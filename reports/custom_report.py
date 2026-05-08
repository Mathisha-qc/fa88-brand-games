import json
import time
import shutil
from datetime import datetime
from pathlib import Path

# CMD NAME MAPPING
from utils.ws_commands import TAIXIU_MINI_CMD, WS_CMD, TAIXIU_MD5_MINI_CMD, TREN_DUOI_CMD, MINI_POKER_CMD

ALL_WS_CMDS = {}
ALL_WS_CMDS.update({str(v): k for k, v in TAIXIU_MINI_CMD.items()})
ALL_WS_CMDS.update({str(v): k for k, v in WS_CMD.items()})
ALL_WS_CMDS.update({str(v): k for k, v in TAIXIU_MD5_MINI_CMD.items()})
ALL_WS_CMDS.update({str(v): k for k, v in TREN_DUOI_CMD.items()})
ALL_WS_CMDS.update({str(v): k for k, v in MINI_POKER_CMD.items()})


def get_cmd_name(cmd):
    return ALL_WS_CMDS.get(str(cmd), f"WS CMD {cmd}")

class ReportStep:
    def __init__(self, name, status, message="", screenshot=None, extra=None):
        self.name = name
        self.status = status
        self.message = message
        self.screenshot = screenshot
        self.timestamp = datetime.now().strftime("%H:%M:%S")
        self.extra = extra or {}

class ExecutionReport:
    def __init__(self):
        self.title = "HitClub Automation Report"
        self.base_url = ""
        self.username = ""
        self.browser_name = "Chrome"
        self.captcha_mode = ""
        
        self.game_name = "" 
        self.video_path = None

        # ✅ Create a unique temporary folder for THIS specific run
        self.run_dir = Path(f"reports/temp_run_{int(time.time())}")
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.started_at = datetime.now()
        self.finished_at = None
        self.status = "RUNNING"
        

        self.steps = []

    def add_step(self, name, status, message="", screenshot=None, extra=None):
        self.steps.append(ReportStep(name, status, message, screenshot, extra))

    def finish(self, status="PASSED"):
        self.status = status
        self.finished_at = datetime.now()



# =========================
# GLOBAL REPORT INSTANCE
# =========================
report = ExecutionReport()


# =========================
# HTML GENERATOR
# =========================
def write_html_report(report_obj: ExecutionReport, output_dir: Path):

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / "custom_report.html"

    # ✅ CREATE THE SCREENSHOT FOLDER INSIDE THE TEMP ZIP FOLDER
    screenshot_dir = output_dir / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    # ✅ Fix screenshot paths 
    for step in report_obj.steps: 
       if step.screenshot: 
        original_path = Path(step.screenshot)
            
        # If the physical file exists, copy it into our pristine zip folder
        if original_path.exists():
            new_path = screenshot_dir / original_path.name
                
            # Prevent copying the file onto itself if it's already there
            if original_path.resolve() != new_path.resolve():
                    try:
                        shutil.copy2(original_path, new_path)
                    except Exception as e:
                        print(f"[WARN] Could not copy screenshot {original_path}: {e}")
            
        # Update the HTML to look for the image inside the local screenshots folder
        step.screenshot = f"screenshots/{original_path.name}"
    
    duration = ""
    if report_obj.finished_at:
        duration = round(
            (report_obj.finished_at - report_obj.started_at).total_seconds(), 2
        )

    status_color = "red" if report_obj.status == "FAILED" else "lime"

    html = []
    html.append("<html><head><title>Test Report</title>")

    html.append("""
    <style>
        body { font-family: Arial; background:#f4f4f4; }
        .container { width: 90%; margin:auto; }

        h1 { text-align:center; }

        .summary {
            background:white;
            padding:15px;
            border-radius:10px;
            margin-bottom:20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .step {
            background:white;
            padding:15px;
            margin:15px 0;
            border-radius:10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .PASSED { border-left: 6px solid green; }
        .FAILED { border-left: 6px solid red; }
        .INFO { border-left: 6px solid blue; }

        h3 {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .status {
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            color: white;
        }

        .status.PASSED { background: green; }
        .status.FAILED { background: red; }
        .status.INFO { background: blue; }

        img {
            width: 100%;
            max-width: 900px;
            margin-top:10px;
            border-radius:8px;
            border:1px solid #ddd;
            display:block;
            cursor:pointer;
        }

        img:hover {
            transform: scale(1.05);
        }

        .time {
            color:#666;
            font-size:12px;
        }
    </style>
    <script>
    function togglePayload(id) {
        var row = document.getElementById(id);
        if (row.style.display === "none") {
            row.style.display = "table-row";
        } else {
            row.style.display = "none";
        }
    }
    </script>
    """)

    html.append("</head><body>")
    html.append("<div class='container'>")

     # ================= HEADER =================
    html.append(f"""
    <div style="
        background: linear-gradient(135deg, #1f2937, #374151);
        color: white;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 25px;
    ">

        <h1 style="
            margin:0;
            font-size: 28px;
            font-weight: 600;
            letter-spacing: 0.5px;
    ">
        {report_obj.title}
        <span style="
            font-size: 28px;
            font-weight: 600;
            margin-left: 8px;
        ">
           - {report_obj.game_name or "Game Not Set"}
        </span>
    </h1>

        <p>
            Execution pipeline and detailed step validation.
            Status: <b style="color:{status_color};">
                {report_obj.status}
            </b>
        </p>

        <div style="display:flex; justify-content:space-between; margin-top:20px;">

            <div>
                <p><b>Environment</b></p>
                <p>Target URL: {report_obj.base_url or "-"}</p>
                <p>Test User: {report_obj.username or "-"}</p>
                <p>Captcha Mode: {report_obj.captcha_mode or "-"}</p>
            </div>

            <div>
                <p><b>Execution</b></p>
                <p>Duration: {duration} seconds</p>
                <p>Started: {report_obj.started_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p>Finished: {report_obj.finished_at.strftime("%Y-%m-%d %H:%M:%S") if report_obj.finished_at else "-"}</p>
            </div>

        </div>
    </div>
    """)
    
    # ADD THIS VIDEO BLOCK:
    if getattr(report_obj, "video_path", None):
        rel_vid_path = Path(report_obj.video_path).name # Only the filename is needed since it's in root
        html.append(f"""
        <div style="background:white; padding:15px; border-radius:10px; margin-bottom:20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align:center;">
            <h3 style='margin-top:0; color:#333; text-align:left;'>🎥 Execution Video</h3>
            <video width="100%" style="max-width: 900px; border-radius:8px; border:1px solid #ddd; background:black;" controls>
              <source src="{rel_vid_path}" type="video/mp4">
            </video>
        </div>
        """)

    # ================= SPLIT STEPS =================
    ws_steps = [s for s in report_obj.steps if s.extra and "cmd" in s.extra]
    other_steps = [s for s in report_obj.steps if not (s.extra and "cmd" in s.extra)]

    # ================= WS STEPS =================
    if ws_steps:
     # Create Payload Export Directory
     ws_dir = output_dir / "ws_payloads"
     ws_dir.mkdir(parents=True, exist_ok=True)

     html.append("<h2 style='color:#6a5acd;'>WebSocket Commands</h2>")

     html.append("""
    <table style="width:100%; border-collapse: collapse; margin-bottom:20px; background:white;">
        <tr style="background:#eee;">
            <th style="padding:10px; border:1px solid #ddd;">Command</th>
            <th style="padding:10px; border:1px solid #ddd;">Time</th>
            <th style="padding:10px; border:1px solid #ddd;">Status</th>
        </tr>
    """)

    for i, step in enumerate(ws_steps):
        cmd = step.extra["cmd"]
        cmd_name = get_cmd_name(cmd)
        payload = step.extra.get("payload", {})

        # ✅ FIXED: Actually save the physical JSON file to the folder!
        safe_name = f"step_{i+1}_{cmd_name.replace(' ', '_')}.json"
        (ws_dir / safe_name).write_text(json.dumps(payload, indent=2), encoding="utf-8")

        html.append(f"""
        <tr onclick="togglePayload('payload_{i}')" style="cursor:pointer;">
            <td style="padding:10px; border:1px solid #ddd;">
                <b>{cmd_name} ({cmd})</b><br>
            </td>
            <td style="padding:10px; border:1px solid #ddd;">
                {step.timestamp}
            </td>
            <td style="padding:10px; border:1px solid #ddd; color:{'green' if step.status=='PASSED' else 'red'};">
                {step.status}
            </td>
        </tr>

        <tr id="payload_{i}" style="display:none; background:#fafafa;">
            <td colspan="3" style="padding:10px; border:1px solid #ddd;">
                <pre>{json.dumps(payload, indent=2)}</pre>
            </td>
        </tr>
        """)

    html.append("</table>")

    # ================= NORMAL STEPS =================
    html.append("<h2>Execution Steps</h2>")

    for step in other_steps:
        html.append(f"<div class='step {step.status}'>")
        html.append(f"""
        <h3>
            {step.name}
            <span class='status {step.status}'>{step.status}</span>
        </h3>
        """)

        if step.message:
            html.append(f"<p>{step.message}</p>")

        html.append(f"<p class='time'><b>Time:</b> {step.timestamp}</p>")

        if step.screenshot:
         html.append(f"<img src='{step.screenshot}' />")
           

        html.append("</div>")

    # ================= IMAGE ZOOM =================
    html.append("""
    <script>
    document.querySelectorAll("img").forEach(img => {
        img.onclick = () => {
            const w = window.open("");
            w.document.write(`<img src="${img.src}" style="width:100%">`);
        };
    });
    </script>
    """)

    html.append("</div></body></html>")

    file_path.write_text("".join(html), encoding="utf-8")

    return file_path