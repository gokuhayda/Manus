# Manual de Instalação e Configuração - Assistente Virtual PoupaVet

## Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Git (opcional, para clonagem do repositório)

## Instalação

### 1. Preparação do Ambiente

```bash
# Criar diretório do projeto
mkdir poupavet-assistant
cd poupavet-assistant

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# No Linux/Mac:
source venv/bin/activate
# No Windows:
venv\Scripts\activate
```

### 2. Instalação das Dependências

```bash
# Instalar dependências
pip install flask flask-cors requests sqlalchemy

# Ou usar o arquivo requirements.txt (se disponível)
pip install -r requirements.txt
```

### 3. Estrutura de Arquivos

Criar a seguinte estrutura de diretórios:

```
poupavet-assistant/
├── src/
│   ├── models/
│   │   └── user.py
│   ├── routes/
│   │   ├── assistant.py
│   │   ├── integration.py
│   │   └── user.py
│   ├── static/
│   │   └── index.html
│   ├── database/
│   │   └── app.db
│   └── main.py
├── venv/
└── requirements.txt
```

### 4. Configuração

Criar arquivo `.env` na raiz do projeto:

```env
# URLs de integração
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/poupavet-agendamento
N8N_API_KEY=your-api-key-here

# Configurações do Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
```

## Execução

### Desenvolvimento

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar aplicação
python src/main.py
```

A aplicação estará disponível em: http://localhost:5001

### Produção

Para produção, recomenda-se usar Gunicorn:

```bash
# Instalar Gunicorn
pip install gunicorn

# Executar com Gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 src.main:app
```

## Configuração de Integrações

### n8n

1. Configure a URL do webhook no arquivo `.env`
2. Obtenha a chave de API do n8n
3. Configure o endpoint de recebimento no n8n

### WhatsApp

1. Configure a API do WhatsApp (Evolution API, Baileys, etc.)
2. Atualize as configurações de integração
3. Teste o envio de mensagens

## Testes

Para testar a aplicação:

1. Acesse http://localhost:5001
2. Teste diferentes tipos de mensagens:
   - "Quero agendar uma consulta"
   - "Quanto custa uma vacina?"
   - "Socorro! Emergência!"

## Troubleshooting

### Problemas Comuns

1. **Porta em uso**: Altere a porta no arquivo `main.py`
2. **Dependências**: Verifique se todas as dependências estão instaladas
3. **Permissões**: Verifique permissões de escrita no diretório

### Logs

Os logs são exibidos no console durante execução. Para produção, configure logging em arquivo.

## Manutenção

### Atualização da Base de Conhecimento

Edite o dicionário `KNOWLEDGE_BASE` em `src/routes/assistant.py`:

```python
KNOWLEDGE_BASE = {
    "servicos": [
        {"nome": "consulta", "preco": 85.00, "descricao": "Consulta veterinária geral"},
        # Adicionar novos serviços aqui
    ]
}
```

### Backup

Faça backup regular dos seguintes arquivos:
- Configurações (`.env`)
- Base de conhecimento (`assistant.py`)
- Banco de dados (`database/app.db`)

## Suporte

Para suporte técnico, consulte:
- Documentação técnica completa
- Logs de erro da aplicação
- Configurações de integração

