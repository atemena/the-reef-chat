from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
from werkzeug.utils import secure_filename
from utils.rag_chain import CAGChain

load_dotenv()

app = Flask(__name__)
CORS(app)

# Security headers
@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com;"
    return response

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RAG_DOCS_FOLDER'] = 'rag_docs'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RAG_DOCS_FOLDER'], exist_ok=True)

# Initialize CAG chain with the PDF
pdf_path = os.path.join(app.config['RAG_DOCS_FOLDER'], 'The Reef Administration Handbook.pdf')
cag_chain = CAGChain(pdf_path)

# CAG system initializes automatically with the PDF

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/status')
def status():
    """Get application and document status."""
    return jsonify({
        'app_status': 'healthy',
        'pdf_loaded': cag_chain.has_document(),
        'pdf_path': pdf_path,
        'openai_configured': cag_chain.openai_client is not None
    })

# Upload endpoint removed - CAG works with the single cached PDF

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Check if we have the PDF cached
    if not cag_chain.has_document():
        def no_pdf_response():
            yield f"data: {json.dumps({'response': 'PDF document not available or could not be loaded.'})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        return Response(no_pdf_response(), mimetype='text/event-stream')
    
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