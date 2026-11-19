# Fornace — React JavaScript, Django e SQL

Sistema acadêmico de pedidos, salão, cozinha e acompanhamento da produção. O frontend usa **React com JavaScript e JSX**. O backend usa **Django**, organizado em modelos, formulários, views baseadas em classes, rotas e painel administrativo, seguindo o padrão do [blog-django-crud](https://github.com/arthurfran/blog-django-crud).

O banco local é **SQLite**. O deploy no Render utiliza **PostgreSQL** e serve o React compilado, a API e o Django Admin no mesmo endereço. A execução local usa dois terminais; o projeto não inclui Docker nem suíte de testes automatizados.

O layout, o cardápio e as imagens do Fornace foram preservados. O modelo de negócio mantém **9 entidades, 57 atributos e 9 relacionamentos**, com PK e FK distintas, perfis acumuláveis e responsável de cozinha por item do pedido.

## Executar pela primeira vez

Requisitos: Python 3.12 ou superior e Node.js 22.17 ou superior. Extraia o ZIP e abra um terminal na pasta `Fornace`, onde está este README. SQLite acompanha o Python.

### Terminal 1 — backend no Windows / PowerShell

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.venv\Scripts\python.exe backend/manage.py migrate
.venv\Scripts\python.exe backend/manage.py seed_demo
.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
```

O comando `seed_demo` pede uma senha de 8 a 64 caracteres. Ela será utilizada nas contas demonstrativas criadas nessa execução. O terminal não exibe os caracteres digitados. A carga cria mesas, categorias, pratos e equipe, sem pedidos ou vendas fictícias.

### Terminal 1 — alternativa para Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py seed_demo
.venv/bin/python backend/manage.py runserver 127.0.0.1:8000
```

### Terminal 2 — frontend

Abra outro terminal na pasta `Fornace`:

```bash
cd frontend
npm ci
npm run dev
```

Acesse **http://127.0.0.1:5173**. Mantenha os dois terminais abertos. Se o Vite usar outra porta porque a 5173 está ocupada, use o endereço informado no terminal.

Em execuções seguintes, basta iniciar o backend e executar `npm run dev` no frontend. Não é necessário recriar o ambiente nem repetir a carga. Para encerrar cada servidor, use `Ctrl+C`.

## Contas e perfis

Na tela de entrada, selecione **Sou da equipe** e use a senha definida no `seed_demo`.

| Login | Acesso |
| --- | --- |
| `admin` | Administração de usuários e Django Admin |
| `teo`, `iara` | Garçom, inicialmente em escala |
| `marina` | Operadora de cozinha com análises gerenciais |
| `caio` | Operador de cozinha |
| `duplo` | Garçom e operador na mesma conta |

O administrador pode ter nenhum, um ou ambos os perfis operacionais. Ser administrador, por si só, não permite preparar ou entregar pedidos. Clientes podem se cadastrar ou continuar como anônimos, sempre vinculando o pedido a uma mesa.

O `seed_demo` preserva contas e senhas existentes. Para criar outro administrador ou trocar uma senha, execute, com o Python do ambiente virtual:

```bash
python backend/manage.py createsuperuser
python backend/manage.py changepassword admin
```

Se não tiver ativado o ambiente, substitua `python` por `.venv\Scripts\python.exe` no Windows ou `.venv/bin/python` no Linux/macOS, como nos comandos anteriores.

## Painel administrativo

Entre como `admin` no React e clique em **Cadastros Django**. Também é possível acessar **http://127.0.0.1:5173/admin/** e entrar com a mesma conta.

O painel permite cadastrar e editar usuários, perfis, mesas, categorias e itens do cardápio. Pedidos, itens de pedidos e clientes ficam disponíveis para consulta. Preparo e entrega continuam nas telas operacionais do React, que aplicam as regras do fluxo.

O frontend encaminha `/api/`, `/admin/` e `/static/` ao Django. Assim, React e painel compartilham a sessão. O endereço direto **http://127.0.0.1:8000/admin/** também funciona; prefira usar o mesmo host durante a demonstração.

## Organização do código

| Arquivo / diretório | Responsabilidade |
| --- | --- |
| `backend/config/settings.py` | Configuração do Django, autenticação e banco |
| `backend/config/urls.py` | Rotas principais: admin e API |
| `backend/restaurante/models.py` | Entidades, atributos, relacionamentos e comportamento de domínio |
| `backend/restaurante/forms.py` | `Form` e `ModelForm`: validação e cadastros |
| `backend/restaurante/views.py` | Views baseadas em classes e respostas JSON |
| `backend/restaurante/urls.py` | Endpoints de cada caso de uso |
| `backend/restaurante/mixins.py` | Acesso às views por perfil |
| `backend/restaurante/admin.py` | Cadastros e consultas do Django Admin |
| `backend/restaurante/services.py` | Fluxos de carrinho, atribuição, preparo e entrega |
| `backend/restaurante/domain.py` | Cálculo de totais e política de atribuição automática |
| `backend/restaurante/migrations/` | Evolução do esquema SQL |
| `frontend/src/pages/` | Telas React em `.jsx` |
| `frontend/src/components/` | Componentes compartilhados |
| `frontend/src/api.js` | Cliente HTTP, sessão, CSRF e mensagens de erro |
| `frontend/src/hooks.js` | Hooks reutilizáveis |

O Django mantém orientação a objetos por modelos, formulários, views, mixins e serviços. O React utiliza componentes funcionais e hooks. Nenhum arquivo da aplicação usa TypeScript.

## Atualizar a versão anterior

Para preservar um banco SQLite da entrega anterior:

1. Encerre os servidores e faça uma cópia de segurança do antigo `backend/db.sqlite3`.
2. Extraia esta versão em outra pasta e copie o banco antigo para o novo `backend/db.sqlite3`.
3. Instale as dependências e execute `migrate`, conforme as instruções de instalação.
4. Execute `npm ci` no novo frontend e reinicie os servidores. Entre novamente na conta.

Não apague o banco nem as migrações. As migrações iniciais foram preservadas. A integração de `Usuario` com a autenticação do Django mantém a coluna física `senha_hash`, os identificadores e os relacionamentos. O nome do atributo no ORM passa a ser `password`, com `db_column="senha_hash"`.

## PostgreSQL opcional

Para a apresentação acadêmica, SQLite é suficiente e não exige um servidor separado. Para usar um PostgreSQL já instalado, crie um banco vazio e um usuário com acesso a ele; depois, instale as dependências opcionais e defina `DATABASE_URL` no terminal do backend:

```powershell
.venv\Scripts\python.exe -m pip install -r backend/requirements-postgres.txt
$env:DATABASE_URL = "postgresql://usuario:senha@127.0.0.1:5432/fornace"
.venv\Scripts\python.exe backend/manage.py migrate
.venv\Scripts\python.exe backend/manage.py seed_demo
.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
```

No Linux/macOS, use `export DATABASE_URL='postgresql://usuario:senha@127.0.0.1:5432/fornace'` e o executável `.venv/bin/python`. Substitua as credenciais; caracteres especiais na URL precisam de codificação apropriada. A variável vale para aquele terminal. A aplicação não carrega arquivos `.env` automaticamente.

Mudar de SQLite para PostgreSQL **não transfere os dados existentes**. Este procedimento configura uma instalação nova. Para retornar ao SQLite, remova a variável `DATABASE_URL` antes de iniciar o backend.

O painel de análises lê a view SQL `cubo_producao`. Nos dois bancos, pedidos entregues aparecem nas próximas consultas sem um processo de atualização separado.

## Publicar no GitHub e no Render

Confira o [guia de publicação](docs/RENDER.md). O `render.yaml` cria um serviço web e um PostgreSQL exclusivos do Fornace. A configuração local continua conforme os passos acima.

## Documentação e conferência

- [Arquitetura, regras e correspondência com os casos de uso](docs/ARQUITETURA_E_REGRAS.md)
- [Entidades e atributos do DER implementado](docs/DER_IMPLEMENTADO.md)
- [Rotas e contratos da API](docs/API.md)
- [Roteiro de demonstração e verificações da versão](docs/GUIA_DEMONSTRACAO.md)

Para conferir a configuração e gerar o frontend compilado, usando o ambiente Python do projeto:

```bash
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
cd frontend
npm run build
```

Esses comandos verificam configuração, consistência das migrações e compilação. `npm run dev` é o modo indicado para a apresentação local; o serviço do Render publica o build e a API juntos.

## Configurações opcionais

| Variável | Padrão / efeito |
| --- | --- |
| `DATABASE_URL` | Ausente: SQLite local; presente: conexão indicada |
| `SQLITE_PATH` | `backend/db.sqlite3`; permite outro arquivo local |
| `SLA_PREPARO_MIN` | 18; intervalo permitido de 6 a 40 |
| `SLA_ENTREGA_MIN` | 0: meta de entrega não definida |
| `CAPACIDADE_PEDIDOS_HORA` | 0: capacidade não definida |
| `VITE_API_PROXY` | `http://127.0.0.1:8000`; endereço do backend no terminal do Vite |

O projeto vem configurado para desenvolvimento local. Pagamentos, estoque, reservas e histórico de escalas não fazem parte do escopo implementado.
