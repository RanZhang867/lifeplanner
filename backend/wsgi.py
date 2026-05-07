import sys, os

# Replace YOUR_USERNAME with your PythonAnywhere username
_HOME = "/home/YOUR_USERNAME/lifeplanner"
sys.path.insert(0, _HOME)

os.environ.setdefault("API_TOKEN", "changeme")
os.environ.setdefault("DB_PATH",   _HOME + "/lifeplanner.db")

from a2wsgi import ASGIMiddleware
from main import app
application = ASGIMiddleware(app)
