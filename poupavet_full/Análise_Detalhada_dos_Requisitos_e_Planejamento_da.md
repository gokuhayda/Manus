
# Análise Detalhada dos Requisitos e Planejamento da Arquitetura

## 1. Visão Geral do Sistema

O objetivo principal é desenvolver um sistema de atendimento inteligente e automatizado para clínicas veterinárias, capaz de interagir com clientes via WhatsApp e Web. O sistema será modular, combinando um backend robusto em Flask, um orquestrador de fluxos (n8n), integração com serviços de IA (OpenAI Assistants), gerenciamento de dados (Google Sheets, Google Calendar, Supabase) e um sistema de precificação e custos.

## 2. Componentes Principais e Suas Funções

### 2.1. Frontend (Chat Panel e Dashboard)

*   **Chat Panel (Web e WhatsApp):** Interface para o cliente interagir com a assistente virtual. Deverá ser responsivo e intuitivo, com suporte a botões interativos e opções.
*   **Dashboard de Atendimentos:** Painel administrativo para monitoramento em tempo real de conversas, métricas de atendimento, configuração de agendas e integrações, e visualização de custos.

### 2.2. Backend (Flask Application)

*   **Lógica de Negócio:** Contém a inteligência central da assistente, incluindo processamento de mensagens, detecção de intenções (agendamento, consulta de preços, emergência, etc.), validação de dados e formatação de respostas.
*   **Integração com Supabase:** Gerenciamento de dados persistentes, como `anexos_bot`, `escala_medicos`, `mensagens_salvas`, `thread_id_track`, `urgencia`, `agenda_reservas`, `bloqueios_bot`, `erros_bot`, `lead_poupavet`, `mensagens_processadas`.
*   **Integração com Google Sheets:** Módulos para leitura e gravação de dados em múltiplas planilhas (ex: base de conhecimento, rastreamento de threads, leads).
*   **Integração com Google Calendar:** Módulos para criação de eventos, consulta de disponibilidade e detecção de conflitos em múltiplas agendas (salas).
*   **Sistema de Precificação e Custos:** Lógica para registrar interações, calcular custos com base em diferentes modelos de cobrança (fixo, híbrido, por uso, por resultado, por canal) e fornecer dados para o dashboard.

### 2.3. Orquestrador de Fluxos (n8n)

*   **Webhook de Entrada:** Ponto de entrada para mensagens do WhatsApp (via Z-API) e Web (via Typebot).
*   **Pré-processamento e Normalização:** Limpeza e organização dos dados de entrada (IdConversa, Mensagem, inicio_execucao, canal, etc.).
*   **Chamada à Assistente Flask:** Envio da mensagem pré-processada para o backend Flask para processamento da lógica de negócio.
*   **Integração com OpenAI Assistants:** Gerenciamento de Threads, envio de mensagens, execução de Runs e recuperação de respostas do Assistant.
*   **Armazenamento e Rastreamento:** Verificação e gravação de `thread_id` e status em planilhas ou Supabase.
*   **Detecção de Intenção e Agendamento:** Lógica para formatar datas/horas, consultar múltiplas agendas do Google Calendar, contar conflitos e decidir o agendamento.
*   **Criação de Evento no Google Calendar:** Utilização da API do Google Calendar para criar eventos.
*   **Fallback e Redirecionamento:** Lógica para redirecionar mensagens para atendimento humano em caso de erros, respostas vazias ou intenção específica de redirecionamento.
*   **Resposta ao Usuário:** Envio da mensagem final formatada de volta ao usuário via Z-API ou Typebot.

### 2.4. Serviços Externos

*   **OpenAI Assistants API:** Para processamento de linguagem natural, interpretação de intenções e geração de respostas inteligentes.
*   **Google Calendar API:** Para gerenciamento de agendas e agendamentos.
*   **Google Sheets API:** Para armazenamento e consulta de dados.
*   **Z-API (WhatsApp):** Para comunicação com usuários via WhatsApp.
*   **Typebot (Chat Web):** Para comunicação com usuários via interface web.
*   **Supabase:** Banco de dados para persistência de dados da aplicação.

## 3. Fluxo de Dados e Interações

