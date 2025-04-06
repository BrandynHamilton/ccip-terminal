import logging
import os
import sys

# 🧠 Fix stdout encoding for Windows terminals that can't handle Unicode
if sys.stdout.encoding is None or sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

# 📁 Set up logging paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'log_data')
LOG_PATH = os.path.join(LOG_DIR, 'transfer.log')

# ✅ Ensure log folder exists
os.makedirs(LOG_DIR, exist_ok=True)

# 📦 Logger setup
logger = logging.getLogger("ccip_logger")
logger.setLevel(logging.INFO)

# 📝 File logger
file_handler = logging.FileHandler(LOG_PATH)
file_handler.setLevel(logging.INFO)

# 🖥️ Console logger
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# 🧾 Format logs
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# ➕ Attach both handlers
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
