from flask import Blueprint, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import json
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials as ServiceCredentials

google_bp = Blueprint('google', __name__)

# Configurações do Google
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets'
]

class GoogleSheetsManager:
    """Gerenciador de integração com Google Sheets"""
    
    def __init__(self, credentials_file=None):
        self.credentials_file = credentials_file or GOOGLE_CREDENTIALS_FILE
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa o cliente do Google Sheets"""
        try:
            if os.path.exists(self.credentials_file):
                creds = ServiceCredentials.from_service_account_file(
                    self.credentials_file, scopes=SCOPES
                )
                self.client = gspread.authorize(creds)
        except Exception as e:
            print(f"Erro ao inicializar Google Sheets: {e}")
    
    def read_knowledge_base(self, spreadsheet_id, sheet_name="Base_Conhecimento"):
        """Lê a base de conhecimento do Google Sheets"""
        try:
            if not self.client:
                return None
            
            sheet = self.client.open_by_key(spreadsheet_id).worksheet(sheet_name)
            records = sheet.get_all_records()
            return records
        except Exception as e:
            print(f"Erro ao ler base de conhecimento: {e}")
            return None
    
    def update_thread_tracking(self, spreadsheet_id, thread_id, phone_number, status="active"):
        """Atualiza rastreamento de threads"""
        try:
            if not self.client:
                return False
            
            sheet = self.client.open_by_key(spreadsheet_id).worksheet("Thread_Tracking")
            
            # Verificar se já existe
            records = sheet.get_all_records()
            row_to_update = None
            
            for i, record in enumerate(records):
                if record.get('phone_number') == phone_number:
                    row_to_update = i + 2  # +2 porque começa na linha 2
                    break
            
            data = [thread_id, phone_number, datetime.now().isoformat(), status]
            
            if row_to_update:
                # Atualizar linha existente
                sheet.update(f"A{row_to_update}:D{row_to_update}", [data])
            else:
                # Adicionar nova linha
                sheet.append_row(data)
            
            return True
        except Exception as e:
            print(f"Erro ao atualizar thread tracking: {e}")
            return False
    
    def log_interaction(self, spreadsheet_id, phone_number, message, response, intent=""):
        """Registra interação no Google Sheets"""
        try:
            if not self.client:
                return False
            
            sheet = self.client.open_by_key(spreadsheet_id).worksheet("Interactions_Log")
            
            data = [
                datetime.now().isoformat(),
                phone_number,
                message,
                response,
                intent
            ]
            
            sheet.append_row(data)
            return True
        except Exception as e:
            print(f"Erro ao registrar interação: {e}")
            return False
    
    def get_doctor_schedule(self, spreadsheet_id, date=None):
        """Obtém escala de médicos"""
        try:
            if not self.client:
                return []
            
            sheet = self.client.open_by_key(spreadsheet_id).worksheet("Escala_Medicos")
            records = sheet.get_all_records()
            
            if date:
                # Filtrar por data específica
                filtered_records = [r for r in records if r.get('data') == date]
                return filtered_records
            
            return records
        except Exception as e:
            print(f"Erro ao obter escala de médicos: {e}")
            return []

class GoogleCalendarManager:
    """Gerenciador de integração com Google Calendar"""
    
    def __init__(self):
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Inicializa o serviço do Google Calendar"""
        try:
            creds = None
            
            # Carregar token existente
            if os.path.exists(GOOGLE_TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
            
            # Se não há credenciais válidas, fazer autenticação
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if os.path.exists(GOOGLE_CREDENTIALS_FILE):
                        flow = Flow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
                        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                        
                        # Para desenvolvimento, usar flow offline
                        print("Acesse este URL para autorizar a aplicação:")
                        auth_url, _ = flow.authorization_url(prompt='consent')
                        print(auth_url)
                        
                        # Em produção, implementar fluxo web adequado
                        return
                
                # Salvar credenciais
                with open(GOOGLE_TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('calendar', 'v3', credentials=creds)
        except Exception as e:
            print(f"Erro ao inicializar Google Calendar: {e}")
    
    def list_calendars(self):
        """Lista todos os calendários disponíveis"""
        try:
            if not self.service:
                return []
            
            calendars_result = self.service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            return calendars
        except Exception as e:
            print(f"Erro ao listar calendários: {e}")
            return []
    
    def check_availability(self, calendar_ids, start_time, end_time):
        """Verifica disponibilidade em múltiplas agendas"""
        try:
            if not self.service:
                return {"available": False, "conflicts": []}
            
            conflicts = []
            
            for calendar_id in calendar_ids:
                # Buscar eventos no período
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=start_time.isoformat(),
                    timeMax=end_time.isoformat(),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                
                for event in events:
                    conflicts.append({
                        'calendar_id': calendar_id,
                        'event_id': event['id'],
                        'summary': event.get('summary', 'Sem título'),
                        'start': event['start'].get('dateTime', event['start'].get('date')),
                        'end': event['end'].get('dateTime', event['end'].get('date'))
                    })
            
            return {
                "available": len(conflicts) == 0,
                "conflicts": conflicts,
                "total_conflicts": len(conflicts)
            }
        except Exception as e:
            print(f"Erro ao verificar disponibilidade: {e}")
            return {"available": False, "conflicts": [], "error": str(e)}
    
    def create_appointment(self, calendar_id, title, description, start_time, end_time, attendee_email=None):
        """Cria um agendamento no Google Calendar"""
        try:
            if not self.service:
                return None
            
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 dia antes
                        {'method': 'popup', 'minutes': 60},       # 1 hora antes
                    ],
                },
            }
            
            if attendee_email:
                event['attendees'] = [{'email': attendee_email}]
            
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            return created_event
        except Exception as e:
            print(f"Erro ao criar agendamento: {e}")
            return None
    
    def get_available_slots(self, calendar_ids, date, duration_minutes=60):
        """Obtém horários disponíveis para uma data específica"""
        try:
            if not self.service:
                return []
            
            # Definir horário de funcionamento (8h às 18h)
            start_of_day = datetime.combine(date, datetime.min.time().replace(hour=8))
            end_of_day = datetime.combine(date, datetime.min.time().replace(hour=18))
            
            # Verificar disponibilidade em intervalos de 1 hora
            available_slots = []
            current_time = start_of_day
            
            while current_time < end_of_day:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                availability = self.check_availability(calendar_ids, current_time, slot_end)
                
                if availability["available"]:
                    available_slots.append({
                        'start': current_time.strftime('%H:%M'),
                        'end': slot_end.strftime('%H:%M'),
                        'datetime_start': current_time.isoformat(),
                        'datetime_end': slot_end.isoformat()
                    })
                
                current_time += timedelta(hours=1)
            
            return available_slots
        except Exception as e:
            print(f"Erro ao obter horários disponíveis: {e}")
            return []

