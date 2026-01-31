# Triadeflow DataSync

Sistema profissional de validacao e enriquecimento de dados para CRM.

## Features

- Validacao de Emails (regex, separacao de multiplos)
- Formatacao de Telefones BR (+55 DDD)
- Separacao de Contatos Multiplos
- API REST pronta para integracao
- Preparado para GoHighLevel e outros CRMs

## Deploy no Railway

1. Faca push deste repositorio para o GitHub
2. Acesse [Railway](https://railway.app)
3. Clique em **New Project** > **Deploy from GitHub repo**
4. Selecione o repositorio `triadeflow-ia/datasync`
5. O deploy sera automatico

### Variaveis de Ambiente (opcional)

```
DEFAULT_DDD=85
```

## API Endpoints

### GET /
Retorna informacoes do servico.

### GET /health
Health check para monitoramento.

### POST /validate
Valida e formata arquivo de contatos.

**Request:**
- `Content-Type: multipart/form-data`
- `file`: Arquivo .xlsx ou .csv

**Response:**
- Arquivo CSV validado e formatado

**Exemplo com curl:**
```bash
curl -X POST \
  -F "file=@contatos.xlsx" \
  https://seu-app.up.railway.app/validate \
  -o resultado.csv
```

## Formato de Saida

O CSV de saida contem as seguintes colunas:

| Coluna | Descricao |
|--------|-----------|
| Contact ID | ID unico gerado |
| Phone | Telefone principal formatado |
| Email | Email principal validado |
| First Name | Primeiro nome |
| Last Name | Sobrenome |
| Business Name | Nome da empresa |
| Opportunity ID | ID da oportunidade |
| Opportunity name | Nome da oportunidade |
| Pipeline | Pipeline (Sales Pipeline) |
| Stage | Estagio (New Lead) |
| Source | Origem (DataSync API) |
| Status | Status (Open) |
| Additional Emails | Emails adicionais |
| Additional Phones | Telefones adicionais |
| Tags | Tags (DataSync Import) |

## Estrutura do Projeto

```
datasync/
├── api_server.py         # Servidor Flask
├── contact_validator.py  # Validador de contatos
├── requirements.txt      # Dependencias Python
├── railway.json          # Configuracao Railway
└── README.md
```

## Desenvolvimento Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Executar servidor
python api_server.py

# Servidor disponivel em http://localhost:5000
```

---

**Desenvolvido por Triadeflow**
