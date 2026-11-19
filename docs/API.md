# API JSON

Prefixo `/api/`. O navegador usa a mesma origem do frontend. Rotas GET não exigem login quando o conteúdo é público; cada operação protegida valida o perfil no servidor. Erros retornam `{"erro":"mensagem"}` com status HTTP apropriado.

A API usa as views e os formulários nativos do Django. O cliente em `frontend/src/api.js` mantém os cookies e o token CSRF. O painel `/admin/` é HTML gerado pelo Django e compartilha o login da equipe; não é um endpoint JSON.

## Sessão

| Método | Rota | Resultado / acesso |
| --- | --- | --- |
| GET | `contexto/` | Identidade, token CSRF, mesas e garçons elegíveis; inicia sessão anônima |
| POST | `cadastro/` | `nome`, `email`, `senha`; cria cliente e autentica |
| POST | `login/` | `tipo`: `cliente` ou `usuario`; `login` (e-mail do cliente), `senha` |
| POST | `logout/` | Encerra a sessão |
| GET | `saude/` | Verifica conexão com o banco |

POST e PATCH precisam de `Content-Type: application/json`, cookie de sessão e `X-CSRFToken`. Depois de login/cadastro, use o novo token retornado. Os formulários da aplicação aceitam senhas de 8 a 64 caracteres. O frontend usa `credentials: same-origin`.

## Cardápio e carrinho

| Método | Rota | Dados / acesso |
| --- | --- | --- |
| GET | `cardapio/` | Itens e categorias, incluindo disponibilidade |
| PATCH | `cardapio/{id}/disponibilidade/` | `disponivel` booleano; operador |
| GET | `carrinhos/{origem}/` | Carrinho atual; origem `cliente` ou `salao` |
| POST | `carrinhos/{origem}/` | Ação abaixo; `salao` exige garçom |
| POST | `carrinhos/{origem}/confirmar/` | `revisao` e `garcom_id` opcional no autoatendimento |

Ações do carrinho:

```json
{"acao":"mesa","mesa_id":1}
```

```json
{"acao":"adicionar","item_id":1,"quantidade":2,"observacoes":"Sem cebola"}
```

```json
{"acao":"alterar","linha_id":"identificador-retornado-no-carrinho","quantidade":3,"observacoes":"Sem lactose"}
```

```json
{"acao":"remover","linha_id":"identificador-retornado-no-carrinho"}
```

```json
{"acao":"limpar"}
```

A resposta contém `revisao`, `mesa_id`, `linhas`, `subtotal`, `servico` e `total`. Confirme com a revisão mais recente. Preços e totais são strings decimais no JSON para preservar precisão. `garcom_id: null` seleciona atribuição automática. No salão, o servidor utiliza o próprio garçom autenticado.

## Operação

| Método | Rota | Dados / acesso |
| --- | --- | --- |
| GET | `pedidos/?visao=cliente` | Pedidos do cliente ou da sessão anônima |
| GET | `pedidos/?visao=salao` | Pedidos do garçom autenticado |
| GET | `pedidos/?visao=cozinha` | Todos os pedidos; operador |
| GET | `pedidos/?visao=monitor` | Todos os pedidos; operador, visão de salão |
| PATCH | `itens/{id}/preparo/` | `situacao`: `AGUARDANDO`, `EM_PREPARO` ou `PRONTO`; operador responsável |
| POST | `pedidos/{id}/entregar/` | Corpo `{}`; garçom atribuído |
| PATCH | `escala/` | `em_escala` booleano; próprio garçom |

Por padrão, a consulta lista pedidos ativos. `historico=1` retorna entregues. A paginação retorna até 100 pedidos, `mais` e `antes`; envie o identificador de `antes` na próxima consulta. Pedidos concluídos são preservados.

A alteração de preparo não recebe um operador arbitrário: o servidor utiliza o usuário autenticado. A confirmação de entrega também não recebe `garcom_id`.

## Administração

`GET usuarios/`, `POST usuarios/` e `PATCH usuarios/{id}/` exigem administrador. O formulário envia o objeto completo no cadastro/edição. Na edição, senha vazia mantém a atual.

```json
{
  "nome":"Pessoa da equipe",
  "login":"equipe01",
  "senha":"exemplo-somente-documentacao",
  "ativo":true,
  "administrador":false,
  "garcom":{"setor":"Salão","em_escala":true},
  "operador":{"funcao":"Preparo","perfil_gerencial":false}
}
```

Os dados são validados pelo mesmo `UsuarioForm` utilizado no Django Admin. Use `null` no perfil que não existir. Perfis referenciados não podem ser removidos. Desativar uma conta com pendências operacionais é rejeitado. Para administrador sem perfis, use `administrador: true` e ambos os perfis nulos.

## Indicadores

`GET analise/?dias=30` exige operador com perfil gerencial. Períodos permitidos: 7, 30 ou 90. Filtros opcionais `categoria` e `turno` retornam o recorte da matriz. A resposta inclui totais, médias, variações, matriz, ranking, curva por hora, volume semanal e até 100 pedidos detalhados do recorte. Sem dados ou configuração para um indicador, o campo correspondente fica nulo.
