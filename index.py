import os
import sys

# Ensure root directory is in python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

class VercelWSGIWrapper:
    """Robust WSGI wrapper for Vercel Serverless Functions"""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. Check original URI headers passed by Vercel / edge routing
        orig_uri = (
            environ.get('HTTP_X_VERCEL_ORIGINAL_URI') or
            environ.get('HTTP_X_NOW_ORIGINAL_URI') or
            environ.get('HTTP_X_FORWARDED_URI') or
            environ.get('REQUEST_URI') or
            environ.get('RAW_URI')
        )

        if orig_uri:
            path = orig_uri.split('?')[0]
            environ['PATH_INFO'] = path if path else '/'
            if '?' in orig_uri:
                environ['QUERY_STRING'] = orig_uri.split('?')[1]
        else:
            path = environ.get('PATH_INFO', '/')
            # Strip Vercel handler prefix variations safely
            for prefix in ('/api/index.py', '/api/index'):
                if path == prefix or path == prefix + '/':
                    path = '/'
                    break
                elif path.startswith(prefix + '/'):
                    path = path[len(prefix):]
                    break
            environ['PATH_INFO'] = path if path else '/'

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIWrapper(app.wsgi_app)

