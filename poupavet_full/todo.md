## Tarefas

### Fase 1: Análise Detalhada dos Requisitos e Planejamento da Arquitetura
- [ ] Analisar todos os requisitos fornecidos para o sistema completo.
- [ ] Definir a arquitetura geral do sistema (backend, frontend, integrações, banco de dados).
- [ ] Esboçar o fluxo de dados entre os componentes.

### Fase 2: Configuração do Ambiente de Desenvolvimento e Ferramentas (Docker, n8n, Python)
- [x] Configurar o ambiente Docker para o n8n.
- [x] Configurar o ambiente Python para o backend Flask.
- [x] Garantir que todas as dependências estejam instaladas.

### Fase 3: Desenvolvimento do Backend Core (Flask) e Integração com Supabase
- [x] Implementar a estrutura base do projeto Flask.
- [x] Configurar a conexão com o Supabase.
- [x] Criar modelos de dados no Flask que correspondam às tabelas do Supabase (anexos_bot, escala_medicos, mensagens_salvas, thread_id_track, urgencia, agenda_reservas, bloqueios_bot, erros_bot, lead_poupavet, mensagens_processadas).
- [x] Implementar operações CRUD básicas para as tabelas do Supabase.

### Fase 4: Implementação da Lógica de Integração com Google Sheets e Calendar
- [x] Desenvolver módulos para interação com a Google Sheets API (leitura e gravação).
- [x] Desenvolver módulos para interação com a Google Calendar API (criação de eventos, detecção de conflitos em múltiplas agendas).
- [x] Implementar a lógica de verificação de disponibilidade de horários.

### Fase 5: Desenvolvimento do Sistema de Precificação e Gerenciamento de Custos
- [x] Implementar a lógica para registro detalhado de interações (tipo, canal, cliente_id, dados_extras).
- [x] Desenvolver a lógica de cálculo de custos baseada nos modelos de cobrança (fixo, híbrido, por uso, por resultado, por canal).
- [x] Criar endpoints para consulta de métricas e projeções de custos.
- [x] Desenvolver a interface do dashboard de custos.

### Fase 6: Implementação do Chat Panel e Interface Web
- [x] Desenvolver a interface web principal do chat panel.
- [x] Implementar a comunicação frontend-backend para envio e recebimento de mensagens.
- [x] Criar o dashboard de atendimentos em tempo real.
- [x] Desenvolver a interface para monitoramento de conversas.
- [ ] Implementar a configuração de múltiplas agendas na interface.
- [ ] Criar o painel de configuração de integrações (OpenAI, Google Calendar, etc.).
- [ ] Desenvolver a visualização de métricas de atendimento.

### Fase 7: Configuração e Desenvolvimento do Fluxo n8n (Webhooks, Pré-processamento, OpenAI)
- [x] Criar o Webhook de entrada no n8n para receber mensagens.
- [x] Implementar o pré-processamento e normalização de dados no n8n.
- [x] Configurar a chamada à API da assistente Flask para processamento da mensagem.

### Fase 8: Integração com OpenAI Assistants (Threads, Runs, Mensagens)
- [ ] Implementar a lógica no n8n para criar Threads (POST /v1/threads).
- [ ] Desenvolver o envio de mensagens ao Assistant (POST /v1/threads/{thread_id}/messages).
- [ ] Configurar a execução do Assistant (POST /v1/threads/{thread_id}/runs).
- [ ] Implementar a espera pela resposta do Assistant com tentativas e backoff.
- [ ] Desenvolver a busca da mensagem gerada pelo Assistant (GET /threads/{thread_id}/messages).

### Fase 9: Integração com Z-API (WhatsApp) e Typebot (Web)
- [ ] Configurar o envio de mensagens via Z-API para WhatsApp.
- [ ] Configurar o envio de mensagens via Typebot para Web.
- [ ] Implementar o fallback e redirecionamento para atendimento humano.

### Fase 10: Testes Abrangentes e Validação do Sistema
- [ ] Realizar testes unitários para cada módulo e funcionalidade.
- [ ] Realizar testes de integração para o fluxo completo (WhatsApp/Web -> n8n -> Flask -> OpenAI/Google -> Flask -> n8n -> WhatsApp/Web).
- [ ] Validar a detecção de intenções e agendamentos.
- [ ] Testar o sistema de precificação e o dashboard de custos.
- [ ] Testar os casos de fallback e redirecionamento.

### Fase 11: Documentação Completa e Preparação dos Entregáveis
- [ ] Documentar a arquitetura do sistema e o fluxo de dados.
- [ ] Documentar o código do backend Flask e do frontend.
- [ ] Preparar o projeto .json do n8n com todos os nós configurados.
- [ ] Documentar as tabelas organizadas no Google Sheets.
- [ ] Documentar as contas conectadas ao Google Calendar e OpenAI.
- [ ] Preparar um relatório final com as melhorias e instruções de uso.


