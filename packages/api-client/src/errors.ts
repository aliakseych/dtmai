/** RFC 7807 problem body emitted by the API (`application/problem+json`). */
export interface Problem {
  type?: string;
  title?: string;
  status?: number;
  code?: string;
  detail?: string | unknown;
}

/** Typed API failure. `code` is the stable machine code from the API; `status` is the HTTP status. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly problem: Problem | undefined;

  constructor(status: number, problem: Problem | undefined, fallback?: string) {
    super(ApiError.describe(status, problem, fallback));
    this.name = "ApiError";
    this.status = status;
    this.code = problem?.code ?? `http_${status}`;
    this.problem = problem;
  }

  static describe(status: number, problem: Problem | undefined, fallback?: string): string {
    const d = problem?.detail;
    if (typeof d === "string" && d) return d;
    if (Array.isArray(d) && d.length > 0) {
      return d.map((e: { loc?: unknown[]; msg?: string }) => `${(e.loc ?? []).slice(1).join(".")}: ${e.msg ?? ""}`).join("; ");
    }
    return problem?.title ?? fallback ?? `HTTP ${status}`;
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }
  get isForbidden(): boolean {
    return this.status === 403;
  }
}

/** Network-level failure (offline, CORS, DNS). */
export class NetworkError extends Error {
  constructor(cause: unknown) {
    super("Network error");
    this.name = "NetworkError";
    this.cause = cause;
  }
}
