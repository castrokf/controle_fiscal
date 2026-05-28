# Controle Marketplace Fiscal - Ambiente de Teste

MVP Flask para validar fluxo empresarial de pedidos ficticios, marketplaces ficticios, validacao fiscal simulada, dashboard, relatórios, logs, fechamento diario e geracao de XML/PDF fake.

Este projeto e 100% ficticio.

- Nao emite NF-e real.
- Nao chama SEFAZ.
- Nao usa certificado digital.
- Nao integra Amazon SP-API real.
- Nao integra Shopee Open Platform real.
- Nao usa scraping, Selenium ou automacao de login.
- Nao usa dados reais, CPF/CNPJ real, endereco real ou credenciais reais.

## Stack

- Python 3.11+
- Flask
- SQLAlchemy
- Flask-Migrate
- Flask-Login
- Flask-WTF
- Flask-Bcrypt
- SQLite local ou PostgreSQL
- Bootstrap 5
- Jinja2
- python-dotenv
- pandas/openpyxl
- APScheduler opcional, desativado por padrao

## Estrutura

```text
controle-marketplace-fiscal-teste/
  app/
    auth/
    dashboard/
    orders/
    products/
    fiscal/
    reports/
    logs/
    settings/
    closing/
    models/
    templates/
    static/
  migrations/
  storage/
    invoices/
      xml/
      pdf/
  tests/
  run.py
  requirements.txt
  .env.example
  README.md
```

## Instalar no Windows

Entre na pasta do projeto:

```powershell
cd C:\Users\REDFIT\OneDrive\Documentos\controle_fiscal\controle-marketplace-fiscal-teste
```

Crie e ative o ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependencias:

```powershell
python -m pip install -r requirements.txt
```

Crie o arquivo `.env` com base no exemplo:

```powershell
copy .env.example .env
```

## Banco de dados

Aplicar migrations:

```powershell
python -m flask --app run.py db upgrade
```

Popular dados ficticios:

```powershell
python -m flask --app run.py seed
```

O seed cria:

- 1 usuario administrador
- 20 produtos ficticios
- 50 pedidos ficticios Amazon
- 50 pedidos ficticios Shopee
- compradores, enderecos e documentos ficticios
- notas fiscais ficticias autorizadas e rejeitadas
- pedidos sem NF-e
- produtos sem classificacao fiscal do produto (NCM)
- produtos sem codigo fiscal da operacao (CFOP)
- logs e fechamentos diarios ficticios

## Rodar localmente

```powershell
python -m flask --app run.py run --debug
```

Acesse:

```text
http://127.0.0.1:5000
```

Login inicial:

```text
Email: admin@teste.com
Senha: Teste@1234
```

## Testar filtro por horario

No menu `Pedidos`, use:

```text
Marketplace: Amazon ou Shopee
Horario inicial: 08:00
Horario final: 18:00
```

Esse filtro usa o campo `order_datetime` dos pedidos ficticios.

## Emitir NF-e ficticia

1. Acesse `Pedidos`.
2. Abra um pedido.
3. Clique em `Validar fiscal`.
4. Clique em `Emitir NF-e ficticia`.
5. Clique em `Gerar XML/PDF fake`.
6. Baixe os arquivos pela tela do pedido ou por `Fiscal Simulado`.

Os arquivos ficam em:

```text
storage/invoices/xml
storage/invoices/pdf
```

Ao clicar em `Baixar XML` ou `Baixar PDF`, o sistema gera um arquivo com corpo e finalidade:

- finalidade do documento de teste;
- aviso de que nao possui validade fiscal;
- dados do pedido ficticio;
- comprador e endereco ficticios;
- itens;
- valores ficticios;
- status fiscal simulado;
- motivo de rejeicao ficticia, quando existir.

O PDF usa um modelo visual inspirado em DANFE para teste operacional. Ele tem quadros, cabecalho, destinatario, valores, produtos e informacoes adicionais. O arquivo real usado como referencia visual nao e copiado para dentro do projeto e nenhum dado real dele e reaproveitado.

No Windows local, uma copia tambem e salva em:

```text
C:\Users\REDFIT\Downloads\controle-marketplace-fiscal-teste
```

## Gerar pedidos ficticios agora

1. Acesse `Configuracoes`.
2. Clique em `Gerar pedidos ficticios agora`.

APScheduler existe no projeto, mas fica desligado por padrao:

```env
AUTO_GENERATE_FAKE_ORDERS=false
FAKE_ORDER_INTERVAL_MINUTES=10
```

## Rodar testes

```powershell
python -m pytest -q
```

Cobertura basica:

- login
- bloqueio sem login
- criacao de produto
- seed
- listagem de pedidos
- filtro por horario
- validacao fiscal simulada
- emissao de NF-e ficticia
- geracao de XML/PDF fake
- relatorios e CSV

## Deploy de teste no Render

O repositório já tem um `render.yaml` na raiz apontando para esta pasta:

```text
controle-marketplace-fiscal-teste
```

Esse Blueprint cria:

- 1 Web Service Python;
- 1 banco PostgreSQL;
- `SECRET_KEY` gerada automaticamente;
- `DATABASE_URL` ligada ao PostgreSQL;
- migrations antes do deploy;
- seed inicial uma vez para criar dados ficticios.

No Render:

1. Faça push para o GitHub.
2. Acesse `New > Blueprint`.
3. Conecte o repositório `castrokf/controle_fiscal`.
4. Selecione o arquivo `render.yaml` na raiz.
5. Clique em `Deploy Blueprint`.

Configuracao usada pelo Blueprint:

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn run:app
```

Pre-deploy command:

```bash
python -m flask --app run.py db upgrade
```

Initial deploy hook:

```bash
python -m flask --app run.py seed
```

Variaveis de ambiente principais:

```env
SECRET_KEY=gerada automaticamente pelo Render
DATABASE_URL=ligada automaticamente ao PostgreSQL do Render
AUTO_GENERATE_FAKE_ORDERS=false
FAKE_ORDER_INTERVAL_MINUTES=10
LOCAL_DOWNLOAD_COPY_ENABLED=false
```

Se o plano escolhido nao executar `preDeployCommand` ou `initialDeployHook`, rode manualmente no Shell do Render:

```bash
python -m flask --app run.py db upgrade
python -m flask --app run.py seed
```

Para Render, prefira PostgreSQL. SQLite em hospedagem pode perder dados em reinicio de ambiente.

## O que mudaria para virar sistema real

- Substituir `MockFiscalProvider` por provedor fiscal homologado.
- Implementar ambiente de homologacao fiscal antes de qualquer producao.
- Criar integracoes oficiais com Amazon SP-API e Shopee Open Platform.
- Usar armazenamento seguro para certificados, tokens e secrets.
- Validar classificacao fiscal do produto (NCM), codigo fiscal da operacao (CFOP), situacao tributaria (CST/CSOSN), regras tributarias e dados do comprador com regras reais.
- Adicionar fila de processamento para emissao fiscal.
- Criar controle de permissoes mais granular.
- Adicionar observabilidade, backups, auditoria formal e politicas LGPD.
- Revisar seguranca, testes e deploy com checklist de producao.
