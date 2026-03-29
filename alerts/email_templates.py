"""
HTML email templates for anomaly alerts and daily summary reports.
Uses string.Template ($variable syntax) to avoid conflicts with CSS braces.
"""
from string import Template

ANOMALY_ALERT_TEMPLATE = Template("""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    body  { font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }
    .wrap { max-width: 600px; margin: 30px auto; background: #fff;
            border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.15); }
    .hdr  { background: #c0392b; color: #fff; padding: 24px 32px; }
    .hdr h1 { margin: 0; font-size: 22px; }
    .body { padding: 28px 32px; color: #333; }
    .kv   { display: flex; justify-content: space-between; padding: 8px 0;
            border-bottom: 1px solid #eee; }
    .kv:last-child { border-bottom: none; }
    .key  { font-weight: bold; color: #555; }
    .val  { color: #222; }
    .sig  { background: #fdecea; border-left: 4px solid #c0392b;
            padding: 10px 14px; margin: 16px 0; border-radius: 4px;
            font-family: monospace; font-size: 13px; }
    .cta  { display: inline-block; margin-top: 20px; padding: 12px 24px;
            background: #c0392b; color: #fff; text-decoration: none;
            border-radius: 4px; font-weight: bold; }
    .ftr  { background: #f9f9f9; padding: 14px 32px; font-size: 12px; color: #999;
            border-top: 1px solid #eee; }
  </style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <h1>&#x1F6A8; ANOMALY DETECTED &mdash; Urban Safety AI</h1>
    <p style="margin:6px 0 0;opacity:.85">Automated alert from the monitoring pipeline</p>
  </div>
  <div class="body">
    <div class="kv"><span class="key">Job ID</span>        <span class="val">#$job_id</span></div>
    <div class="kv"><span class="key">Anomaly window</span><span class="val">$timestamp_start s &ndash; $timestamp_end s</span></div>
    <div class="kv"><span class="key">Anomaly frames</span><span class="val">$anomaly_count of $total_frames ($anomaly_pct%)</span></div>
    <div class="kv"><span class="key">Suspicious frames</span><span class="val">$suspicious_count</span></div>
    <div class="kv"><span class="key">Normal frames</span>  <span class="val">$normal_count</span></div>

    <p style="margin-top:20px;font-weight:bold;color:#c0392b">Triggered signals:</p>
    <div class="sig">$triggered_signals</div>

    <p style="color:#555;font-size:14px">
      Please review the annotated footage and confirm whether this event
      requires immediate action.
    </p>
    <a class="cta" href="http://localhost:8000/docs#/Analysis/get_job_api_jobs__job_id__get">
      View on Dashboard
    </a>
  </div>
  <div class="ftr">Urban Safety AI &bull; Automated Alert &bull; Do not reply to this email.</div>
</div>
</body>
</html>
""")

ANOMALY_ALERT_SUBJECT = "\U0001f6a8 ANOMALY DETECTED \u2014 Urban Safety AI"


SUMMARY_REPORT_TEMPLATE = Template("""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    body  { font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }
    .wrap { max-width: 600px; margin: 30px auto; background: #fff;
            border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.15); }
    .hdr  { background: #2c3e50; color: #fff; padding: 24px 32px; }
    .hdr h1 { margin: 0; font-size: 22px; }
    .body { padding: 28px 32px; color: #333; }
    .stat { text-align: center; display: inline-block; width: 30%;
            background: #ecf0f1; border-radius: 6px; padding: 16px 0; margin: 4px; }
    .stat .num { font-size: 32px; font-weight: bold; color: #2c3e50; }
    .stat .lbl { font-size: 12px; color: #777; margin-top: 4px; }
    .kv   { display: flex; justify-content: space-between; padding: 8px 0;
            border-bottom: 1px solid #eee; }
    .key  { font-weight: bold; color: #555; }
    .ftr  { background: #f9f9f9; padding: 14px 32px; font-size: 12px; color: #999;
            border-top: 1px solid #eee; }
  </style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <h1>&#x1F4CA; Daily Safety Report &mdash; Urban Safety AI</h1>
    <p style="margin:6px 0 0;opacity:.85">$report_date</p>
  </div>
  <div class="body">
    <div style="text-align:center;margin-bottom:20px">
      <div class="stat"><div class="num">$total_jobs</div><div class="lbl">Jobs Processed</div></div>
      <div class="stat"><div class="num">$total_anomalies</div><div class="lbl">Anomalies Detected</div></div>
      <div class="stat"><div class="num">$total_events</div><div class="lbl">Total Events</div></div>
    </div>

    <div class="kv"><span class="key">ANOMALY events</span>  <span class="val">$count_anomaly</span></div>
    <div class="kv"><span class="key">SUSPICIOUS events</span><span class="val">$count_suspicious</span></div>
    <div class="kv"><span class="key">NORMAL events</span>   <span class="val">$count_normal</span></div>
    <div class="kv"><span class="key">Busiest hour (UTC)</span><span class="val">$busiest_hour:00</span></div>
  </div>
  <div class="ftr">Urban Safety AI &bull; Daily Summary &bull; Do not reply to this email.</div>
</div>
</body>
</html>
""")

SUMMARY_REPORT_SUBJECT = "\U0001f4ca Daily Safety Report \u2014 Urban Safety AI"
