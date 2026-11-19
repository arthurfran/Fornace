# Arquitetura e regras do Fornace

## Estrutura baseada no projeto de referência

A organização adota os elementos usados no [blog-django-crud](https://github.com/arthurfran/blog-django-crud): projeto `config`, aplicação Django, modelos ORM, formulários, views baseadas em classes, rotas separadas e Django Admin. O domínio permanece o restaurante Fornace e a interface operacional permanece em React.

| Elemento | Aplicação no Fornace |
| --- | --- |
| `models.Model` | Entidades do DER e restrições do banco |
| `AbstractBaseUser` | `Usuario`, integrado à autenticação e ao admin |
| `forms.Form` | Validação de login, carrinho, preparo, escala e disponibilidade |
| `forms.ModelForm` | Cadastro de usuários, clientes, mesas, categorias e cardápio |
| `ListView` | Listagem JSON do cardápio e dos usuários |
| `View` | Operações específicas dos casos de uso, recebendo JSON do React |
| `LoginRequiredMixin`, `UserPassesTestMixin` | Acesso por perfil, com resposta JSON nas rotas da API |
| `ModelAdmin` | Cadastro de dados básicos e consulta dos pedidos |
| `urls.py` | Separação das rotas gerais e das rotas da aplicação |

As views recebem a requisição, os formulários validam os dados e os serviços coordenam as entidades em transações. `serializers.py` monta os dicionários JSON; não utiliza Django REST Framework. O React usa componentes funcionais, hooks e a classe `ApiClient`, todos em JavaScript.

## DER e perfis

- `USUARIO` representa a conta da equipe. `GARCOM` e `OPERADOR_COZINHA` são perfis opcionais e acumuláveis. Cada perfil possui PK própria e FK única para o usuário.
- `administrador` habilita gestão de usuários e Django Admin. Preparo, entrega e análises exigem os respectivos perfis, mesmo para um administrador.
- `CLIENTE` permanece separado da equipe. No autoatendimento anônimo, `PEDIDO.id_cliente` fica nulo e a mesa é obrigatória. O acesso ao pedido pertence à sessão que o criou.
- `ITEM_PEDIDO.id_operador` aceita nulo até o primeiro início. Depois, o responsável é mantido inclusive em correções. Outro operador não pode assumir essa linha.
- Não existe `HISTORICO_SITUACAO`: estados e marcos ficam em `PEDIDO` e `ITEM_PEDIDO`. Não há autor artificial “sistema”.
- Tabelas técnicas do Django, de sessões, permissões, log administrativo, cache e migrações não alteram as nove entidades do DER de negócio. `cubo_producao` é uma projeção SQL derivada.

## Autenticação integrada

`Usuario` herda de `AbstractBaseUser`. O atributo Python `password` é mapeado para a coluna física `senha_hash`. As propriedades `is_active`, `is_staff` e `is_superuser` utilizam `ativo` e `administrador`, sem criar colunas adicionais. `last_login` não é persistido porque não integra o DER.

A equipe usa `authenticate`, `login` e `logout` do Django. React e Django Admin compartilham a sessão. Clientes continuam com sua própria entidade e autenticação de cliente, sem acesso ao admin. O cadastro administrativo usa o mesmo `UsuarioForm` na API e no painel.

Senhas são armazenadas como hashes pelo Django e nunca são devolvidas na API. A sessão usa cookie HttpOnly e SameSite=Lax, com duração de 12 horas. O identificador muda na autenticação e o logout elimina a sessão. POST e PATCH da API exigem JSON e CSRF. O login da API limita tentativas em cache SQL compartilhado.

Administradores não podem retirar o próprio acesso administrativo. A remoção de perfis referenciados é bloqueada. Desativar uma conta exige concluir os pedidos atribuídos ao seu garçom e os pedidos com itens sob responsabilidade do seu operador.

## Confirmação e atribuição automática

`ConfirmacaoPedido` recebe uma `PoliticaAtribuicao`; o padrão é `MenorCarga`. Só participam garçons com usuário ativo e perfil em escala. A ordenação considera:

1. Menor quantidade de pedidos ainda não entregues.
2. Nunca ter recebido atribuição.
3. Data/hora mais antiga da última atribuição.
4. Menor `id_garcom`.

Garçons ocupados continuam elegíveis. No autoatendimento, o cliente pode selecionar um garçom elegível ou deixar a atribuição automática. No salão, o próprio garçom autenticado é o responsável e precisa estar em escala. Todo pedido confirmado tem um garçom.

A escolha, a criação do pedido e suas linhas ocorrem na mesma transação. No SQLite, a conexão usa transações `IMMEDIATE`; no PostgreSQL, os serviços usam um bloqueio transacional compartilhado. É uma estratégia simples para o porte acadêmico do projeto, com menor concorrência entre escritas. Alterações SQL externas não seguem esse protocolo.

O carrinho é relido dentro da transação. Sua revisão identifica a confirmação: repeti-la retorna o mesmo pedido e uma revisão desatualizada é rejeitada. Sem garçom elegível, a operação é cancelada e o carrinho permanece.

## Carrinho e valores

Cada inclusão cria uma linha separada, com quantidade de 1 a 20 e observações de até 200 caracteres. O servidor registra o preço e o tempo de preparo vigentes na inclusão. Alterações posteriores no cardápio não modificam esses valores. A indisponibilidade bloqueia novas inclusões. Trocar a mesa mantém o carrinho.

`Totais` usa `Decimal`: soma dos itens, serviço de 10% arredondado a centavos e total. Preços enviados pelo navegador não são utilizados. Quantidades e observações podem ser editadas antes da confirmação. O modelo não multiplica a meta de preparo pela quantidade.

## Preparo, entrega e retenção

| Ação do operador responsável | Efeito no item |
| --- | --- |
| Assumir e iniciar | Registra operador, estado `EM_PREPARO` e início |
| Marcar pronto | Exige início; registra `PRONTO` e término |
| Reabrir preparo | Retorna a `EM_PREPARO`, preserva início e limpa término |
| Voltar à fila | Retorna a `AGUARDANDO`, limpa marcos e mantém o operador |

A situação do pedido é recalculada após cada alteração: todas as linhas aguardando → `RECEBIDO`; todas prontas → `PRONTO`; demais combinações → `EM_PREPARO`.

Somente o garçom atribuído, com usuário ativo, confirma a entrega de um pedido pronto. Ele pode finalizar essa entrega depois de sair da escala. `ENTREGUE` é terminal e exige `entregue_em`.

Pedidos e linhas confirmados são preservados. O Django Admin permite consultá-los, sem alterar o fluxo ou excluí-los. Os marcos representam o estado atual; não há uma trilha completa de todas as mudanças de situação. Uma correção pode substituir o intervalo de preparo usado nas análises.

## Análises e banco SQL

SQLite é a configuração local padrão; o Render usa PostgreSQL. `cubo_producao` é uma view SQL nos dois bancos e consulta os dados atuais. A migração `0005` substitui a antiga view materializada do PostgreSQL sem alterar os pedidos armazenados.

O painel analisa pedidos entregues pela data de entrega, em períodos de 7, 30 ou 90 dias. Receita e ticket usam pedidos distintos, evitando multiplicação pelo número de linhas. Quantidades somam unidades. Receita inclui serviço. Sem base anterior, a variação fica ausente.

O preparo de um pedido vai da criação ao maior `pronto_em` de suas linhas; a entrega vai desse marco ao `entregue_em`. O preparo por categoria usa o intervalo de cada linha. Turnos: Almoço 05–14:59, Tarde 15–17:59, Jantar 18–22:59 e Ceia 23–04:59. Categorias não são aditivas como total de pedidos.

A capacidade horária e a meta de entrega só aparecem quando configuradas. Pedidos ativos permanecem no acompanhamento operacional. As análises representam consumo concluído; desistências e demanda reprimida não são registradas pelo DER.

## Casos de uso e implementação

| Caso de uso | Implementação principal |
| --- | --- |
| Acesso do cliente | `Login.jsx`, `Autenticacao`, `CadastroClienteForm`, `Cliente` |
| Consultar cardápio | `Menu.jsx`, `CardapioView`, `ItemCardapio` |
| Montar e editar carrinho | `Menu.jsx`, `Carrinho`, `CarrinhoForm`, sessão SQL |
| Confirmar pedido | `ConfirmacaoPedido`, política de atribuição, `Pedido`, `ItemPedido` |
| Acompanhar e consultar concluídos | `Orders.jsx`, `ConsultaPedidos`, atualização a cada 4 segundos |
| Registrar pedido no salão | Perfil `Garcom`, carrinho do salão e confirmação |
| Controlar escala atual | `EscalaForm`, `Escala`, `Garcom.em_escala` |
| Preparar itens | Tela de cozinha, `Preparo`, operador por linha |
| Confirmar entrega | `Entrega`, garçom responsável |
| Monitorar salão | Visão de leitura dos pedidos para operador |
| Analisar produção | `Management.jsx`, `AnaliseProducao`, perfil gerencial |
| Alterar disponibilidade | `DisponibilidadeForm`, `Disponibilidade` |
| Administrar equipe | `UsuarioForm`, `AdministracaoUsuarios`, `UsuarioAdmin` |
| Cadastrar mesas, categorias e pratos | ModelForms e Django Admin |

Os clientes autenticados recuperam o histórico ligado à conta. Anônimos consultam somente os pedidos vinculados à sessão, enquanto ela estiver válida. O armazenamento dos pedidos no banco continua após o encerramento da sessão.

Pagamentos, estoque, reservas, escala histórica e entrega externa permanecem fora do escopo.

Referências: [Django — usuários personalizados](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/), [Django — ModelForms](https://docs.djangoproject.com/en/5.2/topics/forms/modelforms/).
