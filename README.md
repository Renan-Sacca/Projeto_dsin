# 💇‍♀️ Cabeleleila Leila — Sistema de Agendamento

## 🛠 Stack Tecnológica

### Backend

| Tecnologia | Versão | Para que serve |
|-----------|--------|---------------|
| **[FastAPI](https://fastapi.tiangolo.com/)** | 0.115.0 | Framework web Python moderno e rápido. Gera documentação automática (Swagger) em `/docs`. Usa tipagem e async. |
| **[SQLAlchemy](https://www.sqlalchemy.org/)** | 2.0.35 | ORM (Object Relational Mapper) — mapeia classes Python para tabelas do banco de dados. Permite fazer queries sem escrever SQL puro. |
| **[Pydantic](https://docs.pydantic.dev/)** | 2.9.2 | Validação de dados. Define schemas (contratos) para dados de entrada e saída da API. Garante que os dados estão no formato correto. |
| **[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** | 2.5.2 | Carrega variáveis de ambiente do arquivo `.env` para configurações da aplicação. |
| **[python-jose](https://python-jose.readthedocs.io/)** | 3.3.0 | Gera e decodifica tokens JWT (JSON Web Token) para autenticação. |
| **[Passlib](https://passlib.readthedocs.io/) + bcrypt** | 1.7.4 | Faz hash seguro de senhas usando algoritmo bcrypt. Nunca armazena senhas em texto claro. |
| **[Uvicorn](https://www.uvicorn.org/)** | 0.30.6 | Servidor ASGI que roda a aplicação FastAPI. Suporta hot-reload em desenvolvimento. |
| **[SQLite](https://www.sqlite.org/)** | (embutido) | Banco de dados relacional em arquivo. Não precisa de servidor separado. Perfeito para projetos pequenos/médios. |

### Frontend

| Tecnologia | Versão | Para que serve |
|-----------|--------|---------------|
| **[Jinja2](https://jinja.palletsprojects.com/)** | 3.1.4 | Motor de templates HTML. Permite usar variáveis Python dentro do HTML. FastAPI renderiza os templates no servidor. |
| **[Bootstrap 5](https://getbootstrap.com/)** | 5.3.3 | Framework CSS para interface responsiva. Fornece componentes prontos (botões, tabelas, modais, etc.). |
| **[Bootstrap Icons](https://icons.getbootstrap.com/)** | 1.11.3 | Biblioteca de ícones SVG do Bootstrap. |
| **JavaScript (Fetch API)** | ES6+ | Faz requisições AJAX para a API sem recarregar a página. Manipula a interface dinamicamente. |

### Infraestrutura

| Tecnologia | Para que serve |
|-----------|---------------|
| **[Docker](https://www.docker.com/)** | Empacota a aplicação em um container isolado com todas as dependências. |
| **[Docker Compose](https://docs.docker.com/compose/)** | Orquestra os containers. Define serviços, volumes e redes em um arquivo YAML. |



## 🚀 Como Rodar

### Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e **rodando**

### Subir o projeto

```bash
cd "Projeto dsin"
docker-compose up --build
```

A aplicação estará disponível em: **http://localhost:8000**

### Parar o projeto

```bash
docker-compose down
```


### Acessar a documentação automática da API

- **Swagger UI**: http://localhost:8000/docs

## 🔑 Credenciais Padrão

| Tipo | Email | Senha |
|------|-------|-------|
| **Administrador** | `admin@admin.com` | `admin123` |
| **Cliente** | *(crie pelo formulário de cadastro)* | — |

O admin padrão é criado automaticamente ao iniciar o sistema pela primeira vez, para trocar o usuario admin, altere no .env

---

## 🏗 Arquitetura do Sistema

O projeto segue o padrão de **Arquitetura em Camadas** (Layered Architecture), onde cada camada tem uma responsabilidade específica e só se comunica com a camada adjacente:

```
┌─────────────────────────────────────────────────┐
│                   FRONTEND                       │
│         (Templates Jinja2 + Bootstrap 5)         │
│         (JavaScript com Fetch API)               │
└──────────────────────┬──────────────────────────┘
                       │ HTTP Requests
┌──────────────────────▼──────────────────────────┐
│                   ROUTERS                        │
│         (Endpoints da API REST)                  │
│         Recebe requests, retorna responses       │
│         NÃO contém lógica de negócio             │
└──────────────────────┬──────────────────────────┘
                       │ Chama
┌──────────────────────▼──────────────────────────┐
│               DEPENDENCIES                       │
│         (Autenticação / Autorização)             │
│         Extrai e valida JWT token                │
│         Verifica tipo de usuário                 │
└──────────────────────┬──────────────────────────┘
                       │ Injeta user
┌──────────────────────▼──────────────────────────┐
│                  SERVICES                        │
│         (Regras de Negócio)                      │
│         Conflito de horário, regra 2 dias        │
│         Fluxo de aprovação, permissões           │
└──────────────────────┬──────────────────────────┘
                       │ Chama
┌──────────────────────▼──────────────────────────┐
│               REPOSITORIES                       │
│         (Acesso ao Banco de Dados)               │
│         Queries SQLAlchemy, CRUD                 │
└──────────────────────┬──────────────────────────┘
                       │ SQL
┌──────────────────────▼──────────────────────────┐
│                  DATABASE                        │
│              (SQLite via SQLAlchemy)              │
└─────────────────────────────────────────────────┘
```

**Por que essa separação?**

- **Routers** (controllers) são finos — não têm lógica, só recebem dados e chamam services
- **Services** concentram TODAS as regras de negócio — fácil de testar e manter
- **Repositories** isolam as queries — se trocar o banco, só muda aqui
- **Models** definem a estrutura do banco — independentes de tudo
- **Schemas** definem contratos da API — validação automática

---

## 📂 Estrutura de Pastas e Arquivos

```
Projeto dsin/
│
├── 📄 Dockerfile                    # Imagem Docker
├── 📄 docker-compose.yml            # Orquestração dos containers
├── 📄 requirements.txt              # Dependências Python
├── 📄 .env                          # Variáveis de ambiente
├── 📄 .dockerignore                 # Arquivos ignorados pelo Docker
├── 📄 README.md                     # Este arquivo
│
├── 📁 app/                          # ← CÓDIGO DA APLICAÇÃO
   ├── 📄 __init__.py               # Marca 'app' como pacote Python
   ├── 📄 main.py                   # Ponto de entrada do FastAPI
   │
   ├── 📁 core/                     # Configurações centrais
   │   ├── 📄 __init__.py
   │   ├── 📄 config.py             # Settings do .env (pydantic-settings)
   │   └── 📄 security.py           # JWT + bcrypt (hash/verify/token)
   │
   ├── 📁 database/                 # Camada de banco de dados
   │   ├── 📄 __init__.py
   │   ├── 📄 base.py               # Base declarativa do SQLAlchemy
   │   ├── 📄 connection.py         # Engine, SessionLocal, get_db()
   │   └── 📄 seed.py               # Dados iniciais (admin + config)
   │
   ├── 📁 models/                   # Modelos SQLAlchemy (tabelas)
   │   ├── 📄 __init__.py           # Exporta todos os modelos
   │   ├── 📄 user.py               # User (id, nome, email, senha, tipo)
   │   ├── 📄 client.py             # Client (user_id, telefone)
   │   ├── 📄 service.py            # Service (nome, duração, preço)
   │   ├── 📄 appointment.py        # Appointment + AppointmentService
   │   └── 📄 system_config.py      # SystemConfig (auto_approve)
   │
   ├── 📁 schemas/                  # Schemas Pydantic (validação)
   │   ├── 📄 __init__.py
   │   ├── 📄 user.py               # UserCreate, UserLogin, TokenResponse
   │   ├── 📄 client.py             # ClientResponse, ClientUpdate
   │   ├── 📄 service.py            # ServiceCreate, ServiceUpdate, Response
   │   ├── 📄 appointment.py        # AppointmentCreate, DashboardMetrics
   │   └── 📄 system_config.py      # ConfigUpdate, ConfigResponse
   │
   ├── 📁 repositories/            # Acesso ao banco (queries)
   │   ├── 📄 __init__.py
   │   ├── 📄 user_repository.py    # CRUD de User
   │   ├── 📄 client_repository.py  # CRUD de Client (com joinedload)
   │   ├── 📄 service_repository.py # CRUD de Service
   │   ├── 📄 appointment_repository.py # Conflitos, métricas, receita
   │   └── 📄 system_config_repository.py # Get/Update config
   │
   ├── 📁 services/                 # Regras de negócio
   │   ├── 📄 __init__.py
   │   ├── 📄 auth_service.py       # Registro e login
   │   ├── 📄 user_service.py       # Busca/lista usuários
   │   ├── 📄 client_service.py     # CRUD clientes + soft delete
   │   ├── 📄 service_service.py    # CRUD serviços + soft delete
   │   ├── 📄 appointment_service.py # ★ Coração do sistema ★
   │   └── 📄 system_config_service.py # Toggle aprovação
   │
   ├── 📁 routers/                  # Endpoints da API
   │   ├── 📄 __init__.py
   │   ├── 📄 auth.py               # POST /api/auth/register, /login
   │   ├── 📄 clients.py            # GET/PUT /api/clients
   │   ├── 📄 services.py           # GET/POST/PUT /api/services
   │   ├── 📄 appointments.py       # CRUD + approve/reject/cancel
   │   ├── 📄 system_config.py      # GET/PUT /api/config
   │   └── 📄 pages.py              # Rotas HTML (login, dashboard, etc.)
   │
   ├── 📁 dependencies/            # Injeção de dependências
   │   ├── 📄 __init__.py
   │   └── 📄 auth.py               # get_current_user, require_admin
   │
   ├── 📁 templates/               # HTML (Jinja2 + Bootstrap 5)
   │   ├── 📄 base.html             # Layout base (navbar, footer, toasts)
   │   ├── 📄 login.html            # Formulário de login
   │   ├── 📄 register.html         # Formulário de cadastro
   │   ├── 📁 client/               # Páginas do cliente
   │   │   ├── 📄 dashboard.html    # Painel c/ resumo de agendamentos
   │   │   ├── 📄 new_appointment.html # Solicitar novo agendamento
   │   │   ├── 📄 my_appointments.html # Lista de agendamentos
   │   │   └── 📄 edit_appointment.html # Editar agendamento
   │   └── 📁 admin/                # Páginas do administrador
   │       ├── 📄 dashboard.html    # Dashboard com métricas
   │       ├── 📄 appointments.html # Gerenciar agendamentos
   │       ├── 📄 clients.html      # Gerenciar clientes
   │       ├── 📄 services.html     # Gerenciar serviços
   │       └── 📄 settings.html     # Configurações do sistema
   │
   └── 📁 static/                  # Arquivos estáticos
       ├── 📁 css/
       │   └── 📄 style.css         # Design
       └── 📁 js/
           └── 📄 app.js            # logica de front


```
## 📂 Estrutura dos model

Cada model é uma classe Python que mapeia para uma tabela no SQLite via **SQLAlchemy ORM**:

#### `app/models/user.py` — Tabela `users`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | Integer (PK) | Identificador único |
| `nome` | String | Nome completo |
| `email` | String (unique) | Email de login |
| `senha_hash` | String | Hash bcrypt da senha |
| `tipo` | Enum (CLIENT/ADMIN) | Tipo de usuário para RBAC |
| `ativo` | Boolean | Soft delete (True = ativo) |
| `criado_em` | DateTime | Auto-preenchido na criação |
| `atualizado_em` | DateTime | Auto-preenchido na atualização |

#### `app/models/client.py` — Tabela `clients`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | Integer (PK) | Identificador |
| `user_id` | Integer (FK → users) | Vínculo com o usuário |
| `telefone` | String | Telefone de contato |

**Por que separar User e Client?** O User armazena dados de autenticação (email, senha, tipo). O Client armazena dados específicos do perfil de cliente (telefone, agendamentos). Um Admin é User sem Client.

#### `app/models/service.py` — Tabela `services`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | Integer (PK) | Identificador |
| `nome` | String | Nome do serviço |
| `descricao` | Text | Descrição detalhada |
| `duracao_minutos` | Integer | Duração em minutos |
| `preco` | Float | Preço em reais |
| `ativo` | Boolean | Soft delete |

#### `app/models/appointment.py` — Tabelas `appointments` e `appointment_services`

**Tabela `appointments`:**

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | Integer (PK) | Identificador |
| `client_id` | Integer (FK → clients) | Quem agendou |
| `data_hora` | DateTime | Data e hora do agendamento |
| `status` | Enum | PENDING, APPROVED, REJECTED, CANCELLED, COMPLETED |
| `criado_por` | Integer (FK → users) | Quem criou |
| `aprovado_por` | Integer (FK → users, nullable) | Quem aprovou/rejeitou (**auditoria**) |
| `data_aprovacao` | DateTime (nullable) | Quando foi aprovado/rejeitado (**auditoria**) |

**Tabela `appointment_services`** (associativa N:N):

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `appointment_id` | FK → appointments | Agendamento |
| `service_id` | FK → services | Serviço |

Um agendamento pode ter **múltiplos serviços** (ex: Corte + Escova + Manicure).

#### `app/models/system_config.py` — Tabela `system_config`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | Integer (PK) | Registro único |
| `auto_approve_appointments` | Boolean | Se True, agendamentos são aprovados automaticamente |


## 🔄 Fluxo de Agendamento

```
Cliente solicita agendamento
        │
        ▼
Valida serviços (existem? ativos?)
        │
        ▼
Valida data (é no futuro?)
        │
        ▼
Verifica SystemConfig.auto_approve
        │
   ┌────┴────┐
   │         │
   ▼         ▼
AUTO=true  AUTO=false
   │         │
   ▼         ▼
Verifica   Status:
conflito   PENDING
   │         │
   ▼         ▼
Sem         Admin
conflito?   analisa
   │         │
   ▼    ┌────┴────┐
Status: │         │
APPROVED▼         ▼
      Aprovar   Rejeitar
        │         │
        ▼         ▼
     Verifica   Status:
     conflito   REJECTED
        │
        ▼
     Sem conflito?
        │
        ▼
     Status:
     APPROVED
```

---

## ⚙ Regras de Negócio

### 1. Conflito de Horário
- Dois agendamentos **APPROVED** não podem se sobrepor
- A verificação considera a **duração total** dos serviços selecionados
- Múltiplos agendamentos **PENDING** no mesmo horário são permitidos
- O conflito é verificado **na criação** (se auto-approve) e **na aprovação** (pelo admin)

### 2. Regra dos 2 Dias
- **Cliente** NÃO pode editar/cancelar um agendamento se faltam **menos de 2 dias** para a data/hora
- **Admin** pode editar/cancelar **sempre**, independente da data

### 3. Aprovação Automática vs Manual
- Configurável via `/admin/settings` (toggle)
- **Manual** (padrão): agendamento inicia como PENDING → admin precisa aprovar
- **Automática**: agendamento inicia como APPROVED (se não houver conflito)

### 4. Soft Delete
- Clientes e serviços **nunca são deletados** do banco
- São **desativados** (campo `ativo = False`)
- Preserva integridade referencial e histórico

### 5. Permissões (RBAC)
- **Cliente** só acessa seus próprios dados
- **Admin** Acessa tudo
- **Staff** Acessa dados de gestão e agendamentos, não tem controle sobre outros membros staff.


### 6. Segurança.
- **Proteção contra SQL Injection:** 100% das consultas utilizam o motor ORM do SQLAlchemy com parametrização automática, eliminando riscos de comandos maliciosos via inputs.
- **Sanitização XSS:** Implementada camada de sanitização automática em todos os Schemas Pydantic (User/Client), convertendo caracteres perigosos em entidades seguras (`html.escape`) antes de chegarem ao banco.
- **Auditoria Completa:** Todo agendamento aprovado ou rejeitado registra o ID do administrador responsável e a data exata da ação.
- **Janela de Segurança:** Regra de negócio que impede clientes de alterarem agendamentos com menos de 48h de antecedência.

---

## ✨ Funcionalidades Adicionadas

### 📅 Sugestão Inteligente de Combo Semanal
Ao solicitar um novo agendamento, o sistema verifica automaticamente se o cliente já possui outra marcação na mesma semana. Caso positivo, um **Modal de Alerta** sugere que o cliente aproveite a viagem para realizar todos os serviços no mesmo dia, otimizando a agenda do salão e o tempo do cliente.

### 📊 Dashboard Dinâmico e Receita Potencial
O dashboard administrativo agora é totalmente interativo:
- **Filtros Cruzados:** Filtre por data, serviço ou status e veja o gráfico de receita se atualizarem simultaneamente.
- **Potencial de Receita:** Uma métrica inteligente que soma agendamentos Pendentes + Aprovados para mostrar quanto o salão pode faturar no período selecionado.

### 🔍 Gestão Avançada de Clientes
- **Busca em Tempo Real:** Localize clientes instantaneamente por nome ou e-mail sem recarregar a página.
- **Paginação Inteligente:** Interface preparada para grandes volumes de dados, com navegação fluida entre páginas de registros.

### 🌐 Integração Google Calendar
- **Sincronização Bidirecional:** Agendamentos aprovados podem ser enviados automaticamente para o Google Calendar do Administrador e do Cliente.
- **Login Social:** Suporte a OAuth2 para integração segura com contas Google.


---

## 🛠 Ferramentas de Automação

### Reset Inteligente do Sistema (`cleanup_db.py`)
Para facilitar demonstrações, tem o script de "Reset Total" que:
1. Limpa todo o histórico de agendamentos e clientes.
2. Gera **15 clientes aleatórios** com dados realistas.
3. Cria **30 agendamentos estratégicos** distribuídos nos próximos 7 dias.
4. **Detector de Conflitos:** O script calcula a duração total de cada serviço e garante que os agendamentos gerados não se sobreponham, criando uma agenda realista e organizada.

**Como usar:**
```bash
docker exec cabeleleila-leila python cleanup_db.py
```

---


### Observações:

-- Era ideal ter agendamentos por funcionarios, para ampliar a rede caso o estabelecimento cresça, e possa atender mais de um cliente, porem não ira dar tempo de fazer nessa entrega.
-- As tecnologias utilizadas em sua maioria são as que trabalho hoje no serviço atual.
-- O projeto esta rodando, online e disponível em: https://