# Instâncias globais
sheets_manager = GoogleSheetsManager()
calendar_manager = GoogleCalendarManager()

@google_bp.route('/health', methods=['GET'])
def health_check():
    """Verifica a saúde das integrações Google"""
    status = {
        "sheets": sheets_manager.client is not None,
        "calendar": calendar_manager.service is not None
    }
    return jsonify({"status": status})

@google_bp.route('/sheets/knowledge-base/<spreadsheet_id>', methods=['GET'])
def get_knowledge_base(spreadsheet_id):
    """Obtém base de conhecimento do Google Sheets"""
    try:
        sheet_name = request.args.get('sheet_name', 'Base_Conhecimento')
        data = sheets_manager.read_knowledge_base(spreadsheet_id, sheet_name)
        
        if data is None:
            return jsonify({"error": "Erro ao acessar planilha"}), 500
        
        return jsonify({"data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@google_bp.route('/sheets/thread-tracking/<spreadsheet_id>', methods=['POST'])
def update_thread_tracking(spreadsheet_id):
    """Atualiza rastreamento de threads"""
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        phone_number = data.get('phone_number')
        status = data.get('status', 'active')
        
        success = sheets_manager.update_thread_tracking(
            spreadsheet_id, thread_id, phone_number, status
        )
        
        if success:
            return jsonify({"message": "Thread tracking atualizado com sucesso"})
        else:
            return jsonify({"error": "Erro ao atualizar thread tracking"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@google_bp.route('/sheets/log-interaction/<spreadsheet_id>', methods=['POST'])
def log_interaction(spreadsheet_id):
    """Registra interação no Google Sheets"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        message = data.get('message')
        response = data.get('response')
        intent = data.get('intent', '')
        
        success = sheets_manager.log_interaction(
            spreadsheet_id, phone_number, message, response, intent
        )
        
        if success:
            return jsonify({"message": "Interação registrada com sucesso"})
        else:
            return jsonify({"error": "Erro ao registrar interação"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@google_bp.route('/calendar/calendars', methods=['GET'])
def list_calendars():
    """Lista calendários disponíveis"""
    try:
        calendars = calendar_manager.list_calendars()
        return jsonify({"calendars": calendars})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@google_bp.route('/calendar/availability', methods=['POST'])
def check_availability():
    """Verifica disponibilidade em múltiplas agendas"""
    try:
        data = request.get_json()
        calendar_ids = data.get('calendar_ids', [])
        start_time = datetime.fromisoformat(data.get('start_time'))
        end_time = datetime.fromisoformat(data.get('end_time'))
        
        availability = calendar_manager.check_availability(calendar_ids, start_time, end_time)
        return jsonify(availability)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@google_bp.route('/calendar/available-slots', methods=['POST'])
def get_available_slots():
    """Obtém horários disponíveis para uma data"""
    try:
        data = request.get_json()
        calendar_ids = data.get('calendar_ids', [])
        date_str = data.get('date')
        duration_minutes = data.get('duration_minutes', 60)
        
        date = datetime.fromisoformat(date_str).date()
        slots = calendar_manager.get_available_slots(calendar_ids, date, duration_minutes)
        
        return jsonify({"available_slots": slots})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@google_bp.route('/calendar/create-appointment', methods=['POST'])
def create_appointment():
    """Cria agendamento no Google Calendar"""
    try:
        data = request.get_json()
        calendar_id = data.get('calendar_id')
        title = data.get('title')
        description = data.get('description')
        start_time = datetime.fromisoformat(data.get('start_time'))
        end_time = datetime.fromisoformat(data.get('end_time'))
        attendee_email = data.get('attendee_email')
        
        event = calendar_manager.create_appointment(
            calendar_id, title, description, start_time, end_time, attendee_email
        )
        
        if event:
            return jsonify({
                "message": "Agendamento criado com sucesso",
                "event_id": event['id'],
                "event_link": event.get('htmlLink')
            })
        else:
            return jsonify({"error": "Erro ao criar agendamento"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@google_bp.route('/sheets/doctor-schedule/<spreadsheet_id>', methods=['GET'])
def get_doctor_schedule(spreadsheet_id):
    """Obtém escala de médicos"""
    try:
        date = request.args.get('date')
        schedule = sheets_manager.get_doctor_schedule(spreadsheet_id, date)
        return jsonify({"schedule": schedule})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

