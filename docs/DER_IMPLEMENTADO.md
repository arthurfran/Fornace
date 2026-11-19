# DER implementado — entidades e atributos

O modelo contém **9 entidades, 57 atributos e 9 relacionamentos**. Os nomes abaixo são os nomes físicos das colunas. Os perfis possuem PK própria e FK única; não existe coluna simultaneamente PK/FK.

No Django, o atributo `Usuario.password` usa `db_column="senha_hash"`. Essa integração com a autenticação não muda o nome físico nem adiciona colunas à entidade. `is_active`, `is_staff` e `is_superuser` são propriedades calculadas a partir dos campos existentes.

## USUARIO

| Atributo | Tipo lógico | Nulo | Chave / regra |
| --- | --- | --- | --- |
| `id_usuario` | BIGINT / identidade | Não | PK |
| `nome` | VARCHAR(120) | Não | — |
| `login` | VARCHAR(120) | Não | UK |
| `senha_hash` | VARCHAR(255) | Não | — |
| `ativo` | BOOLEAN | Não | — |
| `administrador` | BOOLEAN | Não | — |

## GARCOM

| Atributo | Tipo lógico | Nulo | Chave / regra |
| --- | --- | --- | --- |
| `id_garcom` | BIGINT / identidade | Não | PK |
| `id_usuario` | BIGINT | Não | FK → USUARIO.id_usuario; UK |
| `setor` | VARCHAR(80) | Não | — |
| `em_escala` | BOOLEAN | Não | — |

## OPERADOR_COZINHA

| Atributo | Tipo lógico | Nulo | Chave / regra |
| --- | --- | --- | --- |
| `id_operador` | BIGINT / identidade | Não | PK |
| `id_usuario` | BIGINT | Não | FK → USUARIO.id_usuario; UK |
| `funcao` | VARCHAR(80) | Não | — |
| `perfil_gerencial` | BOOLEAN | Não | — |

## CLIENTE

| Atributo | Tipo lógico | Nulo | Chave / regra |
| --- | --- | --- | --- |
| `id_cliente` | BIGINT / identidade | Não | PK |
| `nome` | VARCHAR(120) | Não | — |
| `email` | VARCHAR(120) | Não | UK |
| `senha_hash` | VARCHAR(255) | Não | — |

## MESA

| Atributo | Tipo lógico | Nulo | Chave / regra |
| --- | --- | --- | --- |
| `id_mesa` | BIGINT / identidade | Não | PK |
| `identificacao` | VARCHAR(60) | Não | UK |
| `tipo_local` | VARCHAR(10) | Não | MESA, BALCAO, VARANDA |

## CATEGORIA

| Atributo | Tipo lógico | Nulo | Chave / regra |
| --- | --- | --- | --- |
| `id_categoria` | BIGINT / identidade | Não | PK |
| `nome` | VARCHAR(80) | Não | UK |

## ITEM_CARDAPIO

| Atributo | Tipo lógico | Nulo | Chave / regra |
| --- | --- | --- | --- |
| `id_item_cardapio` | BIGINT / identidade | Não | PK |
| `id_categoria` | BIGINT | Não | FK → CATEGORIA.id_categoria |
| `nome` | VARCHAR(80) | Não | — |
| `descricao` | VARCHAR(200) | Não | — |
| `preco_atual` | DECIMAL(12, 2) | Não | — |
| `tempo_medio_preparo_min` | INTEGER ≥ 0 | Não | — |
| `disponivel` | BOOLEAN | Não | — |
| `foto_uri` | TEXT | Sim | — |

## PEDIDO

