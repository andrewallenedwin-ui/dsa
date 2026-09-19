import sys
import os

# Add root directory to sys.path so Vercel can import main, model, dsa_structures
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from main import app

class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        orig_path = (
            environ.get('HTTP_X_MATCHED_PATH') or
            environ.get('HTTP_X_VERCEL_URI') or
            environ.get('HTTP_X_FORWARDED_URI')
        )
        if orig_path:
            if '?' in orig_path:
                orig_path = orig_path.split('?', 1)[0]
            environ['PATH_INFO'] = orig_path
        else:
            path_info = environ.get('PATH_INFO', '')
            for prefix in ['/api/index.py', '/api/index']:
                if path_info.startswith(prefix):
                    new_path = path_info[len(prefix):]
                    if not new_path or not new_path.startswith('/'):
                        new_path = '/' + new_path
                    environ['PATH_INFO'] = new_path
                    break
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

