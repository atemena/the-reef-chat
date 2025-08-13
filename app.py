from flask import Flask, render_template, request, jsonify, Response, session, redirect, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv
import json
from werkzeug.utils import secure_filename
from utils.rag_chain import CAGChain

load_dotenv()

app = Flask(__name__)
CORS(app)

# Session configuration
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key-change-this')
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Rate limiting setup
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri="memory://"
)

# Rate limit error handler
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'error': 'Rate limit exceeded. Please wait before making more requests.',
        'retry_after': e.retry_after if hasattr(e, 'retry_after') else 60
    }), 429

# Security headers
@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com;"
    return response

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RAG_DOCS_FOLDER'] = 'rag_docs'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RAG_DOCS_FOLDER'], exist_ok=True)

# Initialize CAG chain with the TXT file
handbook_path = os.path.join(app.config['RAG_DOCS_FOLDER'], 'The Reef Administration Handbook.txt')
cag_chain = CAGChain(handbook_path)

# CAG system initializes automatically with the PDF

# Password protection
def require_auth():
    """Check if user is authenticated"""
    app_password = os.getenv('APP_PASSWORD')
    flask_env = os.getenv('FLASK_ENV', 'development')
    
    if not app_password:
        if flask_env == 'production':
            return False  # Force authentication in production
        return True  # Allow access in development if no password set
    return session.get('authenticated') == True

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        app_password = os.getenv('APP_PASSWORD')
        
        if app_password and password == app_password:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    # Debug info for production
    app_password = os.getenv('APP_PASSWORD')
    flask_env = os.getenv('FLASK_ENV', 'development')
    is_authenticated = session.get('authenticated')
    
    print(f"DEBUG - APP_PASSWORD set: {bool(app_password)}")
    print(f"DEBUG - FLASK_ENV: {flask_env}")
    print(f"DEBUG - Session authenticated: {is_authenticated}")
    print(f"DEBUG - require_auth() result: {require_auth()}")
    
    if not require_auth():
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/status')
@limiter.limit("30 per minute")
def status():
    """Get application and document status."""
    if not require_auth():
        return jsonify({'error': 'Authentication required'}), 401
    
    return jsonify({
        'app_status': 'healthy',
        'handbook_loaded': cag_chain.has_document(),
        'handbook_path': handbook_path,
        'openai_configured': cag_chain.openai_client is not None
    })

# Upload endpoint removed - CAG works with the single cached PDF

@app.route('/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    if not require_auth():
        return jsonify({'error': 'Authentication required'}), 401
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Check if we have the handbook cached
    if not cag_chain.has_document():
        def no_handbook_response():
            yield f"data: {json.dumps({'response': 'The Reef Administration Handbook is not available or could not be loaded.'})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        return Response(no_handbook_response(), mimetype='text/event-stream')
    
    def generate_response():
        try:
            for chunk in cag_chain.generate_response(query, stream=True):
                yield f"data: {json.dumps({'response': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
    
    return Response(generate_response(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)