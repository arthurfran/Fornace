import { useEffect, useRef, useState } from "react";
import { api, date, money, labels } from "../api";
import { useClock, usePreference, useResource } from "../hooks";
import {
  Badge,
  Empty,
  ErrorBox,
  Loading,
  Modal,
  PageTitle,
} from "../components/ui";
function elapsed(order, now) {
  return Math.max(
    0,
    Math.floor(
      ((order.entregue_em ? new Date(order.entregue_em).getTime() : now) -
        new Date(order.criado_em).getTime()) /
        60000,
    ),
  );
}
export function Orders({ context, visao }) {
  const [history, setHistory] = useState(false),
    [before, setBefore] = useState(null),
    [search, setSearch] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [confirmation, setConfirmation] = useState(null);
  const resource = useResource(
      `pedidos/?visao=${visao}&historico=${history ? 1 : 0}${before ? "&antes=" + before : ""}`,
      4000,
    ),
    now = useClock();
  async function delivery(p) {
    setBusy(true);
    setError("");
    try {
      await api.request(`pedidos/${p.id}/entregar/`, "POST", {});
      setConfirmation(null);
      await resource.refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  const user =
    context.identidade.tipo === "usuario" ? context.identidade : null;
  return (
    <>
      <PageTitle
        eyebrow={
          visao === "cliente"
            ? "DA COZINHA ATÉ VOCÊ"
            : visao === "monitor"
              ? "VISÃO GERAL DO SALÃO"
              : "ATENDIMENTO · SALÃO"
        }
        title={
          visao === "cliente"
            ? "Acompanhe seu pedido."
            : visao === "monitor"
              ? "Todas as mesas, em uma visão."
              : "Sua próxima entrega começa aqui."
        }
      >
        {visao === "salao" && user?.garcom && (
          <div className="scale">
            <label>
              <input
                type="checkbox"
                checked={user.garcom.em_escala}
                onChange={async (e) => {
                  try {
                    await api.request("escala/", "PATCH", {
                      em_escala: e.target.checked,
                    });
                    window.dispatchEvent(new Event("context-refresh"));
                  } catch (e) {
                    setError(e.message);
                  }
                }}
              />
              Em escala para novos pedidos
            </label>
            <a className="button primary" href="#novo">
              + Novo pedido
            </a>
          </div>
        )}
      </PageTitle>
      <div className="toolbar">
        <div className="segmented">
          <button
            className={!history ? "selected" : ""}
            onClick={() => {
              setHistory(false);
              setBefore(null);
            }}
          >
            Em andamento
          </button>
          <button
            className={history ? "selected" : ""}
            onClick={() => {
              setHistory(true);
              setBefore(null);
            }}
          >
            Concluídos
          </button>
        </div>
        <input
          aria-label="Buscar pedidos"
          placeholder="Buscar mesa ou código"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <span className="muted live">Atualização a cada 4 s</span>
      </div>
      <ErrorBox message={error || resource.error} />
      {!resource.data ? (
        <Loading />
      ) : !resource.data.pedidos.length ? (
        <Empty
          title={
            history ? "Nenhum pedido concluído" : "Nenhum pedido em andamento"
          }
        >
          {visao === "cliente"
            ? "Seus pedidos aparecerão aqui após a confirmação."
            : "As novas solicitações aparecerão automaticamente."}
        </Empty>
      ) : (
        <div className="order-grid">
          {resource.data.pedidos
            .filter((p) =>
              (p.codigo + " " + p.mesa)
                .toLowerCase()
                .includes(search.toLowerCase()),
            )
            .map((p) => (
              <article className="order-card panel" key={p.id}>
                <header>
                  <div>
                    <small>{p.codigo}</small>
                    <h2>{p.mesa}</h2>
                  </div>
                  <Badge status={p.situacao} />
                </header>
                <p className="order-meta">
                  {date(p.criado_em)} · {elapsed(p, now)} min
                  {p.situacao !== "ENTREGUE" && (
                    <> · meta de preparo: {p.meta_preparo_min} min</>
                  )}
                </p>
                <div className="order-progress">
                  {["RECEBIDO", "EM_PREPARO", "PRONTO", "ENTREGUE"].map(
                    (s, index) => (
                      <span
                        key={s}
                        className={
                          index <=
                          [
                            "RECEBIDO",
                            "EM_PREPARO",
                            "PRONTO",
                            "ENTREGUE",
                          ].indexOf(p.situacao)
                            ? "complete"
                            : ""
                        }
                      >
                        {labels[s]}
                      </span>
                    ),
                  )}
                </div>
                <ul className="order-lines">
                  {p.itens.map((i) => (
                    <li key={i.id}>
                      <div>
                        <strong>
                          {i.quantidade}× {i.nome}
                        </strong>
                        {i.observacoes && (
                          <small className="observation">{i.observacoes}</small>
                        )}
                        <small>
                          {i.operador
                            ? "Preparo: " + i.operador
                            : "Aguardando operador"}
                        </small>
                      </div>
                      <Badge status={i.situacao} />
                    </li>
                  ))}
                </ul>
                <footer>
                  <div>
                    <small>Garçom responsável</small>
                    <strong>{p.garcom}</strong>
                  </div>
                  <strong>{money(p.total)}</strong>
                </footer>
                {visao === "salao" && p.situacao === "PRONTO" && (
                  <button
                    className="primary wide"
                    onClick={() => setConfirmation(p)}
                  >
                    Confirmar entrega
                  </button>
                )}
                {p.entregue_em && (
                  <small className="muted">
                    Entregue em {date(p.entregue_em)}
                  </small>
                )}
              </article>
            ))}
        </div>
      )}
      {resource.data?.mais && (
        <button
          className="button"
          onClick={() => setBefore(resource.data.antes)}
        >
          Próxima página
        </button>
      )}
      {before && (
        <button className="text-button" onClick={() => setBefore(null)}>
          Voltar aos mais recentes
        </button>
      )}
      {confirmation && (
        <Modal
          title="Confirmar entrega"
          close={() => !busy && setConfirmation(null)}
        >
          <p>
            Todos os itens do pedido <strong>{confirmation.codigo}</strong>{" "}
            foram entregues em <strong>{confirmation.mesa}</strong>?
          </p>
          <ErrorBox message={error} />
          <button
            className="primary wide"
            disabled={busy}
            onClick={() => void delivery(confirmation)}
          >
            {busy ? "Confirmando…" : "Sim, pedido entregue"}
          </button>
        </Modal>
      )}
    </>
  );
}
export function Kitchen({ context }) {
  const [before, setBefore] = useState(null);
  const result = useResource(
      `pedidos/?visao=cozinha${before ? "&antes=" + before : ""}`,
      4000,
    ),
    now = useClock();
  const [mode, setMode] = usePreference("fornace-kds-mode", "ambos"),
    [sound, setSound] = useState(false),
    [filter, setFilter] = useState("todos"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const audio = useRef(null),
    previous = useRef(null);
  const operator =
    context.identidade.tipo === "usuario"
      ? context.identidade.operador?.id
      : null;
  useEffect(() => {
    previous.current = null;
  }, [before]);
  useEffect(() => {
    if (!result.data) return;
    const current = new Map(result.data.pedidos.map((p) => [p.id, p.situacao]));
    if (previous.current && sound && audio.current) {
      const added = [...current.keys()].some((id) => !previous.current.has(id)),
        ready = [...current.entries()].some(
          ([id, s]) => s === "PRONTO" && previous.current.get(id) !== "PRONTO",
        ),
        removed = [...previous.current.keys()].some((id) => !current.has(id));
      if (added || ready || removed) {
        const ctx = audio.current,
          osc = ctx.createOscillator(),
          gain = ctx.createGain();
        osc.frequency.value = ready ? 880 : added ? 540 : 330;
        gain.gain.setValueAtTime(0.06, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
        osc.connect(gain).connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.3);
      }
    }
    previous.current = current;
  }, [result.data, sound]);
  async function change(id, status) {
    setError("");
    setBusy(true);
    try {
      await api.request(`itens/${id}/preparo/`, "PATCH", {
        situacao: status,
      });
      await result.refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  const lines = (result.data?.pedidos || [])
    .flatMap((p) =>
      p.itens.map((i) => ({
        p,
        i,
      })),
    )
    .filter(
      ({ i }) =>
        filter === "todos" ||
        (filter === "meus" ? i.operador_id === operator : !i.operador_id),
    );
  return (
    <>
      <PageTitle
        eyebrow="KITCHEN DISPLAY SYSTEM"
        title="Cada prato, no seu ponto."
      >
        <span className="live">● Ao vivo · 4 s</span>
      </PageTitle>
      <div className="toolbar">
        <label>
          Exibir
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="todos">Todos os itens</option>
            <option value="meus">Meus itens</option>
            <option value="livres">Sem operador</option>
          </select>
        </label>
        <label>
          Interação
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="ambos">Botões e arrastar</option>
            <option value="botoes">Somente botões</option>
            <option value="arrastar">Somente arrastar</option>
          </select>
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={sound}
            onChange={(e) => {
              setSound(e.target.checked);
              if (e.target.checked) {
                audio.current ??= new AudioContext();
                void audio.current.resume();
              }
            }}
          />
          Avisos sonoros
        </label>
        <span className="muted">
          {lines.length} linhas · o primeiro início define o responsável
        </span>
      </div>
      <ErrorBox message={error || result.error} />
      {!result.data ? (
        <Loading />
      ) : (
        <div className="kds-board">
          {["AGUARDANDO", "EM_PREPARO", "PRONTO"].map((s) => (
            <section
              className={"kds-column " + s.toLowerCase()}
              key={s}
              onDragOver={(e) => {
                if (mode !== "botoes") e.preventDefault();
              }}
              onDrop={(e) => {
                e.preventDefault();
                const id = Number(e.dataTransfer.getData("text/plain"));
                if (id && !busy && mode !== "botoes") void change(id, s);
              }}
            >
              <h2>
                {labels[s]}{" "}
                <span>{lines.filter(({ i }) => i.situacao === s).length}</span>
              </h2>
              {lines
                .filter(({ i }) => i.situacao === s)
                .map(({ p, i }) => {
                  const owned = !i.operador_id || i.operador_id === operator;
                  return (
                    <article
                      key={i.id}
                      className={
                        "kds-card " +
                        (elapsed(p, now) > p.meta_preparo_min &&
                        p.situacao !== "PRONTO"
                          ? "late"
                          : "")
                      }
                      draggable={owned && !busy && mode !== "botoes"}
                      onDragStart={(e) =>
                        e.dataTransfer.setData("text/plain", String(i.id))
                      }
                    >
                      <header>
                        <strong>{p.mesa}</strong>
                        <span>{elapsed(p, now)} min</span>
                      </header>
                      <small>
                        {p.codigo} · linha {i.linha} · {p.garcom}
                      </small>
                      <h3>
                        {i.quantidade}× {i.nome}
                      </h3>
                      {i.observacoes && (
                        <p className="observation">{i.observacoes}</p>
                      )}
                      <p className="muted">
                        {i.operador || "Sem operador atribuído"}
                      </p>
                      {mode !== "arrastar" && owned && (
                        <div className="kds-actions">
                          {s === "AGUARDANDO" ? (
                            <button
                              disabled={busy}
                              className="primary"
                              onClick={() => void change(i.id, "EM_PREPARO")}
                            >
                              Assumir e iniciar
                            </button>
                          ) : s === "EM_PREPARO" ? (
                            <>
                              <button
                                disabled={busy}
                                className="primary"
                                onClick={() => void change(i.id, "PRONTO")}
                              >
                                Marcar pronto
                              </button>
                              <button
                                disabled={busy}
                                onClick={() => void change(i.id, "AGUARDANDO")}
                              >
                                Voltar à fila
                              </button>
                            </>
                          ) : (
                            <button
                              disabled={busy}
                              onClick={() => void change(i.id, "EM_PREPARO")}
                            >
                              Reabrir preparo
                            </button>
                          )}
                        </div>
                      )}
                      {!owned && (
                        <small>Alterações restritas ao responsável.</small>
                      )}
                    </article>
                  );
                })}
              {!lines.some(({ i }) => i.situacao === s) && (
                <p className="column-empty">Nenhum item nesta etapa.</p>
              )}
            </section>
          ))}
        </div>
      )}
      {result.data?.mais && (
        <button onClick={() => setBefore(result.data.antes)}>
          Próxima página de pedidos
        </button>
      )}
      {before && (
        <button className="text-button" onClick={() => setBefore(null)}>
          Voltar aos mais recentes
        </button>
      )}
    </>
  );
}
