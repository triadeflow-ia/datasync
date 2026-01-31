"""
Triadeflow DataSync API
Flask server para validacao de dados
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
import os
import random
import string
from datetime import datetime
import logging

from contact_validator import ContactDataValidator

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
    return jsonify({
        'service': 'Triadeflow DataSync API',
        'version': '1.0.0',
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
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
