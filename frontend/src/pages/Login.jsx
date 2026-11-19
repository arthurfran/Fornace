import { useState } from "react";
import { api } from "../api";
import { ErrorBox } from "../components/ui";
export function Login({ done }) {
  const [kind, setKind] = useState("cliente"),
    [register, setRegister] = useState(false),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    const f = new FormData(e.currentTarget);
    try {
      await api.request(
        register ? "cadastro/" : "login/",
        "POST",
        register
          ? {
              nome: f.get("nome"),
              email: f.get("login"),
              senha: f.get("senha"),
            }
          : {
              tipo: kind,
              login: f.get("login"),
              senha: f.get("senha"),
            },
      );
      await done();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="login-layout">
      <div className="login-story">
        <p className="eyebrow">À mesa, do seu jeito.</p>
        <h1>
          Boa comida.
          <br />
          Tudo no seu tempo.
        </h1>
        <p>
          Escolha seus pratos, acompanhe o preparo e deixe o resto com a nossa
          equipe.
        </p>
        <img
          src="/assets/conchiglioni.jpeg"
          alt="Conchiglioni servido na Fornace"
        />
      </div>
      <div className="login-card">
        <p className="eyebrow">FORNACE · ACESSO</p>
        <h2>{register ? "Crie sua conta" : "Que bom ter você aqui."}</h2>
        <div className="segmented">
          <button
            className={kind === "cliente" ? "selected" : ""}
            onClick={() => {
              setKind("cliente");
              setError("");
            }}
          >
            Sou cliente
          </button>
          <button
            className={kind === "usuario" ? "selected" : ""}
            onClick={() => {
              setKind("usuario");
              setRegister(false);
              setError("");
            }}
          >
            Sou da equipe
          </button>
        </div>
        <ErrorBox message={error} />
        <form onSubmit={submit}>
          {register && (
            <label>
              Nome
              <input name="nome" required maxLength={120} autoComplete="name" />
            </label>
          )}
          <label>
            {kind === "cliente" ? "E-mail" : "Login"}
            <input
              name="login"
              type={kind === "cliente" ? "email" : "text"}
              required
              maxLength={120}
              autoComplete="username"
            />
          </label>
          <label>
            Senha
            <input
              name="senha"
              type="password"
              required
              minLength={8}
              maxLength={64}
              autoComplete={register ? "new-password" : "current-password"}
            />
          </label>
          <button className="primary" disabled={busy}>
            {busy ? "Entrando…" : register ? "Cadastrar" : "Entrar"}
          </button>
        </form>
        {kind === "cliente" && (
          <>
            <button
              className="text-button"
              onClick={() => setRegister(!register)}
            >
              {register ? "Já tenho uma conta" : "Criar uma conta"}
            </button>
            <a className="guest-link" href="#cardapio">
              Continuar sem identificação →
            </a>
            <small>
              Seu pedido será vinculado à mesa. Para manter o histórico pessoal,
              entre antes de confirmar.
            </small>
          </>
        )}
      </div>
    </section>
  );
}
