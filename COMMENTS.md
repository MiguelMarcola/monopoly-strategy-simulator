# Guia de Execucao - Simulador de Jogo

## Pre-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes do Python)

## Passo a passo para executar a aplicacao

### 1. Criar ambiente virtual (recomendado)

```bash
python -m venv venv
```

### 2. Ativar o ambiente virtual

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Executar o servidor

```bash
python manage.py runserver 8080
```

O servidor estara disponivel em `http://localhost:8080`

### 5. Testar a API

**Endpoint:** `GET` ou `POST` em `http://localhost:8080/jogo/simular`

**Exemplo com curl:**
```bash
curl http://localhost:8080/jogo/simular
```

**Exemplo de resposta:**
```json
{
  "vencedor": "cauteloso",
  "jogadores": ["cauteloso", "aleatorio", "exigente", "impulsivo"]
}
```

Os logs passo a passo saem no console do servidor.

### 6. Executar testes

Com o venv ativado:

```bash
python -m pytest game/tests/ -v
```

Ou com Django:
```bash
python manage.py test game.tests
```

Se aparecer `ModuleNotFoundError: No module named 'django'`, ative o venv e rode `python -m pytest`.

### 7. Relatorio de cobertura

```bash
python -m pytest game/tests/ --cov=game --cov-report=term-missing
```

Cobertura total e por modulo no terminal.

Relatorio HTML (abre `htmlcov/index.html`):

```bash
python -m pytest game/tests/ --cov=game --cov-report=html
```

O relatorio HTML permite identificar linhas nao cobertas e pontos mortos.

---

## Decisoes arquiteturais

### Separacao dominio, servicos e HTTP

A logica do jogo fica isolada do Django. O framework atua apenas como interface HTTP. Isso permite:

- Testes unitarios sem subir o servidor
- Regras de negocio independentes do framework
- Troca de interface (CLI, outra API) sem alterar o core

### Estrategias abstraidas

Cada tipo de jogador (impulsivo, exigente, cauteloso, aleatorio) implementa a interface `BuyStrategy.should_buy(player, property)`. Beneficios:

- Open/Closed: novas estrategias sem alterar codigo existente
- Testes isolados por estrategia
- Mock de `random` para testes deterministicos do aleatorio

### Eventos e observador

O simulador emite eventos (GameStarted, DiceRolled, PropertyBought, etc). O logger e um observador que consome esses eventos. O jogo funciona identicamente com ou sem logger.

### Parametros do simulador para testes

`GameSimulator(dice=..., event_observer=..., player_order=..., board=...)` aceita parametros opcionais para testes deterministicos: `dice` (mock), `player_order` (lista de indices), `board` (lista de Property).

### Organizacao dos testes

- **test_unit.py**: regras do dominio (Board, Property, Player, Strategy)
- **test_integration.py**: fluxo da simulacao e TurnResolver
- **test_api.py**: contrato do endpoint
- **test_round_1000.py**: desempate e criterios de vitoria

### Determinismo nos testes

- `random.seed(N)` antes de simular para resultados reproduziveis
- `unittest.mock.patch('random.random', return_value=X)` para estrategia aleatoria
- Para testes cirurgicos: injetar `dice`, `player_order` e `board` no `GameSimulator` para controlar dado, ordem dos jogadores e tabuleiro

---

## Estrutura do projeto

```
teste-7com/
├── config/              # Configuracoes do Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── game/
│   ├── domain/          # Entidades e regras puras
│   │   ├── board.py    # Movimento, volta, tabuleiro
│   │   ├── constants.py
│   │   ├── events.py   # GameEvent e subclasses
│   │   ├── player.py
│   │   ├── property.py # Regras de compra e aluguel
│   │   ├── result.py   # SimulationResult
│   │   └── strategies.py
│   ├── observers/      # Infraestrutura de saida
│   │   └── rich_logger.py
│   ├── services/       # Orquestracao
│   │   ├── dice.py
│   │   ├── simulator.py
│   │   └── turn_resolver.py
│   ├── tests/
│   │   ├── test_api.py
│   │   ├── test_integration.py
│   │   ├── test_round_1000.py
│   │   └── test_unit.py
│   ├── urls.py
│   └── views.py
├── manage.py
├── pytest.ini
├── requirements.txt
└── COMMENTS.md
```

---

## Testes automatizados

### Unitarios (test_unit.py)

- Board: movimento, volta, bonus, posicao sempre entre 0 e 19
- Property: compra, aluguel, requires_rent_from (nao paga na propria), nunca dois donos
- Player: saldo, falencia, can_afford
- Strategies: exigente (rent > 50), cauteloso (reserva >= 80), impulsivo (sempre que pode), aleatorio (mock)
- Liberacao apos falencia: propriedades do falido ficam livres, podem ser compradas novamente
- Saldo zero nao elimina
- Invariantes: compra falha nao altera dono, aluguel transfere corretamente

### Integracao (test_integration.py)

- Partida termina com vencedor
- Ranking por saldo, desempate por turno
- Simulador funciona sem logger
- Determinismo com seed e com mock (dice, player_order)
- Jogador falido nao recebe turnos apos falencia
- Um jogador restante: partida encerra com motivo correto
- Propriedade liberada comprada em turno futuro

### Rodada 1000 (test_round_1000.py)

- Desempate por ordem de turno quando saldos iguais
- Vencedor = maior saldo, depois turn_order

### API (test_api.py)

- Status 200, JSON, vencedor e jogadores
- Vencedor string nao vazia, jogadores lista nao vazia
- Vencedor contido em jogadores, sem duplicados
- Jogadores ordenados por ranking (vencedor em primeiro)
