from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import re
import openai
import os
from src.routes.supabase_integration import supabase

assistant_bp = Blueprint("assistant", __name__)

# Configuração OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Base de conhecimento expandida
KNOWLEDGE_BASE = {
    "servicos": [
        {"nome": "consulta", "preco": 85.00, "descricao": "Consulta veterinária geral"},
        {"nome": "vacina", "preco": 45.00, "descricao": "Vacinação preventiva"},
        {"nome": "castração", "preco": 280.00, "descricao": "Cirurgia de castração"},
        {"nome": "exame de sangue", "preco": 120.00, "descricao": "Hemograma completo"},
        {"nome": "ultrassom", "preco": 150.00, "descricao": "Ultrassonografia veterinária"},
        {"nome": "raio-x", "preco": 80.00, "descricao": "Radiografia veterinária"}
    ],
    "medicos": [
        {"nome": "Dr. Ana Silva", "especialidade": "Clínica Geral", "disponibilidade": "Segunda a Sexta"},
        {"nome": "Dr. Carlos Santos", "especialidade": "Cirurgia", "disponibilidade": "Terça e Quinta"},
        {"nome": "Dra. Maria Oliveira", "especialidade": "Dermatologia", "disponibilidade": "Segunda, Quarta e Sexta"}
    ],
    "horarios": ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"],
    "especies": ["cão", "gato", "ave", "roedor", "réptil"]
}

class MessageParser:
    """Classe para parsing e formatação de mensagens"""
    
    @staticmethod
    def split_long_message(message, max_length=500):
        """Divide mensagens longas em partes menores"""
        if len(message) <= max_length:
            return [message]
        
        # Divide por parágrafos primeiro
        paragraphs = message.split("\n\n")
        messages = []
        current_message = ""
        
        for paragraph in paragraphs:
            if len(current_message + paragraph) <= max_length:
                current_message += paragraph + "\n\n"
            else:
                if current_message:
                    messages.append(current_message.strip())
                    current_message = paragraph + "\n\n"
                else:
                    # Parágrafo muito longo, divide por frases
                    sentences = paragraph.split(". ")
                    for sentence in sentences:
                        if len(current_message + sentence) <= max_length:
                            current_message += sentence + ". "
                        else:
                            if current_message:
                                messages.append(current_message.strip())
                            current_message = sentence + ". "
        
        if current_message:
            messages.append(current_message.strip())
        
        return messages
    
    @staticmethod
    def format_for_whatsapp(message):
        """Converte formatação para WhatsApp"""
        # Converter ** para *
        message = re.sub(r"\*\*(.*?)\*\*", r"*\1*", message)
        
        # Converter links para formato com backticks
        message = re.sub(r"https?://[^\s]+", r"`\g<0>`", message)
        
        # Remover formatação desnecessária
        message = message.replace("**", "*")
        
        return message
    
    @staticmethod
    def detect_special_codes(message):
        """Detecta códigos especiais para redirecionamento"""
        special_codes = {
            "251213": "human_redirect",
            "911": "emergency",
            "999": "vip"
        }
        
        for code, action in special_codes.items():
            if code in message:
                return action
        
        return None

