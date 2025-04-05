# usdc_transfer/scheduler/config.py

import os

SCHEDULER_PORT = int(os.getenv("CCIP_SCHEDULER_PORT", 5002))
SCHEDULER_TIMEZONE = os.getenv("CCIP_SCHEDULER_TIMEZONE", "UTC")

JOB_STORE_FILE = os.getenv("CCIP_JOB_STORE", "scheduled_jobs.json")