1.  **Início da Conversa:** O usuário envia uma mensagem via WhatsApp (Z-API) ou Web (Typebot).
2.  **Webhook n8n:** O n8n recebe a mensagem através de um webhook.
3.  **Pré-processamento n8n:** O n8n normaliza os dados da mensagem.
4.  **Chamada ao Backend Flask:** O n8n envia a mensagem pré-processada para o endpoint `/api/assistant/chat` do backend Flask.
5.  **Processamento Flask:**
    *   A assistente Flask processa a mensagem, detecta a intenção e extrai entidades.
    *   Se for agendamento, interage com Google Calendar para verificar disponibilidade e agendar.
    *   Se for consulta de preço, consulta a base de conhecimento (Google Sheets ou Supabase).
    *   Registra a interação no sistema de precificação (Supabase).
    *   Gera a resposta formatada (texto, botões, JSON de agendamento).
6.  **Resposta do Flask ao n8n:** O backend Flask retorna a resposta processada para o n8n.
7.  **Pós-processamento n8n:** O n8n recebe a resposta do Flask.
    *   Se a intenção for agendamento, o n8n cria o evento no Google Calendar.
    *   Se houver necessidade de redirecionamento, o n8n envia a mensagem para o grupo de atendimento humano no WhatsApp.
    *   Atualiza o status da thread no Supabase.
8.  **Resposta ao Usuário:** O n8n envia a mensagem final de volta ao usuário via Z-API ou Typebot.

## 4. Estrutura de Dados (Supabase)

As tabelas no Supabase serão cruciais para a persistência de dados. As tabelas identificadas são:

*   `anexos_bot`
*   `escala_medicos`
*   `mensagens_salvas`
*   `thread_id_track`
*   `urgencia`
*   `agenda_reservas`
*   `bloqueios_bot`
*   `erros_bot`
*   `lead_poupavet`
*   `mensagens_processadas`

Será necessário mapear os campos de cada tabela e definir as relações entre elas.

## 5. Considerações de Segurança e Escalabilidade

*   **Autenticação e Autorização:** Implementar mecanismos de segurança para acesso às APIs e ao dashboard.
*   **Rate Limiting:** Aplicar limites de requisição para evitar abusos e sobrecarga.
*   **Logging e Monitoramento:** Implementar logging detalhado para depuração e monitoramento de performance.
*   **Tratamento de Erros:** Mecanismos robustos de tratamento de erros e fallback para garantir a resiliência do sistema.
*   **Ambiente de Produção:** Utilizar Gunicorn e Nginx para servir a aplicação Flask em produção, e Docker para o n8n.

## 6. Próximos Passos

Com esta análise detalhada, o próximo passo será configurar o ambiente de desenvolvimento e as ferramentas necessárias para iniciar a implementação.


## 7. Análise do Template de Negócio com Agentes de IA

Após analisar o template JSON fornecido, identifiquei várias funcionalidades avançadas que podem ser incorporadas ao projeto PoupaVet:

### 7.1. Funcionalidades Identificadas no Template

#### **Sistema de Agentes IA com Memória Persistente**
- **Postgres Chat Memory:** O template utiliza memória de chat persistente com PostgreSQL, permitindo que a IA mantenha contexto de conversas anteriores
- **Sessões por Telefone:** Cada conversa é identificada pelo número de telefone, mantendo histórico personalizado
- **Context Window:** Configuração de janela de contexto (20 mensagens) para otimizar performance

#### **Divisão Inteligente de Mensagens**
- **Parser Chain:** Sistema sofisticado para dividir mensagens longas em partes menores (300-500 caracteres)
- **Formatação Automática:** Conversão de formatação markdown para WhatsApp (*negrito*, ~tachado~, _itálico_)
- **Tratamento de Links:** Formatação especial para links usando backticks

#### **Sistema de Detecção e Redirecionamento**
- **Switch Inteligente:** Lógica condicional para detectar códigos específicos (ex: "251213") e redirecionar para atendimento humano
- **Notificação de Leads:** Sistema automático para avisar novos leads em grupos do WhatsApp
- **Fallback Robusto:** Múltiplas camadas de fallback para garantir que nenhuma mensagem seja perdida

#### **Integração com Supabase Avançada**
- **Vector Store:** Utilização do Supabase como vector store para embeddings e busca semântica
- **Gestão de Chats:** Sistema completo de cadastro e atualização de chats
- **Rastreamento de Leads:** Monitoramento automático de novos contatos

#### **Evolution API para WhatsApp**
- **Múltiplas Instâncias:** Suporte a diferentes instâncias do WhatsApp
- **Delays Inteligentes:** Configuração de delays entre mensagens para simular digitação humana
- **Opções Avançadas:** Controle de preview de links e outras configurações

### 7.2. Melhorias Propostas para o Projeto PoupaVet

