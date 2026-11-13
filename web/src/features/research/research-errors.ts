import { ApiError } from "@/lib/api/client";

export function asResearchError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }
  return new ApiError({
    status: 500,
    code: "research_request_failed",
    message: "The research request could not be completed. Try again.",
  });
}
