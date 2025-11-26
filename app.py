import os
import requests
import time
import re
import datetime
from flask import Flask, jsonify, request, render_template
from utils import fetch_and_update_aum_and_inav, fetch_and_update_ltp, format_uptime, get_symbol_info
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from tasks import *
import os

def create_app(*args, **kwargs):
    app = Flask(__name__)
    if 'etfs.csv' not in os.listdir('.'):
        print("etfs.csv not found in current directory. Building it from raw.csv...")
        raw_df = pd.read_csv('raw.csv')
        raw_df = fetch_and_update_aum_and_inav(raw_df)
        raw_df = fetch_and_update_ltp(raw_df)
        raw_df.to_csv('etfs.csv', index=False)
    
    # start time for uptime calculation
    START_TIME = time.time()

    # Set up the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(task_update_ltp_and_discount, CronTrigger.from_crontab('*/15 9-15 * * *'))  # runs at every 15th minute past every hour from 9 through 15.
    scheduler.add_job(task_update_aum_and_inav, CronTrigger.from_crontab('0 20 * * *'))  # runs every day at 20:00.
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        # Guard your scheduler start with the WERKZEUG_RUN_MAIN check to ensure it only runs in the main process.
        scheduler.start()
    @app.route('/health', methods=['GET'])
    def health_check():
        """Default health endpoint.

        - GET /health -> basic liveness info (status, version, uptime, timestamp)
        - GET /health?full=1 -> includes optional external checks (may be slower)
        Returns 200 when the app is healthy. If `full` checks are requested and
        any external check fails, returns 503.
        """
        now = time.time()
        uptime = now - START_TIME

        payload = {
            "status": "ok",
            "uptime_seconds": round(uptime, 2),
            "uptime": format_uptime(uptime),
        }
        # full = request.args.get("full") or request.args.get("check")
        # if full and str(full).lower() in ("1", "true", "yes", "on"):
        #     checks = {}
        #     # Example external dependency check - NSE site used in earlier code
        #     checks["nseindia.com"] = _check_url("https://www.nseindia.com")

        #     payload["checks"] = checks
        #     all_ok = all(c.get("ok") for c in checks.values())
        #     if not all_ok:
        #         payload["status"] = "degraded"
        #         return jsonify(payload), 503
        return jsonify(payload), 200
    
    @app.route('/', methods=['GET'])
    def index():
        df = pd.read_csv('etfs.csv')
        etfs = df.to_dict(orient='records')
        categories = sorted(df['category'].dropna().unique().tolist())
        return render_template('index.html', etfs=etfs, categories=categories)
    return app