import {
  ApiErrorResponseSchema,
  InstrumentListSchema,
  MarketResponseSchema,
  SessionSchema,
  type ApiErrorResponse,
  type Credentials,
  type Instrument,
  type InstrumentList,
  type MarketResponse,
  type Session,
  type DataMode,
  type MarketRange,
} from "@/lib/api/schemas";
import { InstrumentSchema } from "@/lib/api/schemas";
import { z } from "zod";

export type { DataMode, MarketRange } from "@/lib/api/schemas";
export const SESSION_RECHECK_EVENT = "cadrisyn:session-recheck";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;
  readonly fieldErrors: Record<string, string | string[]>;

  constructor(options: {
    status: number;
    code: string;
    message: string;
    requestId?: string | null;
    fieldErrors?: Record<string, string | string[]>;
  }) {
    super(options.message);
    this.name = "ApiError";
    this.status = options.status;
    this.code = options.code;
    this.requestId = options.requestId ?? null;
    this.fieldErrors = options.fieldErrors ?? {};
  }
}

async function readJson(response: Response): Promise<unknown> {
  try {
    const payload: unknown = await response.json();
    return payload;
  } catch {
    return null;
  }
}

function apiErrorFrom(response: Response, payload: unknown): ApiError {
  const parsedError = ApiErrorResponseSchema.safeParse(payload);
  if (parsedError.success) {
    if (
      typeof window !== "undefined" &&
      (response.status === 401 || response.status === 403) &&
      ["permission_denied", "authentication_required"].includes(parsedError.data.code)
    ) {
      window.dispatchEvent(new Event(SESSION_RECHECK_EVENT));
    }
    return new ApiError({
      status: response.status,
      code: parsedError.data.code,
      message: parsedError.data.message,
      requestId: parsedError.data.request_id,
      fieldErrors: parsedError.data.field_errors,
    });
  }

  return new ApiError({
    status: response.status,
    code: "request_failed",
    message: "The request could not be completed. Try again.",
  });
}

type JsonRequest<T> = {
  path: string;
  schema: z.ZodType<T>;
  init?: RequestInit;
  csrfToken?: string;
  signal?: AbortSignal;
};

export async function requestJson<T>(options: JsonRequest<T>): Promise<T> {
  return (await requestJsonDocument(options)).data;
}

export async function requestJsonDocument<T>(options: JsonRequest<T>): Promise<{ data: T; source: string }> {
  const headers = new Headers(options.init?.headers);
  headers.set("Accept", "application/json");
  if (options.init?.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (options.csrfToken !== undefined) {
    headers.set("X-CSRFToken", options.csrfToken);
  }

  let response: Response;
  try {
    response = await fetch(options.path, {
      ...options.init,
      headers,
      cache: "no-store",
      credentials: "same-origin",
      signal: options.signal,
    });
  } catch (error: unknown) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError({
      status: 0,
      code: "network_error",
      message: "The API could not be reached. Check that the local services are running.",
    });
  }

  const source = await response.text();
  let payload: unknown = null;
  try {
    payload = JSON.parse(source);
  } catch {
    payload = null;
  }
  if (!response.ok) {
    throw apiErrorFrom(response, payload);
  }

  const parsed = options.schema.safeParse(payload);
  if (!parsed.success) {
    throw new ApiError({
      status: 502,
      code: "invalid_response",
      message: "The API returned data that did not match the market workspace contract.",
    });
  }

  return { data: parsed.data, source };
}

async function requestNoContent(options: {
  path: string;
  method: "DELETE";
  csrfToken: string;
  signal?: AbortSignal;
}): Promise<void> {
  let response: Response;
  try {
    response = await fetch(options.path, {
      method: options.method,
      headers: { Accept: "application/json", "X-CSRFToken": options.csrfToken },
      cache: "no-store",
      credentials: "same-origin",
      signal: options.signal,
    });
  } catch (error: unknown) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError({
      status: 0,
      code: "network_error",
      message: "The API could not be reached. Check that the local services are running.",
    });
  }

  if (!response.ok) {
    throw apiErrorFrom(response, await readJson(response));
  }
}

export function getSession(signal?: AbortSignal): Promise<Session> {
  return requestJson({ path: "/api/v1/session/", schema: SessionSchema, signal });
}

export function login(credentials: Credentials, csrfToken: string): Promise<Session> {
  return requestJson({
    path: "/api/v1/session/",
    schema: SessionSchema,
    init: { method: "POST", body: JSON.stringify(credentials) },
    csrfToken,
  });
}

export function logout(csrfToken: string): Promise<Session> {
  return requestJson({
    path: "/api/v1/session/",
    schema: SessionSchema,
    init: { method: "DELETE" },
    csrfToken,
  });
}

export function searchInstruments(query: string, signal?: AbortSignal): Promise<InstrumentList> {
  const params = new URLSearchParams({ query });
  return requestJson({
    path: `/api/v1/instruments/?${params.toString()}`,
    schema: InstrumentListSchema,
    signal,
  });
}

export function getWatchlist(signal?: AbortSignal): Promise<InstrumentList> {
  return requestJson({
    path: "/api/v1/watchlist/",
    schema: InstrumentListSchema,
    signal,
  });
}

export function addWatchlistInstrument(instrumentId: string, csrfToken: string): Promise<InstrumentList> {
  return requestJson({
    path: "/api/v1/watchlist/",
    schema: InstrumentListSchema,
    init: { method: "POST", body: JSON.stringify({ instrument_id: instrumentId }) },
    csrfToken,
  });
}

export function removeWatchlistInstrument(instrumentId: string, csrfToken: string): Promise<void> {
  return requestNoContent({
    path: `/api/v1/watchlist/${encodeURIComponent(instrumentId)}/`,
    method: "DELETE",
    csrfToken,
  });
}

export async function getMarketBars(options: {
  instrumentId: string;
  range: MarketRange;
  mode: DataMode;
  signal?: AbortSignal;
}): Promise<MarketResponse> {
  const params = new URLSearchParams({ range: options.range, mode: options.mode });
  const response = await requestJson({
    path: `/api/v1/instruments/${encodeURIComponent(options.instrumentId)}/bars/?${params.toString()}`,
    schema: MarketResponseSchema,
    signal: options.signal,
  });

  const expectedMode = options.mode === "demo" ? "demo" : "delayed";
  if (response.provenance.data_mode !== expectedMode) {
    throw new ApiError({
      status: 502,
      code: "market_mode_mismatch",
      message: "The API returned a different data provenance category than requested.",
    });
  }

  return response;
}

export function errorResponse(value: unknown): ApiErrorResponse | null {
  const parsed = ApiErrorResponseSchema.safeParse(value);
  return parsed.success ? parsed.data : null;
}

export function instrumentFromUnknown(value: unknown): Instrument | null {
  const parsed = InstrumentSchema.safeParse(value);
  return parsed.success ? parsed.data : null;
}
