# Demonstração e conferência da versão

## Roteiro sugerido — 7 a 10 minutos

Prepare o projeto conforme o README e use janelas ou perfis independentes do navegador para não misturar as sessões do cliente, do operador e do garçom. A senha é aquela escolhida na carga demonstrativa.

| Tempo | Ação | O que explicar |
| --- | --- | --- |
| 0:00–1:00 | Apresentar React, Django e SQLite | React em JavaScript; Django com modelos, formulários, views e rotas; persistência SQL |
| 1:00–3:00 | Cliente anônimo: selecionar mesa, incluir itens e confirmar com atribuição automática | Cadastro opcional, mesa obrigatória, preço registrado no servidor e garçom sempre atribuído |
| 3:00–5:00 | Entrar como `marina`: assumir e iniciar cada item, depois marcar pronto | Cada linha tem seu operador; a situação do pedido resulta dos estados das linhas |
| 5:00–6:30 | Entrar como o garçom indicado no pedido e confirmar a entrega | Somente o responsável entrega; pedido concluído permanece armazenado |
| 6:30–8:00 | Mostrar Concluídos e Análises com `marina` | Histórico persistido; indicadores calculados sobre pedidos entregues |
| 8:00–9:00 | Entrar como `admin`, cadastrar usuário com os dois perfis e abrir Cadastros Django | Usuário é a conta; garçom e operador são perfis acumuláveis; admin é uma permissão |
| 9:00–10:00 | Mostrar `models.py`, `forms.py`, `views.py` e o DER | PK/FK separadas, regras compartilhadas e estrutura baseada no projeto de referência |

Para uma demonstração de sete minutos, reduza a visão do código e apresente os cadastros sem criar todos os registros ao vivo. As análises refletem a entrega na próxima consulta tanto no SQLite quanto no PostgreSQL.

## Conferência manual disponível ao grupo

1. **Cliente sem identificação:** criar pedido e verificar mesa, garçom e nome “Anônimo”.
2. **Cliente com conta:** cadastrar, sair, entrar novamente e consultar os próprios pedidos.
3. **Garçom em escala:** registrar pedido do salão; ao sair da escala, conferir que deixa de receber novas atribuições.
4. **Operador:** assumir uma linha; com outro operador, conferir que a mesma linha não pode ser modificada.
5. **Entrega:** preparar todas as linhas e confirmar com o garçom responsável. Conferir a permanência em Concluídos.
6. **Usuário com dois perfis:** acessar salão e cozinha usando a mesma conta.
7. **Administrador:** cadastrar/editar equipe no React e mesas, categorias e pratos no Django Admin.
8. **Disponibilidade:** desabilitar um prato, conferir o impedimento de novas inclusões e habilitá-lo novamente.
9. **Telas:** conferir cardápio, carrinho, cozinha e gestão no computador e no celular usados na apresentação.

## Verificações realizadas nesta revisão

- Configuração do Django e aplicação das migrações em um banco SQLite novo.
- Atualização de um banco criado pela versão anterior, preservando contas, senha, pedido e linha de pedido.
- Integração HTTP com CSRF: acesso da equipe, acesso pelo admin nativo, sessão compartilhada e cadastro com ambos os perfis.
- Cadastro/edição de usuários via API, preservação de senha em edição, cadastro e login do cliente.
- Fluxo HTTP de pedido anônimo com atribuição automática, preparo pelo operador, entrega, histórico e análises.
- Bloqueio de preparo por administrador sem perfil e por operador diferente do responsável.
- Alteração/restauração de disponibilidade e da escala atual.
- Compilação do frontend JavaScript com Vite.

Essas verificações foram pontuais durante a revisão. O projeto não inclui suíte de testes ou dependências de testes. Use o roteiro acima para conferir o layout na máquina da apresentação.

O ZIP não contém banco com dados, credenciais, ambiente virtual, dependências instaladas ou arquivos compilados. `migrate` cria o banco e `seed_demo` prepara a demonstração.
