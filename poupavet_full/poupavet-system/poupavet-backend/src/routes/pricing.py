from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
import os
from src.routes.supabase_integration import supabase

pricing_bp = Blueprint('pricing', __name__)

class PricingManager:
    """Gerenciador de precificação e custos"""
    
    def __init__(self):
        self.pricing_models = {
            "fixo_mensal": {
                "name": "Plano Fixo Mensal",
                "base_price": 299.00,
                "included_interactions": 1000,
                "extra_interaction_cost": 0.30
            },
            "hibrido": {
                "name": "Modelo Híbrido",
                "base_price": 149.00,
                "included_interactions": 500,
                "extra_interaction_cost": 0.30
            },
            "por_uso": {
                "name": "Modelo Por Uso",
                "base_price": 100.00,  # Mínimo mensal
                "cost_per_interaction": 0.35
            },
            "por_resultado": {
                "name": "Baseado em Resultado",
                "cost_per_appointment": 2.00,
                "cost_per_lead": 1.50
            },
            "por_canal": {
                "name": "Preço por Canal",
                "whatsapp_cost": 0.40,
                "web_cost": 0.25,
                "base_price": 50.00
            }
        }
        
        self.channel_costs = {
            "whatsapp": 0.05,  # Custo adicional da API do WhatsApp
            "web": 0.00,       # Sem custo adicional
            "telegram": 0.02,
            "instagram": 0.03
        }
    
    def register_interaction(self, client_id, interaction_type, channel, metadata=None):
        """Registra uma interação para cálculo de custos"""
        try:
            interaction_data = {
                "client_id": client_id,
                "interaction_type": interaction_type,  # chat, agendamento, consulta_preco, etc.
                "channel": channel,  # whatsapp, web, etc.
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
                "base_cost": self._calculate_base_cost(interaction_type, channel),
                "channel_cost": self.channel_costs.get(channel, 0)
            }
            
            if supabase:
                result = supabase.table('pricing_interactions').insert(interaction_data).execute()
                return result.data[0] if result.data else None
            
            return interaction_data
        except Exception as e:
            print(f"Erro ao registrar interação: {e}")
            return None
    
    def _calculate_base_cost(self, interaction_type, channel):
        """Calcula custo base da interação"""
        base_costs = {
            "chat": 0.10,
            "agendamento": 0.50,
            "consulta_preco": 0.05,
            "emergencia": 1.00,
            "redirecionamento": 0.20
        }
        
        return base_costs.get(interaction_type, 0.10)
    
    def calculate_monthly_cost(self, client_id, pricing_model, start_date=None, end_date=None):
        """Calcula custo mensal para um cliente"""
        try:
            if not start_date:
                start_date = datetime.now().replace(day=1)
            if not end_date:
                next_month = start_date.replace(month=start_date.month + 1) if start_date.month < 12 else start_date.replace(year=start_date.year + 1, month=1)
                end_date = next_month - timedelta(days=1)
            
            # Buscar interações do período
            if supabase:
                result = supabase.table('pricing_interactions')\
                    .select('*')\
                    .eq('client_id', client_id)\
                    .gte('timestamp', start_date.isoformat())\
                    .lte('timestamp', end_date.isoformat())\
                    .execute()
                
                interactions = result.data
            else:
                interactions = []
            
            return self._apply_pricing_model(interactions, pricing_model)
        except Exception as e:
            print(f"Erro ao calcular custo mensal: {e}")
            return {"error": str(e)}
    
    def _apply_pricing_model(self, interactions, model_name):
        """Aplica modelo de precificação às interações"""
        model = self.pricing_models.get(model_name)
        if not model:
            return {"error": "Modelo de precificação não encontrado"}
        
        total_interactions = len(interactions)
        total_base_cost = sum(i.get('base_cost', 0) for i in interactions)
        total_channel_cost = sum(i.get('channel_cost', 0) for i in interactions)
        
        # Contar tipos específicos
        agendamentos = len([i for i in interactions if i.get('interaction_type') == 'agendamento'])
        leads = len([i for i in interactions if i.get('interaction_type') == 'chat' and i.get('metadata', {}).get('is_new_lead')])
        
        # Contar por canal
        channel_counts = {}
        for interaction in interactions:
            channel = interaction.get('channel', 'unknown')
            channel_counts[channel] = channel_counts.get(channel, 0) + 1
        
        result = {
            "model": model_name,
            "model_name": model["name"],
            "period_stats": {
                "total_interactions": total_interactions,
                "total_appointments": agendamentos,
                "total_leads": leads,
                "channel_breakdown": channel_counts,
                "total_base_cost": total_base_cost,
                "total_channel_cost": total_channel_cost
            }
        }
        
        if model_name == "fixo_mensal":
            base_cost = model["base_price"]
            extra_interactions = max(0, total_interactions - model["included_interactions"])
            extra_cost = extra_interactions * model["extra_interaction_cost"]
            
            result.update({
                "base_price": base_cost,
                "included_interactions": model["included_interactions"],
                "extra_interactions": extra_interactions,
                "extra_cost": extra_cost,
                "total_cost": base_cost + extra_cost
            })
        
        elif model_name == "hibrido":
            base_cost = model["base_price"]
            extra_interactions = max(0, total_interactions - model["included_interactions"])
            extra_cost = extra_interactions * model["extra_interaction_cost"]
            
            result.update({
                "base_price": base_cost,
                "included_interactions": model["included_interactions"],
                "extra_interactions": extra_interactions,
                "extra_cost": extra_cost,
                "total_cost": base_cost + extra_cost
            })
        
        elif model_name == "por_uso":
            usage_cost = total_interactions * model["cost_per_interaction"]
            final_cost = max(model["base_price"], usage_cost)
            
            result.update({
                "minimum_monthly": model["base_price"],
                "usage_cost": usage_cost,
                "cost_per_interaction": model["cost_per_interaction"],
                "total_cost": final_cost
            })
        
        elif model_name == "por_resultado":
            appointment_cost = agendamentos * model["cost_per_appointment"]
            lead_cost = leads * model["cost_per_lead"]
            
            result.update({
                "appointment_cost": appointment_cost,
                "lead_cost": lead_cost,
                "cost_per_appointment": model["cost_per_appointment"],
                "cost_per_lead": model["cost_per_lead"],
                "total_cost": appointment_cost + lead_cost
            })
        
        elif model_name == "por_canal":
            base_cost = model["base_price"]
            whatsapp_cost = channel_counts.get('whatsapp', 0) * model["whatsapp_cost"]
            web_cost = channel_counts.get('web', 0) * model["web_cost"]
            
            result.update({
                "base_price": base_cost,
                "whatsapp_interactions": channel_counts.get('whatsapp', 0),
                "web_interactions": channel_counts.get('web', 0),
                "whatsapp_cost": whatsapp_cost,
                "web_cost": web_cost,
                "total_cost": base_cost + whatsapp_cost + web_cost + total_channel_cost
            })
        
        return result
    
    def get_usage_analytics(self, client_id, days=30):
        """Obtém analytics de uso para um cliente"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            if supabase:
                result = supabase.table('pricing_interactions')\
                    .select('*')\
                    .eq('client_id', client_id)\
                    .gte('timestamp', start_date.isoformat())\
                    .lte('timestamp', end_date.isoformat())\
                    .execute()
                
                interactions = result.data
            else:
                interactions = []
            
            # Análise por dia
            daily_stats = {}
            for interaction in interactions:
                date = interaction['timestamp'][:10]  # YYYY-MM-DD
                if date not in daily_stats:
                    daily_stats[date] = {
                        'total': 0,
                        'by_type': {},
                        'by_channel': {},
                        'cost': 0
                    }
                
                daily_stats[date]['total'] += 1
                
                interaction_type = interaction.get('interaction_type', 'unknown')
                daily_stats[date]['by_type'][interaction_type] = daily_stats[date]['by_type'].get(interaction_type, 0) + 1
                
                channel = interaction.get('channel', 'unknown')
                daily_stats[date]['by_channel'][channel] = daily_stats[date]['by_channel'].get(channel, 0) + 1
                
                daily_stats[date]['cost'] += interaction.get('base_cost', 0) + interaction.get('channel_cost', 0)
            
            # Estatísticas gerais
            total_interactions = len(interactions)
            total_cost = sum(i.get('base_cost', 0) + i.get('channel_cost', 0) for i in interactions)
            avg_daily = total_interactions / days if days > 0 else 0
            
            # Top tipos de interação
            type_counts = {}
            for interaction in interactions:
                interaction_type = interaction.get('interaction_type', 'unknown')
                type_counts[interaction_type] = type_counts.get(interaction_type, 0) + 1
            
            # Top canais
            channel_counts = {}
            for interaction in interactions:
                channel = interaction.get('channel', 'unknown')
                channel_counts[channel] = channel_counts.get(channel, 0) + 1
            
            return {
                "period": f"{days} dias",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "summary": {
                    "total_interactions": total_interactions,
                    "total_cost": round(total_cost, 2),
                    "average_daily": round(avg_daily, 2),
                    "average_cost_per_interaction": round(total_cost / total_interactions, 4) if total_interactions > 0 else 0
                },
                "daily_breakdown": daily_stats,
                "top_interaction_types": sorted(type_counts.items(), key=lambda x: x[1], reverse=True),
                "channel_distribution": sorted(channel_counts.items(), key=lambda x: x[1], reverse=True)
            }
        except Exception as e:
            print(f"Erro ao obter analytics: {e}")
            return {"error": str(e)}
    
    def project_monthly_cost(self, client_id, pricing_model):
        """Projeta custo mensal baseado no uso atual"""
        try:
            # Usar últimos 7 dias para projeção
            analytics = self.get_usage_analytics(client_id, days=7)
            
            if "error" in analytics:
                return analytics
            
            weekly_interactions = analytics["summary"]["total_interactions"]
            projected_monthly = (weekly_interactions / 7) * 30  # Projeção para 30 dias
            
            # Simular interações para o mês
            simulated_interactions = []
            for i in range(int(projected_monthly)):
                simulated_interactions.append({
                    'interaction_type': 'chat',
                    'channel': 'whatsapp',
                    'base_cost': 0.10,
                    'channel_cost': 0.05
                })
            
            projected_cost = self._apply_pricing_model(simulated_interactions, pricing_model)
            projected_cost["is_projection"] = True
            projected_cost["based_on_days"] = 7
            projected_cost["projected_monthly_interactions"] = int(projected_monthly)
            
            return projected_cost
        except Exception as e:
            print(f"Erro ao projetar custo: {e}")
            return {"error": str(e)}

# Instância global do gerenciador
pricing_manager = PricingManager()

@pricing_bp.route('/health', methods=['GET'])
def health_check():
    """Verifica a saúde do sistema de precificação"""
    return jsonify({"status": "ok", "message": "Sistema de precificação funcionando!"})

@pricing_bp.route('/register-interaction', methods=['POST'])
def register_interaction():
    """Registra uma nova interação"""
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        interaction_type = data.get('interaction_type')
        channel = data.get('channel')
        metadata = data.get('metadata')
        
        if not all([client_id, interaction_type, channel]):
            return jsonify({"error": "Campos obrigatórios: client_id, interaction_type, channel"}), 400
        
        result = pricing_manager.register_interaction(client_id, interaction_type, channel, metadata)
        
        if result:
            return jsonify({"message": "Interação registrada com sucesso", "data": result}), 201
        else:
            return jsonify({"error": "Erro ao registrar interação"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pricing_bp.route('/calculate-cost/<client_id>', methods=['POST'])
def calculate_monthly_cost(client_id):
    """Calcula custo mensal para um cliente"""
    try:
        data = request.get_json()
        pricing_model = data.get('pricing_model', 'hibrido')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        result = pricing_manager.calculate_monthly_cost(client_id, pricing_model, start_date, end_date)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pricing_bp.route('/analytics/<client_id>', methods=['GET'])
def get_usage_analytics(client_id):
    """Obtém analytics de uso"""
    try:
        days = int(request.args.get('days', 30))
        result = pricing_manager.get_usage_analytics(client_id, days)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pricing_bp.route('/projection/<client_id>', methods=['POST'])
def project_monthly_cost(client_id):
    """Projeta custo mensal"""
    try:
        data = request.get_json()
        pricing_model = data.get('pricing_model', 'hibrido')
        
        result = pricing_manager.project_monthly_cost(client_id, pricing_model)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pricing_bp.route('/models', methods=['GET'])
def list_pricing_models():
    """Lista todos os modelos de precificação disponíveis"""
    return jsonify({"pricing_models": pricing_manager.pricing_models})

@pricing_bp.route('/compare-models/<client_id>', methods=['GET'])
def compare_pricing_models(client_id):
    """Compara todos os modelos de precificação para um cliente"""
    try:
        days = int(request.args.get('days', 30))
        
        # Obter analytics primeiro
        analytics = pricing_manager.get_usage_analytics(client_id, days)
        
        if "error" in analytics:
            return jsonify(analytics), 500
        
        # Calcular custo para cada modelo
        comparisons = {}
        for model_name in pricing_manager.pricing_models.keys():
            try:
                cost_calc = pricing_manager.calculate_monthly_cost(client_id, model_name)
                comparisons[model_name] = cost_calc
            except Exception as e:
                comparisons[model_name] = {"error": str(e)}
        
        return jsonify({
            "client_id": client_id,
            "period_analytics": analytics,
            "model_comparisons": comparisons,
            "recommendation": _get_best_model_recommendation(comparisons)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _get_best_model_recommendation(comparisons):
    """Recomenda o melhor modelo baseado nos custos"""
    try:
        valid_models = {k: v for k, v in comparisons.items() if "total_cost" in v}
        
        if not valid_models:
            return {"model": None, "reason": "Nenhum modelo válido encontrado"}
        
        # Encontrar modelo com menor custo
        best_model = min(valid_models.items(), key=lambda x: x[1]["total_cost"])
        
        return {
            "recommended_model": best_model[0],
            "estimated_cost": best_model[1]["total_cost"],
            "reason": f"Menor custo total: R$ {best_model[1]['total_cost']:.2f}"
        }
    except Exception as e:
        return {"model": None, "reason": f"Erro ao calcular recomendação: {str(e)}"}

@pricing_bp.route('/dashboard/<client_id>', methods=['GET'])
def pricing_dashboard(client_id):
    """Dashboard completo de precificação para um cliente"""
    try:
        # Analytics dos últimos 30 dias
        analytics_30d = pricing_manager.get_usage_analytics(client_id, 30)
        
        # Analytics dos últimos 7 dias
        analytics_7d = pricing_manager.get_usage_analytics(client_id, 7)
        
        # Projeção para o modelo híbrido (padrão)
        projection = pricing_manager.project_monthly_cost(client_id, 'hibrido')
        
        # Custo atual do mês
        current_month_cost = pricing_manager.calculate_monthly_cost(client_id, 'hibrido')
        
        return jsonify({
            "client_id": client_id,
            "current_month": current_month_cost,
            "analytics_30_days": analytics_30d,
            "analytics_7_days": analytics_7d,
            "monthly_projection": projection,
            "generated_at": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

