from flask import Flask, request, render_template, redirect, url_for, send_file
import os
from text_res_creaning import clean_csv
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))
        
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
        
    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'cleaned_{filename}')
        
        # Save uploaded file
        file.save(input_path)
        
        # Process CSV and get cleaned data
        if clean_csv(input_path, output_path):
            # Read cleaned data for display
            with open(output_path, 'r', encoding='utf-8') as f:
                cleaned_data = f.read()
            
            return render_template('index.html', 
                                 original_filename=filename,
                                 cleaned_data=cleaned_data,
                                 download_link=url_for('download', filename=f'cleaned_{filename}'))
            
    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download(filename):
    return send_file(
        os.path.join(app.config['UPLOAD_FOLDER'], filename),
        as_attachment=True,
        download_name=filename
    )

def build_static_site():
    """Build static HTML files for GitHub Pages"""
    import shutil
    from flask_frozen import Freezer
    
    # Configure freezer
    app.config['FREEZER_DESTINATION'] = 'static'
    app.config['FREEZER_RELATIVE_URLS'] = True
    freezer = Freezer(app)
    
    # Clean and create static directory
    if os.path.exists('static'):
        shutil.rmtree('static')
    os.makedirs('static')
    
    # Freeze the app
    freezer.freeze()
    print("Static site built successfully in ./static directory")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-static', action='store_true', help='Build static site')
    args = parser.parse_args()
    
    if args.build_static:
        build_static_site()
    else:
        app.run(host='0.0.0.0', port=5001, debug=True)