class ChatMemoryManager:
    """Gerenciador de memória de chat"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def get_conversation_history(self, phone_number, limit=20):
        """Recupera histórico de conversas"""
        try:
            if self.supabase:
                result = self.supabase.table("conversation_history")\
                    .select("*")\
                    .eq("phone_number", phone_number)\
                    .order("timestamp", desc=True)\
                    .limit(limit)\
                    .execute()
                return result.data
        except Exception as e:
            print(f"Erro ao recuperar histórico: {e}")
        return []
    
    def save_message(self, phone_number, message, response, context_data=None):
        """Salva mensagem e resposta"""
        try:
            if self.supabase:
                data = {
                    "phone_number": phone_number,
                    "message": message,
                    "response": response,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_data": context_data or {}
                }
                self.supabase.table("conversation_history").insert(data).execute()
        except Exception as e:
            print(f"Erro ao salvar mensagem: {e}")

    def get_thread_id(self, phone_number):
        """Recupera o thread_id do Supabase"""
        try:
            if self.supabase:
                result = self.supabase.table("thread_id_track")\
                    .select("thread_id")\
                    .eq("phone_number", phone_number)\
                    .single()\
                    .execute()
                return result.data["thread_id"]
        except Exception as e:
            print(f"Erro ao recuperar thread_id: {e}")
        return None

    def save_thread_id(self, phone_number, thread_id):
        """Salva o thread_id no Supabase"""
        try:
            if self.supabase:
                data = {
                    "phone_number": phone_number,
                    "thread_id": thread_id,
                    "created_at": datetime.utcnow().isoformat()
                }
                self.supabase.table("thread_id_track").insert(data).execute()
        except Exception as e:
            print(f"Erro ao salvar thread_id: {e}")

class AssistentePoupaVet:
    """Assistente virtual principal da PoupaVet"""
    
    def __init__(self):
        self.knowledge_base = KNOWLEDGE_BASE
        self.parser = MessageParser()
        self.memory_manager = ChatMemoryManager(supabase)
        self.client = openai.OpenAI(api_key=openai.api_key)
        self.assistant_id = ASSISTANT_ID

    def _get_or_create_thread(self, phone_number):
        thread_id = self.memory_manager.get_thread_id(phone_number)
        if thread_id:
            return self.client.beta.threads.retrieve(thread_id)
        else:
            thread = self.client.beta.threads.create()
            self.memory_manager.save_thread_id(phone_number, thread.id)
            return thread

    def _run_assistant(self, thread_id, message):
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id
        )

        while run.status in ["queued", "in_progress", "cancelling"]:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            # Adicionar um pequeno delay para evitar polling excessivo
            # time.sleep(0.5) # Não pode usar time.sleep aqui no ambiente do agente

        if run.status == "completed":
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id
            )
            # Retorna a última mensagem do assistente
            for msg in messages.data:
                if msg.role == "assistant":
                    return msg.content[0].text.value
        return "Desculpe, não consegui processar sua solicitação no momento."

    def processar_mensagem(self, mensagem, phone_number, contexto=None):
        """Processa mensagem principal"""
        try:
            # Detectar códigos especiais
            special_code = self.parser.detect_special_codes(mensagem)
            if special_code == "human_redirect":
                return self._gerar_redirecionamento_humano()
            elif special_code == "emergency":
                return self._processar_emergencia(mensagem)
            
            # Obter ou criar thread do OpenAI
            thread = self._get_or_create_thread(phone_number)

            # Executar o assistente OpenAI
            assistant_response_text = self._run_assistant(thread.id, mensagem)

            # A partir daqui, você pode tentar parsear a resposta do assistente
            # para extrair intenções e dados estruturados, ou deixar o assistente
            # retornar o JSON diretamente se ele for configurado para isso.
            # Por simplicidade, vamos assumir que o assistente retorna texto.

            # Para o agendamento, ainda podemos usar a lógica existente
            # se o assistente retornar uma intenção clara de agendamento.
            # Ou, podemos refatorar para que o assistente retorne um JSON
            # que a gente possa usar diretamente.

            # Por enquanto, vamos retornar a resposta do assistente diretamente
            # e você pode refinar a lógica de parsing ou de tool_use do assistente.

            return {
                "message": assistant_response_text,
                "json_response": {
                    "intencao": "resposta_openai",
                    "texto_original": mensagem,
                    "resposta_assistente": assistant_response_text
                }
            }

        except Exception as e:
            print(f"Erro ao processar mensagem com OpenAI: {e}")
            return self._gerar_redirecionamento_humano()
    
    def _detectar_intencao(self, mensagem):
        """Detecta a intenção da mensagem"""
        # Esta função pode ser removida ou simplificada se o OpenAI Assistant
        # for responsável por toda a detecção de intenção e extração de dados.
        # Por enquanto, mantemos para compatibilidade.
        mensagem_lower = mensagem.lower()
        
        # Palavras-chave para agendamento
        palavras_agendamento = [
            "agendar", "marcar", "consulta", "horário", "disponibilidade",
            "quero", "preciso", "gostaria", "pode", "agenda"
        ]
        
        # Palavras-chave para preços
        palavras_preco = [
            "preço", "valor", "custa", "quanto", "custo", 
            "tabela", "valores", "preços"
        ]
        
        # Palavras-chave para emergência
        palavras_emergencia = [
            "emergência", "urgente", "socorro", "ajuda", "grave",
            "sangue", "dor", "convulsão", "vômito", "diarreia"
        ]
        
        # Palavras-chave para médicos
        palavras_medicos = [
            "médico", "veterinário", "doutor", "doutora", 
            "profissional", "especialista"
        ]
        
        if any(palavra in mensagem_lower for palavra in palavras_emergencia):
            return "emergencia"
        elif any(palavra in mensagem_lower for palavra in palavras_agendamento):
            return "agendamento"
        elif any(palavra in mensagem_lower for palavra in palavras_preco):
            return "consulta_preco"
        elif any(palavra in mensagem_lower for palavra in palavras_medicos):
            return "medicos"
        else:
            return "outro"
    
    def _processar_agendamento(self, mensagem):
        """Processa solicitação de agendamento"""
        # Esta função pode ser chamada pelo OpenAI Assistant via Tool Use
        # ou a lógica pode ser incorporada no Assistant diretamente.
        # Por enquanto, mantemos para compatibilidade.
        # Extrair dados da mensagem
        dados = self._extrair_dados_agendamento(mensagem)
        
        # Verificar se tem dados suficientes
        campos_obrigatorios = ["tutor", "pet", "especie", "servico", "data", "hora"]
        dados_faltantes = [campo for campo in campos_obrigatorios if not dados.get(campo)]
        
        if dados_faltantes:
            return self._solicitar_dados_faltantes(dados_faltantes, dados)
        
        # Gerar JSON de agendamento
        return self._gerar_json_agendamento(dados)
    
    def _extrair_dados_agendamento(self, mensagem):
        """Extrai dados de agendamento da mensagem"""
        dados = {}
        
        # Padrões regex para extração
        padroes = {
            "pet": r"(?:meu|minha|do|da)\s+(\w+)",
            "data": r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|hoje|amanhã|segunda|terça|quarta|quinta|sexta|sábado|domingo)",
            "hora": r"(\d{1,2}:\d{2}|\d{1,2}h)",
            "servico": r"(consulta|vacina|castração|exame|ultrassom|raio-x)"
        }
        
        for campo, padrao in padroes.items():
            match = re.search(padrao, mensagem.lower())
            if match:
                dados[campo] = match.group(1)
        
        # Detectar espécie baseada em palavras-chave
        especies_palavras = {
            "cão": ["cão", "cachorro", "dog", "canino"],
            "gato": ["gato", "felino", "cat"],
            "ave": ["ave", "pássaro", "bird"],
            "roedor": ["hamster", "coelho", "roedor"],
            "réptil": ["réptil", "iguana", "cobra"]
        }
        
        for especie, palavras in especies_palavras.items():
            if any(palavra in mensagem.lower() for palavra in palavras):
                dados["especie"] = especie
                break
        
        return dados
    
    def _solicitar_dados_faltantes(self, dados_faltantes, dados_existentes):
        """Solicita dados faltantes para agendamento"""
        if "tutor" in dados_faltantes:
            return {
                "message": "Para finalizar o agendamento, preciso do seu nome completo. Como você se chama? 😊",
                "json_response": {
                    "intencao": "agendamento_incompleto",
                    "dados_coletados": dados_existentes,
                    "proximo_campo": "tutor"
                }
            }
        elif "pet" in dados_faltantes:
            return {
                "message": "Qual é o nome do seu pet? 🐾",
                "json_response": {
                    "intencao": "agendamento_incompleto",
                    "dados_coletados": dados_existentes,
                    "proximo_campo": "pet"
                }
            }
        elif "especie" in dados_faltantes:
            return {
                "message": "Seu pet é um cão, gato ou outro animal? 🐕🐱",
                "optionList": {
                    "title": "Escolha a espécie",
                    "buttonLabel": "Selecionar espécie",
                    "options": [
                        {"id": "1", "title": "Cão", "description": "Cachorro"},
                        {"id": "2", "title": "Gato", "description": "Felino"},
                        {"id": "3", "title": "Ave", "description": "Pássaro"},
                        {"id": "4", "title": "Outro", "description": "Outros animais"}
                    ]
                }
            }
        elif "servico" in dados_faltantes:
            return {
                "message": "Que tipo de atendimento você precisa? 🏥",
                "optionList": {
                    "title": "Escolha o serviço",
                    "buttonLabel": "Selecionar serviço",
                    "options": [
                        {"id": str(i+1), "title": servico["nome"].title(), "description": f"R$ {servico["preco"]:.2f}"}
                        for i, servico in enumerate(self.knowledge_base["servicos"])
                    ]
                }
            }
        elif "data" in dados_faltantes:
            return {
                "message": "Para qual data você gostaria de agendar? 📅",
                "json_response": {
                    "intencao": "agendamento_incompleto",
                    "dados_coletados": dados_existentes,
                    "proximo_campo": "data"
                }
            }
        elif "hora" in dados_faltantes:
            return {
                "message": "Qual horário prefere? Temos disponibilidade nos seguintes horários: ⏰",
                "optionList": {
                    "title": "Escolha o horário",
                    "buttonLabel": "Selecionar horário",
                    "options": [
                        {"id": str(i+1), "title": horario, "description": "Disponível"}
                        for i, horario in enumerate(self.knowledge_base["horarios"])
                    ]
                }
            }
        else:
            return self._gerar_redirecionamento_humano()
    
    def _gerar_json_agendamento(self, dados):
        """Gera o JSON final de agendamento"""
        json_agendamento = {
            "intencao": "agendamento",
            "tutor": dados["tutor"],
            "pet": dados["pet"],
            "especie": dados["especie"],
            "servico": dados["servico"],
            "data": dados["data"],
            "hora": dados["hora"]
        }
        
        # Adicionar médico padrão se não especificado
        if dados.get("medico"):
            json_agendamento["medico"] = dados["medico"]
        else:
            json_agendamento["medico"] = "Dr. Ana Silva"
        
        if dados.get("especialidade"):
            json_agendamento["especialidade"] = dados["especialidade"]
        
        # Gerar detalhamento
        detalhamento = f"✅ {dados["servico"].title()} do {dados["pet"]} confirmado para {dados["data"]} às {dados["hora"]} 🐾💖"
        json_agendamento["detalhamento"] = detalhamento
        
        return {
            "message": f"Perfeito! Agendamento realizado com sucesso! 🎉\n\n{detalhamento}\n\nEm breve você receberá uma confirmação. Até logo! 😊",
            "json_response": json_agendamento
        }
    
    def _processar_consulta_preco(self, mensagem):
        """Processa consulta sobre preços"""
        # Buscar serviço específico na mensagem
        for servico in self.knowledge_base["servicos"]:
            if servico["nome"] in mensagem.lower():
                return {
                    "message": f"A {servico["nome"]} na PoupaVet custa R$ {servico["preco"]:.2f}. {servico["descricao"]}. Posso ajudar com o agendamento? 🐾"
                }
        
        # Se não encontrou serviço específico, mostrar opções
        return {
            "message": "Sobre qual serviço você gostaria de saber o valor? 💰",
            "optionList": {
                "title": "Dúvidas de valores?",
                "buttonLabel": "Selecione o tipo",
                "options": [
                    {"id": "1", "title": "Consulta", "description": "Valores e modalidades"},
                    {"id": "2", "title": "Vacinas", "description": "Tabela atualizada"},
                    {"id": "3", "title": "Exames", "description": "Principais exames"},
                    {"id": "4", "title": "Cirurgias", "description": "Custos estimados por tipo"}
                ]
            }
        }
    
    def _processar_emergencia(self, mensagem):
        """Processa casos de emergência"""
        return {
            "message": "🚨 EMERGÊNCIA DETECTADA! 🚨\n\nEstou redirecionando você imediatamente para nossa equipe de plantão. Mantenha a calma e aguarde o contato.\n\n📞 Para casos urgentes, ligue: (12) 99999-9999",
            "json_response": {
                "intencao": "emergencia",
                "redirecionar": "humano",
                "prioridade": "alta",
                "contexto": mensagem
            }
        }
    
    def _gerar_redirecionamento_humano(self):
        """Gera resposta para redirecionamento humano"""
        return {
            "message": "No momento, não consigo te ajudar com essa solicitação. Por favor, aguarde que um de nossos atendentes entrará em contato em breve. 🧑‍💻",
            "json_response": {
                "intencao": "redirecionamento_humano"
            }
        }

    def _listar_medicos(self):
        """Lista os médicos disponíveis e suas especialidades"""
        medicos_info = "Nossos médicos disponíveis são:\n\n"
        for medico in self.knowledge_base["medicos"]:
            medicos_info += f"- {medico["nome"]} ({medico["especialidade"]}) - Disponibilidade: {medico["disponibilidade"]}\n"
        medicos_info += "\nPosso ajudar a agendar uma consulta com algum deles?"
        
        return {
            "message": medicos_info,
            "json_response": {
                "intencao": "listar_medicos"
            }
        }

assistente = AssistentePoupaVet()

@assistant_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensagem = data.get("mensagem")
    phone_number = data.get("phone_number")
    contexto = data.get("contexto")

    if not mensagem or not phone_number:
        return jsonify({"error": "Mensagem e phone_number são obrigatórios"}), 400

    response = assistente.processar_mensagem(mensagem, phone_number, contexto)
    
    # Salvar a interação no histórico
    assistente.memory_manager.save_message(phone_number, mensagem, response.get("message"), contexto)

    return jsonify(response)


