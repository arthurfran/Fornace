import { useState } from "react";
import { api, date, money } from "../api";
import { useResource } from "../hooks";
import { Empty, ErrorBox, Loading, Modal, PageTitle } from "../components/ui";
export function Availability() {
  const r = useResource("cardapio/", 4000),
    [error, setError] = useState("");
  return (
    <>
      <PageTitle
        eyebrow="OPERAÇÃO · CARDÁPIO"
        title="Disponibilidade em tempo real."
      />
      <p className="muted">
        A alteração vale para novas inclusões. Itens já no carrinho preservam
        preço e disponibilidade registrados.
      </p>
      <ErrorBox message={error || r.error} />
      <div className="panel table-wrap">
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th>Categoria</th>
              <th>Preço</th>
              <th>Disponível</th>
            </tr>
          </thead>
          <tbody>
            {r.data?.itens.map((i) => (
              <tr key={i.id}>
                <td>{i.nome}</td>
                <td>{i.categoria}</td>
                <td>{money(i.preco)}</td>
                <td>
                  <input
                    aria-label={"Disponibilidade de " + i.nome}
                    type="checkbox"
                    checked={i.disponivel}
                    onChange={async (e) => {
                      try {
                        await api.request(
                          `cardapio/${i.id}/disponibilidade/`,
                          "PATCH",
                          {
                            disponivel: e.target.checked,
                          },
                        );
                        await r.refresh();
                      } catch (e) {
                        setError(e.message);
                      }
                    }}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
export function Users() {
  const r = useResource("usuarios/"),
    [editing, setEditing] = useState(null),
    [waiter, setWaiter] = useState(false),
    [operator, setOperator] = useState(false),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  function edit(u) {
    setEditing(u);
    setWaiter(u !== "new" && !!u.garcom);
    setOperator(u !== "new" && !!u.operador);
    setError("");
  }
  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const f = new FormData(e.currentTarget);
    try {
      await api.request(
        `usuarios/${editing !== "new" && editing ? editing.id + "/" : ""}`,
        editing === "new" ? "POST" : "PATCH",
        {
          nome: f.get("nome"),
          login: f.get("login"),
          senha: f.get("senha"),
          ativo: f.has("ativo"),
          administrador: f.has("administrador"),
          garcom: waiter
            ? {
                setor: f.get("setor"),
                em_escala: f.has("em_escala"),
              }
            : null,
          operador: operator
            ? {
                funcao: f.get("funcao"),
                perfil_gerencial: f.has("perfil_gerencial"),
              }
            : null,
        },
      );
      setEditing(null);
      await r.refresh();
      window.dispatchEvent(new Event("context-refresh"));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  const u = editing && editing !== "new" ? editing : null;
  return (
    <>
      <PageTitle
        eyebrow="ADMINISTRAÇÃO · ACESSOS"
        title="Uma conta. Os perfis necessários."
      >
        <button className="primary" onClick={() => edit("new")}>
          + Novo usuário
        </button>
      </PageTitle>
      <p className="muted">
        Garçom e operador podem coexistir. A permissão de administrador pode ser
        usada sozinha.
      </p>
      <ErrorBox message={r.error} />
      <div className="panel table-wrap">
        <table>
          <thead>
            <tr>
              <th>Usuário</th>
              <th>Perfis</th>
              <th>Situação</th>
              <th>Ação</th>
            </tr>
          </thead>
          <tbody>
            {r.data?.usuarios.map((u) => (
              <tr key={u.id}>
                <td>
                  <strong>{u.nome}</strong>
                  <small>{u.login}</small>
                </td>
                <td>
                  {[
                    u.administrador ? "Administrador" : "",
                    u.garcom ? "Garçom" : "",
                    u.operador
                      ? "Operador" +
                        (u.operador.perfil_gerencial ? " gerencial" : "")
                      : "",
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </td>
                <td>{u.ativo ? "Ativo" : "Inativo"}</td>
                <td>
                  <button onClick={() => edit(u)}>Editar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {editing && (
        <Modal
          title={u ? "Editar usuário" : "Novo usuário"}
          close={() => !busy && setEditing(null)}
        >
          <ErrorBox message={error} />
          <form onSubmit={save}>
            <div className="form-grid">
              <label>
                Nome
                <input
                  name="nome"
                  defaultValue={u?.nome}
                  required
                  maxLength={120}
                />
              </label>
              <label>
                Login
                <input
                  name="login"
                  defaultValue={u?.login}
                  required
                  maxLength={120}
                />
              </label>
            </div>
            <label>
              {u ? "Nova senha (opcional)" : "Senha"}
              <input
                name="senha"
                type="password"
                minLength={8}
                maxLength={64}
                required={!u}
                autoComplete="new-password"
              />
            </label>
            <div className="form-checks">
              <label>
                <input
                  type="checkbox"
                  name="ativo"
                  defaultChecked={u?.ativo ?? true}
                />
                Usuário ativo
              </label>
              <label>
                <input
                  type="checkbox"
                  name="administrador"
                  defaultChecked={u?.administrador}
                />
                Administrador
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={waiter}
                  onChange={(e) => setWaiter(e.target.checked)}
                />
                Perfil de garçom
              </label>
              {waiter && (
                <fieldset>
                  <label>
                    Setor
                    <input
                      name="setor"
                      defaultValue={u?.garcom?.setor || "Salão"}
                      required
                      maxLength={80}
                    />
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      name="em_escala"
                      defaultChecked={u?.garcom?.em_escala}
                    />
                    Em escala
                  </label>
                </fieldset>
              )}
              <label>
                <input
                  type="checkbox"
                  checked={operator}
                  onChange={(e) => setOperator(e.target.checked)}
                />
                Perfil de operador de cozinha
              </label>
              {operator && (
                <fieldset>
                  <label>
                    Função
                    <input
                      name="funcao"
                      defaultValue={u?.operador?.funcao || "Preparo"}
                      required
                      maxLength={80}
                    />
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      name="perfil_gerencial"
                      defaultChecked={u?.operador?.perfil_gerencial}
                    />
                    Acesso a análises gerenciais
                  </label>
                </fieldset>
              )}
            </div>
            <button className="primary wide" disabled={busy}>
              {busy ? "Salvando…" : "Salvar usuário"}
            </button>
          </form>
        </Modal>
      )}
    </>
  );
}
function Bars({ rows, unit = "" }) {
  const max = Math.max(...rows.map((r) => r.value), 1);
  return (
    <div className="bars">
      {rows.map((r) => (
        <div className="bar-row" key={r.label}>
          <span>{r.label}</span>
          <div>
            <i
              style={{
                width: (r.value / max) * 100 + "%",
              }}
            />
          </div>
          <strong>
            {r.value}
            {unit}
          </strong>
        </div>
      ))}
    </div>
  );
}
export function Analysis() {
  const [days, setDays] = useState(30),
    [cell, setCell] = useState(null);
  const r = useResource(`analise/?dias=${days}`, 30000),
    detail = useResource(
      `analise/?dias=${days}${cell ? "&categoria=" + encodeURIComponent(cell.categoria) + "&turno=" + encodeURIComponent(cell.turno) : ""}`,
    );
  const d = r.data;
  return (
    <>
      <PageTitle
        eyebrow="GESTÃO · OFERTA E DEMANDA"
        title="Da operação, uma visão clara."
      >
        <label>
          Período
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
          >
            {[7, 30, 90].map((n) => (
              <option key={n} value={n}>
                Últimos {n} dias
              </option>
            ))}
          </select>
        </label>
      </PageTitle>
      <ErrorBox message={r.error} />
      {!d ? (
        <Loading />
      ) : (
        <>
          <p className="muted">
            {d.criterio}{" "}
            {d.atualizado_em
              ? "Projeção atualizada em " + date(d.atualizado_em) + "."
              : "Ainda não há entregas para analisar."}
          </p>
          <div className="metric-grid">
            {[
              ["Pedidos entregues", d.pedidos],
              ["Unidades servidas", d.unidades],
              ["Receita com serviço", money(d.receita)],
              ["Ticket médio", money(d.ticket_medio)],
              [
                "Preparo médio",
                d.preparo_medio_min === null
                  ? "—"
                  : d.preparo_medio_min + " min",
              ],
              [
                "Acima da meta de preparo",
                d.atraso_preparo_pct === null
                  ? "—"
                  : d.atraso_preparo_pct + "%",
              ],
            ].map(([label, value]) => (
              <article className="panel metric" key={label}>
                <small>{label}</small>
                <strong>{value}</strong>
              </article>
            ))}
          </div>
          <p className="muted">
            Em relação ao período anterior: pedidos{" "}
            {d.variacao_pedidos_pct === null
              ? "sem base de comparação"
              : d.variacao_pedidos_pct + "%"}{" "}
            · receita{" "}
            {d.variacao_receita_pct === null
              ? "sem base de comparação"
              : d.variacao_receita_pct + "%"}
            . Entrega após pronto:{" "}
            {d.entrega_media_min === null ? "—" : d.entrega_media_min + " min"}.{" "}
            {d.sla_entrega_min
              ? `Fora do prazo de entrega: ${d.atraso_entrega_pct ?? "—"}%.`
              : "Prazo de entrega não configurado."}
          </p>
          <div className="analytics-grid">
            <section className="panel chart">
              <h2>Demanda por categoria e turno</h2>
              <p className="muted">
                Pedidos distintos. Clique em uma célula para consultar as
                entregas.
              </p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Categoria</th>
                      {["Almoço", "Tarde", "Jantar", "Ceia"].map((t) => (
                        <th key={t}>{t}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {d.categorias.map((c) => (
                      <tr key={c.nome}>
                        <th>{c.nome}</th>
                        {["Almoço", "Tarde", "Jantar", "Ceia"].map((t) => (
                          <td key={t}>
                            <button
                              className="cell-button"
                              onClick={() =>
                                setCell({
                                  categoria: c.nome,
                                  turno: t,
                                })
                              }
                            >
                              {d.matriz.find(
                                (m) => m.categoria === c.nome && m.turno === t,
                              )?.pedidos || 0}
                            </button>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <small>
                Um pedido com duas categorias aparece em ambas; as células não
                devem ser somadas como total de pedidos.
              </small>
            </section>
            <section className="panel chart">
              <h2>Mais pedidos</h2>
              <Bars
                rows={d.ranking.map((r) => ({
                  label: r.nome,
                  value: r.unidades,
                }))}
              />
              {!d.ranking.length && <Empty title="Sem entregas no período" />}
            </section>
            <section className="panel chart">
              <h2>Preparo por categoria</h2>
              <Bars
                rows={d.categorias.map((c) => ({
                  label: c.nome,
                  value: c.preparo_medio_min || 0,
                }))}
                unit=" min"
              />
              <small>Média por linha: início até pronto.</small>
            </section>
            <section className="panel chart">
              <h2>Volume por dia da semana</h2>
              <Bars
                rows={d.semana.map((r) => ({
                  label: r.dia,
                  value: r.pedidos,
                }))}
              />
            </section>
            <section className="panel chart span-two">
              <h2>Entregas por hora</h2>
              <p className="muted">
                Média por dia no período ·{" "}
                {d.capacidade_hora
                  ? `capacidade configurada: ${d.capacidade_hora} pedidos/h`
                  : "capacidade não configurada"}
              </p>
              <div
                className="hour-chart"
                role="img"
                aria-label="Média diária de pedidos entregues por hora"
              >
                {d.capacidade_hora && (
                  <div
                    className="capacity"
                    style={{
                      bottom:
                        (d.capacidade_hora /
                          Math.max(
                            ...d.horas.map((h) => h.media_dia),
                            d.capacidade_hora,
                            1,
                          )) *
                          100 +
                        "%",
                    }}
                  >
                    <span>Capacidade</span>
                  </div>
                )}
                {d.horas.map((h) => (
                  <div
                    className="hour"
                    key={h.hora}
                    title={`${h.hora}h: ${h.media_dia} pedidos/dia (${h.pedidos} no período)`}
                  >
                    <i
                      style={{
                        height:
                          (h.media_dia /
                            Math.max(
                              ...d.horas.map((h) => h.media_dia),
                              d.capacidade_hora || 0,
                              1,
                            )) *
                            100 +
                          "%",
                      }}
                    />
                    <small>{h.hora}</small>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </>
      )}
      {cell && (
        <Modal
          title={`${cell.categoria} · ${cell.turno}`}
          close={() => setCell(null)}
        >
          <ErrorBox message={detail.error} />
          <p className="muted">Até 100 entregas mais recentes deste recorte.</p>
          {!detail.data ? (
            <Loading />
          ) : !detail.data.pedidos_detalhe.length ? (
            <Empty title="Nenhuma entrega neste recorte" />
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Pedido</th>
                  <th>Entrega</th>
                  <th>Total do pedido</th>
                </tr>
              </thead>
              <tbody>
                {detail.data.pedidos_detalhe.map((p) => (
                  <tr key={p.id}>
                    <td>{p.codigo}</td>
                    <td>{date(p.entregue_em)}</td>
                    <td>{money(p.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Modal>
      )}
    </>
  );
}
