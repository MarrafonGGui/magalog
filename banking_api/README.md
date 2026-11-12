# API Bancária Assíncrona — FastAPI

Projeto didático de uma API REST bancária usando `async def` no FastAPI e acesso assíncrono ao SQLite com `aiosqlite`.

## Funcionalidades

- Criar contas bancárias.
- Consultar dados da conta e saldo.
- Realizar depósitos.
- Realizar saques, bloqueando operações sem saldo suficiente.
- Transferir valores entre contas.
- Consultar extrato com paginação (`limit` e `offset`).
- Documentação interativa automática pelo Swagger UI.

## Tecnologias

- Python 3.10+
- FastAPI
- Uvicorn
- aiosqlite
- Pydantic v2
- SQLite

Os valores monetários são armazenados como centavos inteiros (`INTEGER`), evitando cálculos com ponto flutuante. Saques e transferências utilizam transações SQLite (`BEGIN IMMEDIATE`), e os lançamentos de extrato são gravados junto com a alteração do saldo.

## Executar no Windows (PowerShell)

```powershell
cd banking_api
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Executar no Linux/macOS

```bash
cd banking_api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

A API ficará disponível em `http://127.0.0.1:8000`.

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/health`

O arquivo `bank.db` é criado automaticamente na pasta em que o servidor for iniciado. Para alterar o caminho, defina a variável de ambiente `BANK_DB_PATH`.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Verificar se a API está funcionando |
| `POST` | `/accounts` | Criar conta |
| `GET` | `/accounts/{account_id}` | Consultar conta e saldo |
| `POST` | `/accounts/{account_id}/deposit` | Depositar |
| `POST` | `/accounts/{account_id}/withdraw` | Sacar |
| `POST` | `/accounts/{source_account_id}/transfers` | Transferir para outra conta |
| `GET` | `/accounts/{account_id}/transactions` | Consultar extrato |

## Exemplos de requisição

### 1. Criar conta

`POST /accounts`

```json
{
  "holder_name": "Maria da Silva"
}
```

### 2. Depositar R$ 500,00

`POST /accounts/{account_id}/deposit`

```json
{
  "amount": "500.00",
  "description": "Depósito inicial"
}
```

### 3. Sacar R$ 100,00

`POST /accounts/{account_id}/withdraw`

```json
{
  "amount": "100.00",
  "description": "Saque no caixa"
}
```

### 4. Transferir R$ 75,50

`POST /accounts/{source_account_id}/transfers`

```json
{
  "destination_account_id": "UUID-DA-CONTA-DESTINO",
  "amount": "75.50",
  "description": "Pagamento"
}
```

### 5. Consultar extrato

`GET /accounts/{account_id}/transactions?limit=20&offset=0`

## Executar os testes

```bash
pytest -q
```

## Códigos HTTP principais

- `201`: conta criada.
- `200`: consulta ou operação realizada.
- `404`: conta não encontrada.
- `409`: saldo insuficiente.
- `422`: dados inválidos (por exemplo, valor negativo ou com mais de duas casas decimais).

## Limitações importantes

Este projeto é para estudo e demonstração. Não possui autenticação, autorização, KYC, criptografia de dados sensíveis, limites antifraude, trilha de auditoria imutável, idempotência de requisições ou integração com sistemas de pagamento. SQLite é adequado para desenvolvimento local e prototipação, mas um sistema financeiro de produção precisaria de arquitetura, controles de segurança, observabilidade e banco de dados apropriados (por exemplo, PostgreSQL), além de revisão especializada. `aiosqlite` fornece uma interface `async` para SQLite, mas não transforma o mecanismo SQLite em um banco de dados de rede não bloqueante.
