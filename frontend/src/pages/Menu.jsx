import { useState } from "react";
import { api, money } from "../api";
import { useResource } from "../hooks";
import { ErrorBox, Empty, Loading, Modal, PageTitle } from "../components/ui";
const notes = [
  "Sem cebola",
  "Sem lactose",
  "Ponto ao ponto",
  "Bem passado",
  "Trocar guarnição",
  "Alergia a nozes",
];
export function Menu({ context, origem, confirmed }) {
  const menu = useResource("cardapio/", 4000),
    cart = useResource(`carrinhos/${origem}/`);
  const [category, setCategory] = useState("Todos"),
    [search, setSearch] = useState(""),
    [selected, setSelected] = useState(null),
    [editing, setEditing] = useState(null),
    [qty, setQty] = useState(1),
    [note, setNote] = useState(""),
    [waiter, setWaiter] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const items = menu.data?.itens || [],
    categories = ["Todos", ...new Set(items.map((i) => i.categoria))];
  async function change(data) {
    setBusy(true);
    setError("");
    try {
      cart.setData(await api.request(`carrinhos/${origem}/`, "POST", data));
      return true;
    } catch (e) {
      setError(e.message);
      return false;
    } finally {
      setBusy(false);
    }
  }
  async function checkout() {
    if (!cart.data) return;
    setBusy(true);
    setError("");
    try {
      const { pedido } = await api.request(
        `carrinhos/${origem}/confirmar/`,
        "POST",
        {
          revisao: cart.data.revisao,
          garcom_id: waiter ? Number(waiter) : null,
        },
      );
      confirmed(pedido);
    } catch (e) {
      setError(e.message);
      await cart.refresh();
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow={
          origem === "salao"
            ? "ATENDIMENTO · NOVO PEDIDO"
            : "COZINHA ITALIANA · FEITA COM TEMPO"
        }
        title={
          origem === "salao"
            ? "Do salão para a cozinha."
            : "O que vai à sua mesa hoje?"
        }
      >
        <p>
          Ingredientes escolhidos.
          <br />
          Sabores que convidam a ficar.
        </p>
      </PageTitle>
      <ErrorBox message={error || menu.error || cart.error} />
      <div className="menu-layout">
        <section>
          <div className="menu-tools">
            <label className="search">
              Buscar no cardápio
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Prato, ingrediente…"
              />
            </label>
            <div className="pills" aria-label="Categorias">
              {categories.map((c) => (
                <button
                  key={c}
                  className={c === category ? "selected" : ""}
                  onClick={() => setCategory(c)}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
          <div className="menu-grid">
            {!menu.data ? (
              <Loading />
            ) : (
              items
                .filter(
                  (i) =>
                    (category === "Todos" || i.categoria === category) &&
                    (i.nome + " " + i.descricao)
                      .toLowerCase()
                      .includes(search.toLowerCase()),
                )
                .map((i) => (
                  <article
                    className={
                      "food-card " + (!i.disponivel ? "unavailable" : "")
                    }
                    key={i.id}
                  >
                    <img
                      src={i.foto || undefined}
                      alt={i.nome}
                      loading="lazy"
                    />
                    <div className="food-body">
                      <div className="food-meta">
                        <span>{i.categoria}</span>
                        <span>{i.tempo} min</span>
                      </div>
                      <h2>{i.nome}</h2>
                      <p>{i.descricao}</p>
                      <footer>
                        <strong>{money(i.preco)}</strong>
                        <button
                          disabled={!i.disponivel || busy}
                          aria-label={"Adicionar " + i.nome}
                          onClick={() => {
                            setSelected(i);
                            setQty(1);
                            setNote("");
                          }}
                        >
                          {i.disponivel ? "Adicionar +" : "Indisponível"}
                        </button>
                      </footer>
                    </div>
                  </article>
                ))
            )}
          </div>
        </section>
        <aside className="cart panel">
          <div className="cart-title">
            <h2>Seu pedido</h2>
            <span>
              {cart.data?.linhas.reduce((n, l) => n + l.quantidade, 0) || 0}{" "}
              itens
            </span>
          </div>
          {cart.data && (
            <>
              <label>
                {origem === "salao" ? "Mesa do atendimento" : "Onde você está?"}
                <select
                  value={cart.data.mesa_id || ""}
                  disabled={busy}
                  onChange={(e) =>
                    void change({
                      acao: "mesa",
                      mesa_id: Number(e.target.value),
                    })
                  }
                >
                  <option value="" disabled>
                    Selecione a mesa
                  </option>
                  {context.mesas.map((m) => (
                    <option key={m.id_mesa} value={m.id_mesa}>
                      {m.identificacao}
                    </option>
                  ))}
                </select>
              </label>
              {!cart.data.linhas.length ? (
                <Empty title="A mesa está posta">
                  Escolha um prato para começar.
                </Empty>
              ) : (
                <div className="cart-lines">
                  {cart.data.linhas.map((l) => (
                    <div className="cart-line" key={l.id}>
                      <div>
                        <strong>{l.nome}</strong>
                        <span>{money(Number(l.preco) * l.quantidade)}</span>
                      </div>
                      {l.observacoes && <small>{l.observacoes}</small>}
                      <div>
                        <label className="quantity">
                          Quantidade
                          <input
                            aria-label={"Quantidade de " + l.nome}
                            type="number"
                            min="1"
                            max="20"
                            value={l.quantidade}
                            disabled={busy}
                            onChange={(e) => {
                              const value = Number(e.target.value);
                              if (value >= 1 && value <= 20)
                                void change({
                                  acao: "alterar",
                                  linha_id: l.id,
                                  quantidade: value,
                                  observacoes: l.observacoes,
                                });
                            }}
                          />
                        </label>
                        <button
                          className="text-button"
                          disabled={busy}
                          onClick={() => {
                            setEditing(l);
                            setQty(l.quantidade);
                            setNote(l.observacoes);
                          }}
                        >
                          Editar
                        </button>
                        <button
                          className="text-button danger"
                          disabled={busy}
                          onClick={() =>
                            void change({
                              acao: "remover",
                              linha_id: l.id,
                            })
                          }
                        >
                          Remover
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {origem === "cliente" && (
                <label>
                  Garçom responsável
                  <select
                    aria-label="Garçom responsável"
                    value={waiter}
                    onChange={(e) => setWaiter(e.target.value)}
                  >
                    <option value="">Seleção automática</option>
                    {context.garcons.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.nome}
                      </option>
                    ))}
                  </select>
                  <small>
                    Na seleção automática, priorizamos quem tem menos pedidos em
                    andamento.
                  </small>
                </label>
              )}
              <dl className="totals">
                <div>
                  <dt>Subtotal</dt>
                  <dd>{money(cart.data.subtotal)}</dd>
                </div>
                <div>
                  <dt>Serviço (10%)</dt>
                  <dd>{money(cart.data.servico)}</dd>
                </div>
                <div className="total">
                  <dt>Total</dt>
                  <dd>{money(cart.data.total)}</dd>
                </div>
              </dl>
              <button
                className="primary wide"
                disabled={
                  busy || !cart.data.linhas.length || !cart.data.mesa_id
                }
                onClick={() => void checkout()}
              >
                {busy ? "Processando…" : "Confirmar pedido →"}
              </button>
              <small className="cart-foot">
                O pedido será confirmado com um garçom responsável pela entrega.
              </small>
            </>
          )}
        </aside>
      </div>
      {(selected || editing) && (
        <Modal
          title={(selected || editing).nome}
          close={() => {
            if (!busy) {
              setSelected(null);
              setEditing(null);
            }
          }}
        >
          {selected && <p className="muted">{selected.descricao}</p>}
          <ErrorBox message={error} />
          <label>
            Quantidade
            <input
              type="number"
              min={1}
              max={20}
              value={qty}
              onChange={(e) => setQty(Number(e.target.value))}
            />
          </label>
          <label>
            Observações
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={200}
              placeholder="Preferências ou restrições alimentares"
            />
          </label>
          <div className="pills notes">
            {notes.map((n) => (
              <button
                key={n}
                onClick={() => setNote((old) => (old ? old + "; " : "") + n)}
                disabled={note.length + n.length + 2 > 200}
              >
                {n}
              </button>
            ))}
          </div>
          <button
            className="primary wide"
            disabled={busy || qty < 1 || qty > 20 || !Number.isInteger(qty)}
            onClick={async () => {
              if (
                await change({
                  acao: editing ? "alterar" : "adicionar",
                  item_id: selected?.id,
                  linha_id: editing?.id,
                  quantidade: qty,
                  observacoes: note,
                })
              ) {
                setSelected(null);
                setEditing(null);
              }
            }}
          >
            {editing ? "Salvar" : "Adicionar"} ·{" "}
            {money(Number((selected || editing).preco) * qty)}
          </button>
        </Modal>
      )}
    </>
  );
}
