"""
Triadeflow DataSync API
Flask server para validacao de dados
"""

from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
import os
import random
import string
from datetime import datetime
import logging

from contact_validator import ContactDataValidator

# HTML Template para interface de upload
UPLOAD_PAGE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Triadeflow DataSync</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: #fff;
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            color: #1a1a2e;
            font-size: 28px;
            margin-bottom: 5px;
        }
        .logo p {
            color: #666;
            font-size: 14px;
        }
        .upload-area {
            border: 3px dashed #ddd;
            border-radius: 15px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 20px;
        }
        .upload-area:hover {
            border-color: #4CAF50;
            background: #f9fff9;
        }
        .upload-area.dragover {
            border-color: #4CAF50;
            background: #e8f5e9;
        }
        .upload-icon {
            font-size: 50px;
            margin-bottom: 15px;
        }
        .upload-area h3 {
            color: #333;
            margin-bottom: 10px;
        }
        .upload-area p {
            color: #888;
            font-size: 14px;
        }
        input[type="file"] {
            display: none;
        }
        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(76, 175, 80, 0.4);
        }
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .file-info {
            background: #e8f5e9;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        .file-info.show {
            display: block;
        }
        .file-info p {
            color: #2e7d32;
            font-weight: 500;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            display: none;
        }
        .status.loading {
            display: block;
            background: #e3f2fd;
            color: #1565c0;
        }
        .status.success {
            display: block;
            background: #e8f5e9;
            color: #2e7d32;
        }
        .status.error {
            display: block;
            background: #ffebee;
            color: #c62828;
        }
        .features {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
        .features h4 {
            color: #333;
            margin-bottom: 15px;
            font-size: 14px;
        }
        .feature-list {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .feature-item {
            font-size: 12px;
            color: #666;
            padding: 8px;
            background: #f5f5f5;
            border-radius: 5px;
        }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #fff;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
            vertical-align: middle;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>Triadeflow DataSync</h1>
            <p>Validacao e formatacao de contatos para CRM</p>
        </div>

        <form id="uploadForm" enctype="multipart/form-data">
            <div class="upload-area" id="dropZone">
                <div class="upload-icon">📁</div>
                <h3>Arraste seu arquivo aqui</h3>
                <p>ou clique para selecionar</p>
                <p style="margin-top: 10px; font-size: 12px;">.xlsx ou .csv</p>
                <input type="file" id="fileInput" name="file" accept=".xlsx,.xls,.csv">
            </div>

            <div class="file-info" id="fileInfo">
                <p id="fileName"></p>
            </div>

            <button type="submit" class="btn" id="submitBtn" disabled>
                Processar Arquivo
            </button>
        </form>

        <div class="status" id="status"></div>

        <div class="features">
            <h4>O que este sistema faz:</h4>
            <div class="feature-list">
                <div class="feature-item">Valida emails</div>
                <div class="feature-item">Formata telefones BR</div>
                <div class="feature-item">Separa contatos</div>
                <div class="feature-item">Gera IDs unicos</div>
            </div>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const submitBtn = document.getElementById('submitBtn');
        const uploadForm = document.getElementById('uploadForm');
        const status = document.getElementById('status');

        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length) {
                fileInput.files = files;
                updateFileInfo(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                updateFileInfo(e.target.files[0]);
            }
        });

        function updateFileInfo(file) {
            fileName.textContent = '📄 ' + file.name + ' (' + (file.size / 1024).toFixed(1) + ' KB)';
            fileInfo.classList.add('show');
            submitBtn.disabled = false;
        }

        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span>Processando...';
            status.className = 'status loading';
            status.textContent = 'Validando e formatando seus contatos...';

            try {
                const response = await fetch('/validate', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'contatos_validados.csv';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    a.remove();

                    status.className = 'status success';
                    status.textContent = 'Arquivo processado com sucesso! Download iniciado.';
                } else {
                    const error = await response.json();
                    throw new Error(error.error || 'Erro ao processar arquivo');
                }
            } catch (error) {
                status.className = 'status error';
                status.textContent = 'Erro: ' + error.message;
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Processar Arquivo';
            }
        });
    </script>
</body>
</html>
'''

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['OUTPUT_FOLDER'] = '/tmp/outputs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['DEFAULT_DDD'] = os.getenv('DEFAULT_DDD', '85')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def generate_id(length=20):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def split_name(name):
    if pd.isna(name):
        return "", ""
    name_str = str(name).strip()
    if '/' in name_str:
        name_str = name_str.split('/')[0].strip()

    name_parts = name_str.split()
    if len(name_parts) == 0:
        return "", ""
    elif len(name_parts) == 1:
        return name_parts[0].title(), ""
    else:
        return name_parts[0].title(), " ".join(name_parts[1:]).title()

@app.route('/')
def home():
    return render_template_string(UPLOAD_PAGE)

@app.route('/api')
def api_info():
    return jsonify({
        'service': 'Triadeflow DataSync API',
        'version': '1.0.0',
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'GET /': 'Interface de upload',
            'GET /api': 'Info da API',
            'GET /health': 'Health check',
            'POST /validate': 'Validar e formatar contatos'
        }
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/validate', methods=['POST'])
def validate():
    logger.info("Iniciando validacao")

    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nome de arquivo vazio'}), 400

    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")

    try:
        file.save(filepath)

        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            try:
                df = pd.read_excel(filepath, skiprows=1)
            except:
                df = pd.read_excel(filepath)
        else:
            df = pd.read_csv(filepath)

        logger.info(f"Arquivo lido: {len(df)} registros")

        col_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if 'empresa' in col_lower or 'company' in col_lower or 'business' in col_lower:
                col_mapping['business'] = col
            elif 'telefone' in col_lower or 'phone' in col_lower or 'fone' in col_lower:
                col_mapping['phone'] = col
            elif 'email' in col_lower or 'e-mail' in col_lower:
                col_mapping['email'] = col
            elif ('contato' in col_lower or 'nome' in col_lower) and 'phone' not in col_lower:
                col_mapping['contact'] = col

        validator = ContactDataValidator(default_ddd=app.config['DEFAULT_DDD'])
        output_data = []

        for idx, row in df.iterrows():
            phone_main, phone_additional = validator.validate_and_format_phones(
                row.get(col_mapping.get('phone', ''), '')
            )
            email_main, email_additional, _ = validator.validate_and_format_email(
                row.get(col_mapping.get('email', ''), '')
            )

            first_name, last_name = split_name(
                row.get(col_mapping.get('contact', ''), '')
            )

            output_data.append({
                'Contact ID': generate_id(20),
                'Phone': phone_main,
                'Email': email_main,
                'First Name': first_name,
                'Last Name': last_name,
                'Business Name': str(row.get(col_mapping.get('business', ''), '')).strip(),
                'Opportunity ID': generate_id(20),
                'Opportunity name': f'Opportunity - {row.get(col_mapping.get("business", ""), "")}',
                'Pipeline': 'Sales Pipeline',
                'Stage': 'New Lead',
                'Opportunity Value': '',
                'Source': 'DataSync API',
                'Status': 'Open',
                'Additional Emails': email_additional,
                'Additional Phones': phone_additional,
                'Tags': 'DataSync Import'
            })

        output_df = pd.DataFrame(output_data)
        output_filename = f"validated_{timestamp}_{filename.replace('.xlsx', '.csv').replace('.xls', '.csv')}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        output_df.to_csv(output_path, index=False)

        logger.info(f"Validacao concluida: {output_path}")

        return send_file(
            output_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=output_filename
        )

    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        return jsonify({'error': str(e)}), 500

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
