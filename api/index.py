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
        if 'route=' in qs:
            params = parse_qs(qs)
            route_val = params.get('route', [''])[0].strip()
            if route_val == 'admin':
                environ['PATH_INFO'] = '/admin'
            elif route_val in ['index', '', '/']:
                environ['PATH_INFO'] = '/'
            elif route_val.startswith('api/'):
                environ['PATH_INFO'] = '/' + route_val
            elif route_val.startswith('/'):
                environ['PATH_INFO'] = route_val
            else:
                environ['PATH_INFO'] = '/' + route_val
        elif '__vercel_path=' in qs:
            params = parse_qs(qs)
            vpath = params.get('__vercel_path', ['/'])[0].strip()
            if 'admin' in vpath:
                environ['PATH_INFO'] = '/admin'
            elif not vpath or vpath in ['/', '//']:
                environ['PATH_INFO'] = '/'
            else:
                environ['PATH_INFO'] = vpath if vpath.startswith('/') else '/' + vpath
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

