# Controle Fiscal - Ambiente Demo

MVP Flask para validar fluxo de controle fiscal com operacoes simuladas, validacao fiscal, painel gerencial, documentos fiscais, indicadores, auditoria, fechamento diario e geracao de XML/PDF simulados.

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

Abra o `.env` e preencha o administrador inicial antes de rodar o seed:

```env
INITIAL_ADMIN_NAME=Administrador
INITIAL_ADMIN_EMAIL=admin@teste.com
INITIAL_ADMIN_PASSWORD=Teste1234
```

Para este ambiente demo, o acesso configurado e `admin@teste.com` com senha `Teste1234`. Em producao real, troque por uma senha privada no Environment do Render.

## Banco de dados

Aplicar migrations:

```powershell
python -m flask --app run.py db upgrade
```

Popular dados simulados:

```powershell
python -m flask --app run.py seed
```

O seed cria:

- 1 usuario administrador
- 20 produtos simulados
- 50 operacoes Amazon
- 50 operacoes Shopee
- compradores, enderecos e documentos simulados
- notas fiscais simuladas autorizadas e rejeitadas
- pedidos sem NF-e
- produtos sem classificacao fiscal do produto (NCM)
- produtos sem codigo fiscal da operacao (CFOP)
- logs e fechamentos diarios simulados

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
Use o email e a senha definidos no `.env`:

INITIAL_ADMIN_EMAIL
INITIAL_ADMIN_PASSWORD
```

Por seguranca, a tela de login nao mostra credenciais de exemplo.

## Testar filtro por horario

No menu `Operacoes`, use:

```text
Marketplace: Amazon ou Shopee
Horario inicial: 08:00
Horario final: 18:00
```

Esse filtro usa o campo `order_datetime` das operacoes simuladas.

## Emitir NF-e simulada

1. Acesse `Operacoes`.
2. Abra uma operacao.
3. Clique em `Validar fiscal`.
4. Clique em `Emitir NF-e simulada`.
5. Clique em `Gerar XML/PDF`.
6. Baixe os arquivos pela tela da operacao ou por `Documentos fiscais`.

Os arquivos ficam em:

```text
storage/invoices/xml
storage/invoices/pdf
```

Ao clicar em `Baixar XML` ou `Baixar PDF`, o sistema gera um arquivo com corpo e finalidade:

- finalidade do documento de teste;
- aviso de que nao possui validade fiscal;
- dados da operacao simulada;
- comprador e endereco simulados;
- itens;
- valores simulados;
- status fiscal simulado;
- motivo de rejeicao simulada, quando existir.

O PDF usa um modelo visual inspirado em DANFE para teste operacional. Ele tem quadros, cabecalho, destinatario, valores, produtos e informacoes adicionais. O arquivo real usado como referencia visual nao e copiado para dentro do projeto e nenhum dado real dele e reaproveitado.

No Windows local, uma copia tambem e salva em:

```text
C:\Users\REDFIT\Downloads\controle-marketplace-fiscal-teste
```

## Gerar operacoes simuladas agora

1. Acesse `Administracao`.
2. Clique em `Gerar operacoes simuladas`.

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
- listagem de operacoes
- filtro por horario
- validacao fiscal simulada
- emissao de NF-e simulada
- geracao de XML/PDF
- indicadores e CSV

## Seguranca implementada

Este MVP e de portfolio/demo tecnica, mas ja possui uma base de seguranca mais seria:

- senha inicial do admin via variaveis de ambiente, sem senha publica hardcoded;
- tela de login sem usuario/senha de exemplo;
- politica minima de senha para o admin demo criado pelo seed;
- protecao CSRF em formularios;
- cookies de sessao `HttpOnly`, `SameSite=Lax` e `Secure` em producao;
- expiracao de CSRF e sessao permanente com tempo controlado;
- limite de tentativas de login com bloqueio temporario;
- bloqueio de redirect externo no parametro `next`;
- headers de seguranca: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy e HSTS em producao;
- logs de auditoria para login, falha de login, logout e acoes operacionais.

Para virar autenticacao de produto real, os proximos passos naturais seriam recuperacao de senha, troca de senha pelo usuario, 2FA opcional e armazenamento do rate limit em Redis/PostgreSQL em vez de memoria do processo.

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
- migrations no comando de start;
- seed inicial automatico apenas se o banco ainda nao tiver usuario cadastrado.

No Render:

1. Faça push para o GitHub.
2. Acesse `New > Blueprint`.
3. Conecte o repositório `castrokf/controle_fiscal`.
4. Selecione o arquivo `render.yaml` na raiz.
5. O Blueprint ja define o acesso demo:
   - `INITIAL_ADMIN_EMAIL`: `admin@teste.com`;
   - `INITIAL_ADMIN_PASSWORD`: `Teste1234`.
6. Clique em `Deploy Blueprint`.

Configuracao usada pelo Blueprint:

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python -m flask --app run.py deploy && gunicorn run:app --bind 0.0.0.0:$PORT
```

Variaveis de ambiente principais:

```env
SECRET_KEY=gerada automaticamente pelo Render
DATABASE_URL=ligada automaticamente ao PostgreSQL do Render
INITIAL_ADMIN_EMAIL=admin@teste.com
INITIAL_ADMIN_PASSWORD=Teste1234
ENABLE_AUTO_SEED=true
AUTO_GENERATE_FAKE_ORDERS=false
FAKE_ORDER_INTERVAL_MINUTES=10
LOCAL_DOWNLOAD_COPY_ENABLED=false
```

O comando `deploy` aplica migrations e executa o seed inicial somente quando o banco ainda nao possui usuario. Isso evita apagar dados em reinicios do servico.

Se `INITIAL_ADMIN_EMAIL` ou `INITIAL_ADMIN_PASSWORD` estiverem ausentes, o sistema usa os valores demo `admin@teste.com` e `Teste1234`. Se estiverem invalidos, o deploy registra um aviso no log, mas o Web Service continua subindo.

Se precisar rodar manualmente no Shell do Render:

```bash
python -m flask --app run.py deploy
```

Para criar ou redefinir o usuario administrador sem apagar dados:

```bash
python -m flask --app run.py reset-admin
```

Esse comando usa `INITIAL_ADMIN_EMAIL` e `INITIAL_ADMIN_PASSWORD` configurados no Environment do Render. Para o demo atual, use `admin@teste.com` e `Teste1234`.

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
