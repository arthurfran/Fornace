# Publicação do Fornace

O Render hospeda um único serviço web Python. O build compila o frontend em JavaScript com Vite, instala o backend e coleta os arquivos do Django Admin. O serviço publica o cardápio em `/`, a API em `/api/` e o admin em `/admin/`. O banco PostgreSQL é separado; o SQLite local continua em `backend/db.sqlite3`.

## 1. GitHub

Crie um repositório **privado** chamado `fornace` no seu GitHub. Se for iniciar de um ZIP, deixe o repositório remoto vazio (sem README, licença ou .gitignore gerados). Abra a pasta `Fornace` que contém `render.yaml` e, usando Git no terminal, execute:

```powershell
git init -b main
git add .
git diff --cached --stat
git commit -m "Publica o Fornace com configuração para Render"
git remote add origin https://github.com/SEU_USUARIO/fornace.git
git push -u origin main
```

Se o projeto já estiver em Git, use a branch `main`, confira `git remote -v` e pule a inicialização e a criação de `origin` quando já estiverem corretas. O repositório deve conter o código, imagens do cardápio, migrações, arquivos de dependência e `render.yaml`. O `.gitignore` exclui banco local, segredos, dependências instaladas e arquivos gerados.

## 2. Render

1. No [painel do Render](https://dashboard.render.com/), escolha **New → Blueprint**.
2. Conecte o GitHub e dê ao Render acesso ao repositório `fornace`. Se o repositório privado não aparecer, inclua-o nos repositórios autorizados da integração do Render.
3. Selecione o repositório, a branch `main` e o arquivo `render.yaml`.
4. Confira os recursos propostos: serviço web `fornace-app` e banco `fornace-postgres`, ambos **Free** e na mesma região. Confirme que são recursos novos do Fornace.
5. Acione **Deploy Blueprint** e acompanhe o log até o serviço ficar disponível.

| Campo | Valor |
| --- | --- |
| Runtime | Python, configurado por `.python-version` |
| Diretório raiz | Raiz do repositório |
| Build | `bash scripts/render-build.sh` |
| Start | `bash scripts/render-start.sh` |
| Health check | `/api/saude/` |
| Banco | `DATABASE_URL` vinculada à conexão interna de `fornace-postgres` |
| Chave Django | `SECRET_KEY` gerada pelo Render |
| Senhas iniciais | `ADMIN_PASSWORD` e `DEMO_PASSWORD`, geradas separadamente no Render |

O PostgreSQL gratuito expira em 30 dias e o Render permite um banco gratuito ativo por workspace. Se o banco de outro projeto ocupar essa vaga, use outro workspace que possa criar o banco gratuito ou configure uma conexão PostgreSQL exclusiva para o Fornace. Não troque a conexão nem exclua o banco do blog. Sempre confira o plano antes de criar recursos. A implantação começa com dados de demonstração, sem importar clientes ou pedidos do SQLite local.

### Se já houver um PostgreSQL próprio para o Fornace

É possível criar somente o **Web Service** em vez de usar o Blueprint completo. Selecione **Free**, o repositório/branch e os comandos da tabela. No painel **Environment**, configure `DATABASE_URL` com a conexão do banco exclusivo, escolha uma `SECRET_KEY` aleatória de ao menos 32 caracteres e defina duas senhas fortes e distintas de 8 a 64 caracteres em `ADMIN_PASSWORD` e `DEMO_PASSWORD`. Guarde esses valores no Render.

## 3. Primeira abertura

Abra o URL `onrender.com` fornecido pelo Render. Depois de inatividade, o plano Free pode levar algum tempo para acordar. O start aplica as migrações e insere mesas, cardápio e contas demonstrativas. Esses passos podem ser repetidos sem criar pedidos falsos nem trocar senhas existentes.

| Conta | Senha inicial |
| --- | --- |
| `admin` | `ADMIN_PASSWORD` |
| `teo`, `iara`, `marina`, `caio`, `duplo` | `DEMO_PASSWORD` |

As senhas iniciais ficam em **Environment**, no próprio serviço. Para trocar a senha de uma conta criada, edite a conta em **Cadastros Django**; alterar a variável de ambiente não sobrescreve a senha em uso.

Abra o cardápio, entre com a equipe e confira o fluxo mesa → pedido → preparo → entrega → análises. A URL `/api/saude/` retorna `{"status":"ok"}` quando o Django consegue consultar o banco. Nas próximas revisões, envie os commits para `main` e acompanhe o novo deploy.

Referências: [Blueprints do Render](https://render.com/docs/infrastructure-as-code), [Django no Render](https://render.com/docs/deploy-django), [limites dos planos Free](https://render.com/docs/free).
