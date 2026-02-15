import os
import sys

# Fix Windows encoding issue with EasyOCR's Unicode progress bar characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS
from database import init_db, get_all_analyses, get_analysis_by_id, delete_analysis, get_analyses_by_ids
from services.analysis_service import analyze_image
from services.pdf_service import generate_pdf

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main single-page application."""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Upload an image and run full analysis pipeline."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Use: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    # Save uploaded file
    filename = secure_filename(file.filename)
    # Add timestamp to avoid collisions
    import time
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{int(time.time())}{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        result = analyze_image(filepath)
        # Make image path relative for frontend
        result['image_url'] = f'/static/uploads/{filename}'
        # Remove non-serializable keys if any
        result.pop('breakdown', None)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/api/history', methods=['GET'])
def api_history():
    """Return all analysis history."""
    analyses = get_all_analyses()
    # Add image URLs
    for a in analyses:
        if a.get('image_path'):
            a['image_url'] = '/static/uploads/' + os.path.basename(a['image_path'])
    return jsonify(analyses), 200


@app.route('/api/analysis/<int:analysis_id>', methods=['GET'])
def api_get_analysis(analysis_id):
    """Return a single analysis by ID."""
    analysis = get_analysis_by_id(analysis_id)
    if not analysis:
        return jsonify({'error': 'Analysis not found'}), 404
    if analysis.get('image_path'):
        analysis['image_url'] = '/static/uploads/' + os.path.basename(analysis['image_path'])
    return jsonify(analysis), 200


@app.route('/api/analysis/<int:analysis_id>', methods=['DELETE'])
def api_delete_analysis(analysis_id):
    """Delete an analysis by ID."""
    deleted = delete_analysis(analysis_id)
    if deleted:
        return jsonify({'message': 'Deleted successfully'}), 200
    return jsonify({'error': 'Analysis not found'}), 404


@app.route('/api/compare', methods=['POST'])
def api_compare():
    """Compare multiple analyses by IDs."""
    data = request.get_json()
    if not data or 'ids' not in data:
        return jsonify({'error': 'Provide list of analysis IDs'}), 400

    ids = data['ids']
    if len(ids) < 2:
        return jsonify({'error': 'Need at least 2 products to compare'}), 400

    analyses = get_analyses_by_ids(ids)
    for a in analyses:
        if a.get('image_path'):
            a['image_url'] = '/static/uploads/' + os.path.basename(a['image_path'])

    return jsonify(analyses), 200


@app.route('/api/report/<int:analysis_id>', methods=['GET'])
def api_report(analysis_id):
    """Generate and download PDF report."""
    analysis = get_analysis_by_id(analysis_id)
    if not analysis:
        return jsonify({'error': 'Analysis not found'}), 404

    try:
        pdf_path = generate_pdf(analysis)
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f'nutricheck_report_{analysis_id}.pdf',
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
