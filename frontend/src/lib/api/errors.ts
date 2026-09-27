/** RFC 9457 problem details returned by the AxiomQ API. */
export interface FieldError {
  field: string;
  message: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly title: string;
  readonly detail: string | undefined;
  readonly fieldErrors: FieldError[];
  readonly retryAfter: number | undefined;

  constructor(status: number, body: unknown) {
    const problem = (typeof body === "object" && body !== null ? body : {}) as Record<
      string,
      unknown
    >;
    const title = typeof problem.title === "string" ? problem.title : "Request failed";
    super(title);
    this.name = "ApiError";
    this.status = status;
    this.title = title;
    this.code = typeof problem.type === "string" ? (problem.type.split("/").pop() ?? "") : "";
    this.detail = typeof problem.detail === "string" ? problem.detail : undefined;
    this.fieldErrors = Array.isArray(problem.errors)
      ? (problem.errors as unknown[]).filter(isFieldError)
      : [];
    this.retryAfter = typeof problem.retry_after === "number" ? problem.retry_after : undefined;
  }

  /** Message suitable for a form-level alert. */
  get userMessage(): string {
    if (this.status === 429 && this.retryAfter) {
      const minutes = Math.ceil(this.retryAfter / 60);
      return `Too many attempts. Try again in ${minutes} minute${minutes === 1 ? "" : "s"}.`;
    }
    return this.detail && this.fieldErrors.length === 0 ? this.detail : this.title;
  }

  fieldError(field: string): string | undefined {
    return this.fieldErrors.find((e) => e.field === field)?.message;
  }
}

function isFieldError(value: unknown): value is FieldError {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as FieldError).field === "string" &&
    typeof (value as FieldError).message === "string"
  );
}
