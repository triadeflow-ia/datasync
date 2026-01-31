#!/bin/bash
# Triadeflow DataSync - Setup Automático
# Execute: bash setup.sh

echo "🚀 Triadeflow DataSync - Setup Automático"
echo "=========================================="
echo ""

# Criar diretório do projeto
mkdir -p triadeflow-datasync
cd triadeflow-datasync

echo "📁 Criando estrutura do projeto..."

# ============================================================================
# 1. CRIAR .gitignore
# ============================================================================
cat > .gitignore << 'GITIGNORE_EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.venv/
venv/
ENV/

# Environments
.env
.envrc

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
.cache/
*.csv
*.xlsx
*.xls
/tmp/
uploads/
outputs/

# Logs
*.log
GITIGNORE_EOF

# ============================================================================
# 2. CRIAR requirements.txt
# ============================================================================
cat > requirements.txt << 'REQUIREMENTS_EOF'
# Core dependencies
pandas>=2.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
openpyxl>=3.1.0

# Web framework
flask>=3.0.0
flask-cors>=4.0.0
flask-limiter>=3.5.0

# Production server
gunicorn>=21.2.0

# Environment variables
python-dotenv>=1.0.0
REQUIREMENTS_EOF

# ============================================================================
# 3. CRIAR railway.json
# ============================================================================
cat > railway.json << 'RAILWAY_EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "startCommand": "gunicorn --bind 0.0.0.0:$PORT --timeout 300 --workers 2 api_server:app"
  }
}
RAILWAY_EOF

# ============================================================================
# 4. CRIAR contact_validator.py
# ============================================================================
cat > contact_validator.py << 'VALIDATOR_EOF'
"""
Contact Data Validator
Valida e formata emails e telefones brasileiros
"""

import pandas as pd
import re
from typing import List, Tuple

class ContactDataValidator:
    def __init__(self, default_ddd='85'):
        self.default_ddd = default_ddd
        self.validation_report = {
            'total_rows': 0,
            'valid_emails': 0,
            'invalid_emails': 0,
            'valid_phones': 0,
            'invalid_phones': 0,
            'phones_with_ddd_added': 0,
            'errors': []
        }
    
    def validate_and_format_email(self, email_str: str) -> Tuple[str, str, List[str]]:
        if pd.isna(email_str) or str(email_str).strip() == '':
            return '', '', []
        
        email_str = str(email_str).lower().strip()
        potential_emails = re.split(r'[;/,\s]+', email_str)
        
        valid_emails = []
        invalid_emails = []
        
        for email in potential_emails:
            email = email.strip()
            if not email or '@' not in email:
                continue
            
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(pattern, email):
                valid_emails.append(email)
                self.validation_report['valid_emails'] += 1
            else:
                invalid_emails.append(email)
                self.validation_report['invalid_emails'] += 1
        
        if len(valid_emails) == 0:
            return '', '', invalid_emails
        elif len(valid_emails) == 1:
            return valid_emails[0], '', invalid_emails
        else:
            return valid_emails[0], ', '.join(valid_emails[1:]), invalid_emails
    
    def parse_brazilian_phone(self, phone_str: str) -> List[str]:
        if pd.isna(phone_str) or str(phone_str).strip() == '':
            return []
        
        phone_str = str(phone_str).strip()
        digits_only = re.sub(r'\D', '', phone_str)
        
        if len(digits_only) == 8:
            digits_only = self.default_ddd + digits_only
            self.validation_report['phones_with_ddd_added'] += 1
        
        if len(digits_only) == 9:
            digits_only = self.default_ddd + digits_only
            self.validation_report['phones_with_ddd_added'] += 1
        
        return [digits_only]
    
    def format_phone(self, phone_digits: str) -> str:
        if len(phone_digits) == 11:
            return f"+55 {phone_digits[:2]} {phone_digits[2:7]}-{phone_digits[7:]}"
        elif len(phone_digits) == 10:
            return f"+55 {phone_digits[:2]} {phone_digits[2:6]}-{phone_digits[6:]}"
        else:
            return f"+55 {self.default_ddd} {phone_digits}"
    
    def validate_and_format_phones(self, phone_str: str) -> Tuple[str, str]:
        phone_numbers = self.parse_brazilian_phone(phone_str)
        
        valid_phones = []
        
        for phone in phone_numbers:
            formatted = self.format_phone(phone)
            valid_phones.append(formatted)
            self.validation_report['valid_phones'] += 1
        
        if len(valid_phones) == 0:
            return '', ''
        elif len(valid_phones) == 1:
            return valid_phones[0], ''
        else:
            return valid_phones[0], ', '.join(valid_phones[1:])
VALIDATOR_EOF

# ============================================================================
# 5. CRIAR api_server.py
# ============================================================================
cat > api_server.py << 'API_EOF'
"""
Triadeflow DataSync API
Flask server para validação de dados
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
    logger.info("Iniciando validação")
    
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
        
        logger.info(f"Validação concluída: {output_path}")
        
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
API_EOF

# ============================================================================
# 6. CRIAR README.md
# ============================================================================
cat > README.md << 'README_EOF'
# 🚀 Triadeflow DataSync

Sistema profissional de validação e enriquecimento de dados para CRM.

## ✨ Features

- ✅ Validação de Emails
- ✅ Formatação de Telefones BR (+55)
- ✅ Separação de Contatos Múltiplos
- ✅ API REST

## 🚀 Deploy no Railway

1. Push para GitHub
2. Railway → New Project → Deploy from GitHub
3. Selecione este repositório
4. Deploy automático!

## 📡 API

**POST /validate**
- Upload arquivo .xlsx ou .csv
- Retorna CSV validado

**Exemplo:**
```bash
curl -F "file=@contatos.xlsx" \
     https://seu-app.up.railway.app/validate \
     -o resultado.csv
```

## 🔧 Variáveis de Ambiente

```
DEFAULT_DDD=85
ENV=production
```

**Desenvolvido por Triadeflow** 🚀
README_EOF

echo ""
echo "✅ Projeto criado com sucesso!"
echo ""
echo "📂 Estrutura criada:"
ls -lh
echo ""
echo "🚀 Próximos passos:"
echo ""
echo "1. Inicialize o Git:"
echo "   git init"
echo ""
echo "2. Adicione o remote:"
echo "   git remote add origin https://github.com/triadeflow-ia/datasync.git"
echo ""
echo "3. Faça o commit:"
echo "   git add ."
echo "   git commit -m 'Initial commit - Triadeflow DataSync'"
echo ""
echo "4. Push para GitHub:"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "5. Deploy no Railway:"
echo "   https://railway.app/dashboard"
echo ""
echo "=========================================="
echo "✨ Setup completo!"
