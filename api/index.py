from main import app

class VercelPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
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

