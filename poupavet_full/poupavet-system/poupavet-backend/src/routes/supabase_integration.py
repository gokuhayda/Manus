from flask import Blueprint, request, jsonify
from supabase import create_client, Client
import os
from datetime import datetime

supabase_bp = Blueprint('supabase', __name__)

# Configuração do Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'your-anon-key')

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Erro ao conectar com Supabase: {e}")
    supabase = None

@supabase_bp.route('/health', methods=['GET'])
def health_check():
    """Verifica a saúde da conexão com Supabase"""
    if supabase is None:
        return jsonify({"status": "error", "message": "Supabase não configurado"}), 500
    
    try:
        # Teste simples de conexão
        result = supabase.table('thread_id_track').select('*').limit(1).execute()
        return jsonify({"status": "ok", "message": "Conexão com Supabase funcionando"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@supabase_bp.route('/thread_id_track', methods=['GET', 'POST'])
def thread_id_track():
    """Gerencia a tabela thread_id_track"""
    if supabase is None:
        return jsonify({"error": "Supabase não configurado"}), 500
    
    try:
        if request.method == 'GET':
            # Buscar threads
            id_conversa = request.args.get('id_conversa')
            if id_conversa:
                result = supabase.table('thread_id_track').select('*').eq('id_conversa', id_conversa).execute()
            else:
                result = supabase.table('thread_id_track').select('*').execute()
            return jsonify(result.data)
        
        elif request.method == 'POST':
            # Criar nova thread
            data = request.get_json()
            required_fields = ['thread_id', 'id_conversa']
            
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Campos obrigatórios: thread_id, id_conversa"}), 400
            
            # Adicionar timestamp se não fornecido
            if 'inicio_execucao' not in data:
                data['inicio_execucao'] = datetime.utcnow().isoformat()
            
            result = supabase.table('thread_id_track').insert(data).execute()
            return jsonify(result.data), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@supabase_bp.route('/mensagens_processadas', methods=['GET', 'POST'])
def mensagens_processadas():
    """Gerencia a tabela mensagens_processadas"""
    if supabase is None:
        return jsonify({"error": "Supabase não configurado"}), 500
    
    try:
        if request.method == 'GET':
            # Buscar mensagens processadas
            id_conversa = request.args.get('id_conversa')
            if id_conversa:
                result = supabase.table('mensagens_processadas').select('*').eq('id_conversa', id_conversa).execute()
            else:
                result = supabase.table('mensagens_processadas').select('*').limit(100).execute()
            return jsonify(result.data)
        
        elif request.method == 'POST':
            # Registrar nova mensagem processada
            data = request.get_json()
            required_fields = ['id_conversa', 'mensagem', 'resposta']
            
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Campos obrigatórios: id_conversa, mensagem, resposta"}), 400
            
            # Adicionar timestamp se não fornecido
            if 'timestamp' not in data:
                data['timestamp'] = datetime.utcnow().isoformat()
            
            result = supabase.table('mensagens_processadas').insert(data).execute()
            return jsonify(result.data), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@supabase_bp.route('/lead_poupavet', methods=['GET', 'POST'])
def lead_poupavet():
    """Gerencia a tabela lead_poupavet"""
    if supabase is None:
        return jsonify({"error": "Supabase não configurado"}), 500
    
    try:
        if request.method == 'GET':
            # Buscar leads
            telefone = request.args.get('telefone')
            if telefone:
                result = supabase.table('lead_poupavet').select('*').eq('telefone', telefone).execute()
            else:
                result = supabase.table('lead_poupavet').select('*').limit(100).execute()
            return jsonify(result.data)
        
        elif request.method == 'POST':
            # Criar novo lead
            data = request.get_json()
            required_fields = ['telefone']
            
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Campos obrigatórios: telefone"}), 400
            
            # Adicionar timestamp se não fornecido
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow().isoformat()
            
            result = supabase.table('lead_poupavet').insert(data).execute()
            return jsonify(result.data), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@supabase_bp.route('/agenda_reservas', methods=['GET', 'POST'])
def agenda_reservas():
    """Gerencia a tabela agenda_reservas"""
    if supabase is None:
        return jsonify({"error": "Supabase não configurado"}), 500
    
    try:
        if request.method == 'GET':
            # Buscar reservas
            data_inicio = request.args.get('data_inicio')
            data_fim = request.args.get('data_fim')
            
            query = supabase.table('agenda_reservas').select('*')
            
            if data_inicio:
                query = query.gte('data_agendamento', data_inicio)
            if data_fim:
                query = query.lte('data_agendamento', data_fim)
            
            result = query.execute()
            return jsonify(result.data)
        
        elif request.method == 'POST':
            # Criar nova reserva
            data = request.get_json()
            required_fields = ['tutor', 'pet', 'servico', 'data_agendamento', 'hora_agendamento']
            
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Campos obrigatórios: tutor, pet, servico, data_agendamento, hora_agendamento"}), 400
            
            # Adicionar timestamp se não fornecido
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow().isoformat()
            
            result = supabase.table('agenda_reservas').insert(data).execute()
            return jsonify(result.data), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@supabase_bp.route('/escala_medicos', methods=['GET'])
def escala_medicos():
    """Busca a escala de médicos"""
    if supabase is None:
        return jsonify({"error": "Supabase não configurado"}), 500
    
    try:
        data_consulta = request.args.get('data')
        query = supabase.table('escala_medicos').select('*')
        
        if data_consulta:
            query = query.eq('data', data_consulta)
        
        result = query.execute()
        return jsonify(result.data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@supabase_bp.route('/erros_bot', methods=['POST'])
def registrar_erro():
    """Registra erros do bot"""
    if supabase is None:
        return jsonify({"error": "Supabase não configurado"}), 500
    
    try:
        data = request.get_json()
        required_fields = ['erro', 'contexto']
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Campos obrigatórios: erro, contexto"}), 400
        
        # Adicionar timestamp se não fornecido
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()
        
        result = supabase.table('erros_bot').insert(data).execute()
        return jsonify(result.data), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

