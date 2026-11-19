import { useEffect, useRef } from "react";
import { labels } from "../api";
export function Badge({ status }) {
  return (
    <span className={"badge " + status.toLowerCase()}>
      {labels[status] || status}
    </span>
  );
}
export function ErrorBox({ message }) {
  return message ? (
    <div className="error" role="alert">
      {message}
    </div>
  ) : null;
}
export function Empty({ title, children }) {
  return (
    <div className="empty">
      <span aria-hidden="true">◯</span>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function Loading() {
  return (
    <p role="status" className="muted">
      Carregando…
    </p>
  );
}
export function Modal({ title, close, children }) {
  const ref = useRef(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => dialog?.close();
  }, []);
  return (
    <dialog ref={ref} onCancel={close} className="modal">
      <header>
        <h2>{title}</h2>
        <button className="icon-button" onClick={close} aria-label="Fechar">
          ×
        </button>
      </header>
      {children}
    </dialog>
  );
}
export function PageTitle({ eyebrow, title, children }) {
  return (
    <header className="page-title">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      {children}
    </header>
  );
}
