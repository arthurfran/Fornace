/** Fronteira HTTP única: cookies HttpOnly, CSRF e tratamento de erros. */
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}
export class ApiClient {
  csrf = "";
  async request(path, method = "GET", body) {
    const response = await fetch("/api/" + path, {
      method,
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        ...(method !== "GET"
          ? {
              "X-CSRFToken": this.csrf,
            }
          : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await response.text();
    let result;
    try {
      result = JSON.parse(text);
    } catch {
      throw new ApiError(
        "O serviço não respondeu como esperado. Tente novamente.",
        response.status,
      );
    }
    if (!response.ok)
      throw new ApiError(
        result.erro || "Não foi possível concluir a operação.",
        response.status,
      );
    if (result.csrf) this.csrf = result.csrf;
    return result;
  }
}
export const api = new ApiClient();
export const money = (n) =>
  Number(n).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
export const date = (value) =>
  new Date(value).toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });
export const labels = {
  AGUARDANDO: "Aguardando",
  RECEBIDO: "Recebido",
  EM_PREPARO: "Em preparo",
  PRONTO: "Pronto",
  ENTREGUE: "Entregue",
};
