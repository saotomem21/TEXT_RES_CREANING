from flask import Flask, request, render_template, redirect, url_for, send_file
import os
import time
import zipfile
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
    if 'files' not in request.files:
        return redirect(url_for('index'))
        
    files = request.files.getlist('files')
    if not files or all(file.filename == '' for file in files):
        return redirect(url_for('index'))
        
    output_mode = request.form.get('output_mode', 'separate')  # separate or combined
    
    results = []
    zip_filename = f'cleaned_files_{int(time.time())}.zip'
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
    
    if output_mode == 'combined':
        # Combine all files into one
        combined_data = []
        for file in files:
            if file and file.filename.endswith('.csv'):
                filename = secure_filename(file.filename)
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'cleaned_{filename}')
                
                # Save uploaded file
                file.save(input_path)
                
                # Process CSV
                if clean_csv(input_path, output_path):
                    # Read cleaned data and add to combined list
                    with open(output_path, 'r', encoding='utf-8') as f:
                        if not combined_data:
                            combined_data.append(f.readline())  # Header
                        combined_data.extend(f.readlines())
        
        # Save combined file
        if combined_data:
            combined_output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'combined_output.csv')
            with open(combined_output_path, 'w', encoding='utf-8') as f:
                f.writelines(combined_data)
            
            results.append({
                'filename': 'combined_output.csv',
                'data': ''.join(combined_data)
            })
            
            # Add to zip
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(combined_output_path, 'combined_output.csv')
    else:
        # Process files separately
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in files:
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
                    
                    results.append({
                        'filename': filename,
                        'data': cleaned_data
                    })
                    
                    # Add cleaned file to zip archive
                    zipf.write(output_path, f'cleaned_{filename}')
    
    if results:
        return render_template('index.html', 
                            results=results,
                            download_link=url_for('download', filename=zip_filename))
            
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
        app.run(host='0.0.0.0', port=5002, debug=True)
