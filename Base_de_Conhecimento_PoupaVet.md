# Base de Conhecimento PoupaVet

## 1. Preços e Serviços

### Estrutura Sugerida:
```json
{
  "servicos": [
    {
      "nome": "Consulta Padrão",
      "preco": 85.00,
      "descricao": "Consulta veterinária geral."
    },
    {
      "nome": "Vacina V10",
      "preco": 120.00,
      "descricao": "Vacina múltipla para cães."
    },
    {
      "nome": "Vacina Antirrábica",
      "preco": 80.00,
      "descricao": "Vacina contra raiva."
    }
    // ... outros serviços e preços
  ]
}
```

## 2. Dados de Agendamento

### Estrutura Obrigatória:
```json
{
  "intencao": "agendamento",
  "tutor": "[Nome do Tutor]",
  "pet": "[Nome do Pet]",
  "especie": "[cão/gato/coelho/etc.]",
  "servico": "[Serviço Solicitado]",
  "data": "AAAA-MM-DD",
  "hora": "HH:MM"
}
```

### Estrutura Opcional (se fornecido pelo cliente):
```json
{
  "medico": "[Nome do Médico]",
  "especialidade": "[Especialidade]"
}
```

### Exemplo Completo de JSON de Agendamento:
```json
{
  "medico": "Ana",
  "especialidade": "cirurgia",
  "intencao": "agendamento",
  "tutor": "Eric",
  "pet": "Dorje",
  "especie": "cão",
  "servico": "retorno",
  "data": "2025-05-11",
  "hora": "13:00",
  "detalhamento": "✅ Retorno da Belinha confirmado para 29/05 às 13h 💖🐾"
}
```

## 3. JSON para Redirecionamento

### Estrutura Padrão:
```json
{
  "intencao": "outro",
  "redirecionar": "humano"
}
```

## 4. JSON para Emergência

### Estrutura Padrão:
```json
{
  "intencao": "emergencia",
  "redirecionar": "humano"
}
```

## 5. JSON para Botões Interativos

### buttonList (escolhas simples):
```json
{
  "buttonList": {
    "buttons": [
      { "id": "cao", "label": "🐶 Cão" },
      { "id": "gato", "label": "🐱 Gato" }
    ]
  }
}
```

### optionList (escolhas com descrição):
```json
{
  "optionList": {
    "title": "Escolha a Especialidade",
    "buttonLabel": "Selecionar especialidade",
    "options": [
      { "id": "1", "title": "Dermatologia", "description": "Coceira, feridas, alergias" },
      { "id": "2", "title": "Cardiologia", "description": "Coração, sopros, exames" }
    ]
  }
}
```

## 6. JSON para Botão de Listagem de Médicos (intencao: botao_list_medico)

### Estrutura Padrão:
```json
{
  "intencao": "botao_list_medico",
  "message": "Você tem preferência por algum médico ou médica da nossa equipe? 😊 Se preferir, selecione abaixo:"
}
```

