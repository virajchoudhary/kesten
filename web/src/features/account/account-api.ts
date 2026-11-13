import { z } from "zod";

import { ApiError, requestJson } from "@/lib/api/client";

export const AccountTokenSchema = z.string().min(1).max(128);
const PasswordSchema = z.string().min(1).max(256);

export const InvitationAcceptRequestSchema = z
  .object({
    token: AccountTokenSchema,
    new_password: PasswordSchema,
    confirm_password: PasswordSchema,
  })
  .strict();

export const PasswordResetConfirmRequestSchema = z
  .object({
    token: AccountTokenSchema,
    new_password: PasswordSchema,
    confirm_password: PasswordSchema,
  })
  .strict();

export const ChangePasswordRequestSchema = z
  .object({
    current_password: PasswordSchema,
    new_password: PasswordSchema,
    confirm_password: PasswordSchema,
  })
  .strict();

export const RevokeOtherSessionsRequestSchema = z
  .object({
    scope: z.literal("others"),
  })
  .strict();

const InvitationAcceptedResponseSchema = z
  .object({
    created: z.literal(true),
  })
  .strict();

const PasswordChangedResponseSchema = z
  .object({
    password_changed: z.literal(true),
  })
  .strict();

const SessionRevocationResponseSchema = z.discriminatedUnion("revoked", [
  z
    .object({
      revoked: z.literal("others"),
      authenticated: z.literal(true),
      csrf_token: z.string().min(1),
    })
    .strict(),
  z
    .object({
      revoked: z.literal("all"),
      authenticated: z.literal(false),
      csrf_token: z.null(),
    })
    .strict(),
]);

export type AccountToken = z.infer<typeof AccountTokenSchema>;
export type InvitationAcceptRequest = z.infer<typeof InvitationAcceptRequestSchema>;
export type PasswordResetConfirmRequest = z.infer<typeof PasswordResetConfirmRequestSchema>;
export type ChangePasswordRequest = z.infer<typeof ChangePasswordRequestSchema>;
export type SessionRevocationResponse = z.infer<typeof SessionRevocationResponseSchema>;
export type OtherSessionsRevoked = Extract<
  SessionRevocationResponse,
  { revoked: "others" }
>;

async function postAccountJson<TRequest, TResponse>(options: {
  path: string;
  payload: TRequest;
  requestSchema: z.ZodType<TRequest>;
  responseSchema: z.ZodType<TResponse>;
  csrfToken: string;
}): Promise<TResponse> {
  const parsedRequest = options.requestSchema.safeParse(options.payload);
  if (!parsedRequest.success) {
    throw new ApiError({
      status: 0,
      code: "invalid_request",
      message: "Review the account form fields and try again.",
    });
  }

  return requestJson({
    path: options.path,
    schema: options.responseSchema,
    init: {
      method: "POST",
      body: JSON.stringify(parsedRequest.data),
    },
    csrfToken: options.csrfToken,
  });
}

export function acceptInvitation(
  payload: InvitationAcceptRequest,
  csrfToken: string,
): Promise<z.infer<typeof InvitationAcceptedResponseSchema>> {
  return postAccountJson({
    path: "/api/v1/account/invitations/accept/",
    payload,
    requestSchema: InvitationAcceptRequestSchema,
    responseSchema: InvitationAcceptedResponseSchema,
    csrfToken,
  });
}

export function confirmPasswordReset(
  payload: PasswordResetConfirmRequest,
  csrfToken: string,
): Promise<z.infer<typeof PasswordChangedResponseSchema>> {
  return postAccountJson({
    path: "/api/v1/account/password-reset/confirm/",
    payload,
    requestSchema: PasswordResetConfirmRequestSchema,
    responseSchema: PasswordChangedResponseSchema,
    csrfToken,
  });
}

export function changePassword(
  payload: ChangePasswordRequest,
  csrfToken: string,
): Promise<z.infer<typeof PasswordChangedResponseSchema>> {
  return postAccountJson({
    path: "/api/v1/account/password/change/",
    payload,
    requestSchema: ChangePasswordRequestSchema,
    responseSchema: PasswordChangedResponseSchema,
    csrfToken,
  });
}

export async function revokeOtherSessions(
  csrfToken: string,
): Promise<OtherSessionsRevoked> {
  const response = await postAccountJson({
    path: "/api/v1/account/sessions/revoke/",
    payload: { scope: "others" },
    requestSchema: RevokeOtherSessionsRequestSchema,
    responseSchema: SessionRevocationResponseSchema,
    csrfToken,
  });

  if (response.revoked !== "others") {
    throw new ApiError({
      status: 502,
      code: "invalid_response",
      message: "The account service did not confirm that other sessions were revoked.",
    });
  }

  return response;
}