| Atributo | Tipo lógico | Nulo | Chave / regra |
| --- | --- | --- | --- |
| `id_pedido` | BIGINT / identidade | Não | PK |
| `codigo` | VARCHAR(32) | Não | UK |
| `id_mesa` | BIGINT | Não | FK → MESA.id_mesa |
| `id_cliente` | BIGINT | Sim | FK → CLIENTE.id_cliente |
| `id_garcom` | BIGINT | Não | FK → GARCOM.id_garcom |
| `origem` | VARCHAR(16) | Não | — |
| `forma_atribuicao` | VARCHAR(12) | Não | — |
| `situacao_atual` | VARCHAR(10) | Não | RECEBIDO, EM_PREPARO, PRONTO, ENTREGUE |
| `criado_em` | TIMESTAMP com fuso | Não | — |
| `atribuido_em` | TIMESTAMP com fuso | Não | — |
| `meta_preparo_min` | INTEGER ≥ 0 | Não | — |
| `taxa_servico_pct` | DECIMAL(5, 2) | Não | — |
| `valor_total_registrado` | DECIMAL(12, 2) | Não | — |
| `entregue_em` | TIMESTAMP com fuso | Sim | — |

## ITEM_PEDIDO

| Atributo | Tipo lógico | Nulo | Chave / regra |
| --- | --- | --- | --- |
| `id_item_pedido` | BIGINT / identidade | Não | PK |
| `id_pedido` | BIGINT | Não | FK → PEDIDO.id_pedido |
| `numero_linha` | INTEGER ≥ 0 | Não | — |
| `id_item_cardapio` | BIGINT | Não | FK → ITEM_CARDAPIO.id_item_cardapio |
| `quantidade` | SMALLINT ≥ 0 | Não | — |
| `observacoes` | VARCHAR(200) | Sim | — |
| `preco_unitario_registrado` | DECIMAL(12, 2) | Não | — |
| `tempo_preparo_registrado_min` | INTEGER ≥ 0 | Não | — |
| `id_operador` | BIGINT | Sim | FK → OPERADOR_COZINHA.id_operador |
| `situacao_preparo` | VARCHAR(10) | Não | AGUARDANDO, EM_PREPARO, PRONTO |
| `inicio_preparo_em` | TIMESTAMP com fuso | Sim | — |
| `pronto_em` | TIMESTAMP com fuso | Sim | — |

## Regras entre entidades

| Relação | Cardinalidade |
| --- | --- |
| USUARIO → GARCOM | 1 → 0..1 |
| USUARIO → OPERADOR_COZINHA | 1 → 0..1 |
| MESA → PEDIDO | 1 → 0..N; mesa obrigatória no pedido |
| CLIENTE → PEDIDO | 1 → 0..N; cliente opcional no pedido |
| GARCOM → PEDIDO | 1 → 0..N; garçom obrigatório no pedido |
| CATEGORIA → ITEM_CARDAPIO | 1 → 0..N; categoria obrigatória |
| PEDIDO → ITEM_PEDIDO | 1 → 1..N em cada confirmação |
| ITEM_CARDAPIO → ITEM_PEDIDO | 1 → 0..N |
| OPERADOR_COZINHA → ITEM_PEDIDO | 1 → 0..N; operador obrigatório a partir do início |

`(id_pedido, numero_linha)` é único. Quantidade fica entre 1 e 20. Preços e tempos são não negativos. `taxa_servico_pct` é 10. Situações e marcos têm restrições de coerência SQL, complementadas pelas regras transacionais dos serviços.

`origem` aceita AUTOATENDIMENTO ou SALAO. `forma_atribuicao` aceita MANUAL/AUTOMATICA para autoatendimento e PELO_SALAO para salão. Pedido entregue exige `entregue_em`; as demais situações exigem esse campo nulo.

`AGUARDANDO` exige marcos de preparo nulos. `EM_PREPARO` exige operador e início; `PRONTO` exige operador e ambos os marcos. O instante pronto não pode anteceder o início. A API usa horários do servidor.

As migrações Django são a fonte executável do esquema. `cubo_producao` deriva destas entidades; tabelas de sessão, cache, migrações, permissões, tipos de conteúdo e log administrativo pertencem à infraestrutura do Django. Elas não integram a contagem de entidades do domínio. Não há HISTORICO_SITUACAO.
