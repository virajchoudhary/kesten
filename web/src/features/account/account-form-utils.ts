import { ApiError } from "@/lib/api/client";

export function fieldError(error: ApiError | null, field: string): string | null {
  if (error === null) {
    return null;
  }

  const value = error.fieldErrors[field];
  if (typeof value === "string") {
    return value;
  }
  return value?.join(" ") ?? null;
}

export function normalizeAccountError(error: unknown, fallback: string): ApiError {
  if (error instanceof ApiError) {
    return error;
  }

  return new ApiError({
    status: 500,
    code: "account_request_failed",
    message: fallback,
  });
}
