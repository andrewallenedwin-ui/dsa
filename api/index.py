import sys
import os
from urllib.parse import parse_qs

# Add root directory to sys.path so Vercel can import main, model, dsa_structures
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from main import app

class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get('QUERY_STRING', '')
        if '__vercel_path=' in qs:
            params = parse_qs(qs)
            if '__vercel_path' in params and params['__vercel_path']:
                vpath = params['__vercel_path'][0]
                while '//' in vpath:
                    vpath = vpath.replace('//', '/')
                if not vpath.startswith('/'):
                    vpath = '/' + vpath
                environ['PATH_INFO'] = vpath
        elif environ.get('PATH_INFO') in ['/api/index.py', '/api/index']:
            environ['PATH_INFO'] = '/'
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