#### **1. Sistema de Memória Persistente**
```python
# Implementar em src/routes/memory.py
class ChatMemoryManager:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def get_conversation_history(self, phone_number, limit=20):
        """Recupera histórico de conversas"""
        pass
    
    def save_message(self, phone_number, message, response):
        """Salva mensagem e resposta"""
        pass
    
    def clear_old_messages(self, phone_number, keep_last=20):
        """Limpa mensagens antigas mantendo apenas as últimas"""
        pass
```

#### **2. Parser de Mensagens Inteligente**
```python
# Implementar em src/routes/message_parser.py
class MessageParser:
    def split_long_message(self, message, max_length=500):
        """Divide mensagens longas em partes menores"""
        pass
    
    def format_for_whatsapp(self, message):
        """Converte formatação para WhatsApp"""
        # ** para *
        # Links para `link`
        # Etc.
        pass
    
    def detect_special_codes(self, message):
        """Detecta códigos especiais para redirecionamento"""
        pass
```

#### **3. Sistema de Redirecionamento Avançado**
```python
# Implementar em src/routes/redirect.py
class RedirectManager:
    def should_redirect_to_human(self, message, context):
        """Determina se deve redirecionar para humano"""
        pass
    
    def notify_new_lead(self, phone_number, name, case_description):
        """Notifica novo lead no grupo"""
        pass
    
    def handle_emergency_case(self, phone_number, emergency_details):
        """Trata casos de emergência"""
        pass
```

#### **4. Integração com Evolution API**
```python
# Implementar em src/routes/whatsapp.py
class WhatsAppManager:
    def __init__(self, evolution_api_config):
        self.config = evolution_api_config
    
    def send_message(self, phone_number, message, delay=4200):
        """Envia mensagem com delay configurável"""
        pass
    
    def send_to_group(self, group_id, message):
        """Envia mensagem para grupo"""
        pass
    
    def format_lead_notification(self, phone_number, name, case):
        """Formata notificação de lead"""
        pass
```

#### **5. Vector Store para Busca Semântica**
```python
# Implementar em src/routes/vector_search.py
class VectorSearchManager:
    def __init__(self, supabase_client, openai_client):
        self.supabase = supabase_client
        self.openai = openai_client
    
    def create_embedding(self, text):
        """Cria embedding do texto"""
        pass
    
    def search_similar_documents(self, query, limit=5):
        """Busca documentos similares"""
        pass
    
    def add_document(self, content, metadata):
        """Adiciona documento ao vector store"""
        pass
```

### 7.3. Estrutura de Dados Aprimorada

#### **Tabelas Adicionais no Supabase**
```sql
-- Tabela para histórico de conversas
CREATE TABLE conversation_history (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    session_id UUID,
    context_data JSONB
);

-- Tabela para vector store
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela para redirecionamentos
CREATE TABLE redirections (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    reason VARCHAR(100) NOT NULL,
    context TEXT,
    handled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 7.4. Fluxo de Trabalho Aprimorado

1. **Recepção da Mensagem**
   - Webhook recebe mensagem
   - Verifica se é novo chat (cadastra no Supabase)
   - Recupera histórico de conversas

2. **Processamento Inteligente**
   - Analisa contexto da conversa
   - Detecta códigos especiais
   - Aplica regras de redirecionamento

3. **Geração de Resposta**
   - Consulta vector store para informações relevantes
   - Gera resposta usando OpenAI com contexto
   - Aplica parser para dividir mensagens longas

4. **Envio e Monitoramento**
   - Envia mensagens com delays apropriados
   - Salva interação no histórico
   - Monitora para notificações de lead

### 7.5. Configurações Avançadas

#### **Arquivo de Configuração Expandido**
```env
# OpenAI
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small

# Evolution API
EVOLUTION_API_URL=https://your-evolution-api.com
EVOLUTION_API_KEY=your-evolution-key
EVOLUTION_INSTANCE=your-instance-name

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
SUPABASE_SERVICE_KEY=your-service-key

# Configurações de Chat
CONTEXT_WINDOW_SIZE=20
MESSAGE_MAX_LENGTH=500
TYPING_DELAY=4200
LEAD_GROUP_ID=your-group-id

# Códigos Especiais
HUMAN_REDIRECT_CODE=251213
EMERGENCY_CODE=911
VIP_CODE=999
```

Esta análise do template revela um sistema muito mais sofisticado do que inicialmente planejado, com funcionalidades avançadas de IA, memória persistente, e integração robusta com WhatsApp. Essas melhorias elevarão significativamente a qualidade e eficiência do sistema PoupaVet.

