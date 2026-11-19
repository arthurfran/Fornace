import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { ErrorBox, Loading } from "./components/ui";
import { Login } from "./pages/Login";
import { Menu } from "./pages/Menu";
import { Orders, Kitchen } from "./pages/Orders";
import { Availability, Users, Analysis } from "./pages/Management";
export default function App() {
  const [context, setContext] = useState(null),
    [error, setError] = useState(""),
    [page, setPage] = useState(location.hash.slice(1) || "cardapio"),
    [notice, setNotice] = useState("");
  const refresh = useCallback(async () => {
    try {
      setContext(await api.request("contexto/"));
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }, []);
  useEffect(() => {
    void refresh();
    const hash = () => {
        setPage(location.hash.slice(1) || "cardapio");
        setNotice("");
      },
      reload = () => void refresh();
    window.addEventListener("hashchange", hash);
    window.addEventListener("context-refresh", reload);
    const id = setInterval(reload, 30000);
    return () => {
      clearInterval(id);
      window.removeEventListener("hashchange", hash);
      window.removeEventListener("context-refresh", reload);
    };
  }, [refresh]);
  const who = context?.identidade,
    user = who?.tipo === "usuario" ? who : null;
  const links = user
    ? [
        ...(user.garcom
          ? [
              ["salao", "Meus pedidos"],
              ["novo", "Novo pedido"],
            ]
          : []),
        ...(user.operador
          ? [
              ["cozinha", "Cozinha"],
              ["monitor", "Salão"],
              ["disponibilidade", "Disponibilidade"],
            ]
          : []),
        ...(user.operador?.perfil_gerencial ? [["analise", "Análises"]] : []),
        ...(user.administrador ? [["usuarios", "Usuários"]] : []),
      ]
    : [
        ["cardapio", "Cardápio"],
        ["pedidos", "Meus pedidos"],
      ];
  const defaultPage = links[0]?.[0] || "cardapio";
  useEffect(() => {
    if (context && page !== "login" && !links.some(([p]) => p === page))
      location.hash = defaultPage;
  }, [context, page, defaultPage]);
  async function loginDone() {
    const c = await api.request("contexto/");
    setContext(c);
    const u = c.identidade;
    location.hash =
      u.tipo === "usuario"
        ? u.garcom
          ? "salao"
          : u.operador
            ? "cozinha"
            : "usuarios"
        : "cardapio";
  }
  async function logout() {
    try {
      await api.request("logout/", "POST", {});
      await refresh();
      location.hash = "login";
    } catch (e) {
      setError(e.message);
    }
  }
  function confirmed(p) {
    location.hash = user ? "salao" : "pedidos";
    setTimeout(
      () =>
        setNotice(
          `Pedido ${p.codigo} confirmado. ${p.garcom} é o responsável pela entrega.`,
        ),
      10,
    );
  }
  const kitchen = page === "cozinha" && !!user?.operador;
  return (
    <div className={kitchen ? "app dark" : "app"}>
      <header className="topbar">
        <a className="brand" href={"#" + defaultPage}>
          fornace<span>CUCINA & INCONTRI</span>
        </a>
        <nav aria-label="Navegação principal">
          {links.map(([p, label]) => (
            <a
              key={p}
              href={"#" + p}
              aria-current={page === p ? "page" : undefined}
            >
              {label}
            </a>
          ))}
        </nav>
        <div className="account">
          {user?.administrador && (
            <a
              className="button"
              href="/admin/"
              target="_blank"
              rel="noreferrer"
            >
              Cadastros Django ↗
            </a>
          )}
          {who && who.tipo !== "anonimo" ? (
            <>
              <span>
                {who.nome}
                <small>{user ? "Equipe" : "Cliente"}</small>
              </span>
              <button className="text-button" onClick={() => void logout()}>
                Sair
              </button>
            </>
          ) : (
            <a href="#login" className="button">
              Entrar
            </a>
          )}
        </div>
      </header>
      <main>
        <ErrorBox message={error} />
        {notice && (
          <div className="notice" role="status">
            {notice}
            <button
              className="icon-button"
              aria-label="Fechar aviso"
              onClick={() => setNotice("")}
            >
              ×
            </button>
          </div>
        )}
        {!context ? (
          <Loading />
        ) : page === "login" ? (
          <Login done={loginDone} />
        ) : page === "cardapio" && !user ? (
          <Menu
            key={who?.tipo + String(who && "id" in who ? who.id : "")}
            context={context}
            origem="cliente"
            confirmed={confirmed}
          />
        ) : page === "novo" && user?.garcom ? (
          <Menu context={context} origem="salao" confirmed={confirmed} />
        ) : page === "pedidos" && !user ? (
          <Orders context={context} visao="cliente" />
        ) : page === "salao" && user?.garcom ? (
          <Orders context={context} visao="salao" />
        ) : page === "cozinha" && user?.operador ? (
          <Kitchen context={context} />
        ) : page === "monitor" && user?.operador ? (
          <Orders context={context} visao="monitor" />
        ) : page === "disponibilidade" && user?.operador ? (
          <Availability />
        ) : page === "analise" && user?.operador?.perfil_gerencial ? (
          <Analysis />
        ) : page === "usuarios" && user?.administrador ? (
          <Users />
        ) : (
          <Loading />
        )}
      </main>
      <footer className="site-footer">
        <span>fornace · cucina & incontri</span>
        <span>Da escolha ao último prato, tudo conectado.</span>
      </footer>
    </div>
  );
}
