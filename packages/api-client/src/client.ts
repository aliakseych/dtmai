import createClient, { type Client, type Middleware } from "openapi-fetch";
import { ApiError, NetworkError, type Problem } from "./errors";
import type { components, paths } from "./generated/schema";

export type Tokens = components["schemas"]["TokensOut"];

export interface ApiClientOptions {
  baseUrl: string;
  /** Current access token (sync or async). */
  getToken: () => string | null | undefined | Promise<string | null | undefined>;
  /** Current refresh token. When omitted no rotation is attempted and a 401 is final. */
  getRefreshToken?: () => string | null | undefined;
  /** Called with the rotated pair after a successful refresh; persist it. */
  setTokens?: (tokens: Tokens) => void;
  /** Called when the session cannot be recovered (refresh failed / missing). */
  onUnauthorized?: () => void;
  /** Content locale sent as `Accept-Language`. */
  locale?: string | (() => string);
}

export interface RawOptions {
  query?: Record<string, unknown>;
  body?: unknown;
  signal?: AbortSignal;
}

export interface ApiClient {
  /** Fully typed openapi-fetch client over the generated `paths`. */
  client: Client<paths>;
  /** Typed call that unwraps `data` or throws {@link ApiError}. */
  unwrap<T>(p: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T>;
  /**
   * Untyped call for operations that are not in the generated schema yet.
   * Goes through the same auth / refresh / locale middleware. Remove usages after `bun run gen:api`.
   */
  raw<T>(method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE", path: string, opts?: RawOptions): Promise<T>;
}

const NO_RETRY = [
  "/v1/identity/login",
  "/v1/identity/register",
  "/v1/identity/refresh",
  "/v1/identity/email/verify",
  "/v1/identity/email/resend",
  "/v1/identity/password/forgot",
  "/v1/identity/password/reset",
];

export function createApiClient(opts: ApiClientOptions): ApiClient {
  const baseUrl = opts.baseUrl.replace(/\/+$/, "");
  const replay = new Map<string, Request>();
  let inflight: Promise<boolean> | null = null;

  const locale = () => (typeof opts.locale === "function" ? opts.locale() : opts.locale);

  /** Single-flight refresh-token rotation. Resolves true when a new pair was stored. */
  async function refresh(): Promise<boolean> {
    const rt = opts.getRefreshToken?.();
    if (!rt) return false;
    inflight ??= (async () => {
      try {
        const res = await fetch(`${baseUrl}/v1/identity/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: rt }),
        });
        if (!res.ok) return false;
        opts.setTokens?.((await res.json()) as Tokens);
        return true;
      } catch {
        return false;
      } finally {
        setTimeout(() => (inflight = null), 0);
      }
    })();
    return inflight;
  }

  const middleware: Middleware = {
    async onRequest({ request, id, schemaPath }) {
      const token = await opts.getToken();
      if (token) request.headers.set("Authorization", `Bearer ${token}`);
      const lang = locale();
      if (lang) request.headers.set("Accept-Language", lang);
      if (!NO_RETRY.includes(schemaPath)) replay.set(id, request.clone());
      return request;
    },
    async onResponse({ response, id, schemaPath }) {
      const original = replay.get(id);
      replay.delete(id);
      if (response.status !== 401 || !original || NO_RETRY.includes(schemaPath)) return response;
      if (await refresh()) {
        const token = await opts.getToken();
        if (token) original.headers.set("Authorization", `Bearer ${token}`);
        const retried = await fetch(original);
        if (retried.status !== 401) return retried;
      }
      opts.onUnauthorized?.();
      return response;
    },
  };

  const client = createClient<paths>({ baseUrl });
  client.use(middleware);

  async function toError(response: Response, error: unknown): Promise<ApiError> {
    let problem = error as Problem | undefined;
    if (problem === undefined || typeof problem !== "object") {
      problem = undefined;
      try {
        problem = (await response.clone().json()) as Problem;
      } catch {
        /* not json */
      }
    }
    return new ApiError(response.status, problem, response.statusText);
  }

  async function unwrap<T>(p: Promise<{ data?: T; error?: unknown; response: Response }>): Promise<T> {
    let r;
    try {
      r = await p;
    } catch (e) {
      throw e instanceof ApiError ? e : new NetworkError(e);
    }
    if (r.error !== undefined || !r.response.ok) throw await toError(r.response, r.error);
    return r.data as T;
  }

  async function raw<T>(method: string, path: string, o: RawOptions = {}): Promise<T> {
    const loose = client as unknown as {
      request: (m: string, p: string, init: unknown) => Promise<{ data?: T; error?: unknown; response: Response }>;
    };
    const form = typeof FormData !== "undefined" && o.body instanceof FormData;
    return unwrap<T>(
      loose.request(method, path, {
        params: { query: o.query },
        body: o.body,
        signal: o.signal,
        ...(form ? { bodySerializer: (b: unknown) => b } : {}),
      }),
    );
  }

  return { client, unwrap, raw };
}
