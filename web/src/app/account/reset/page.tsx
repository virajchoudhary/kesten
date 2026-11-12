import type { Metadata } from "next";
import { KeyRound } from "lucide-react";

import { PublicPageFrame } from "@/components/public-page-frame";
import { TokenPasswordForm } from "@/features/account/token-password-form";

export const metadata: Metadata = {
  title: "Reset password",
  referrer: "no-referrer",
};

export default function ResetPasswordPage(): React.JSX.Element {
  return (
    <PublicPageFrame>
      <article className="mx-auto max-w-md border-y border-border-subtle py-8 sm:py-10">
        <div className="mb-6 flex size-10 items-center justify-center rounded-control bg-accent/10 text-accent">
          <KeyRound aria-hidden="true" size={18} />
        </div>
        <h1 className="text-2xl font-semibold leading-8">Set a new password</h1>
        <p className="mt-2 text-sm text-secondary">
          Use the one-time reset link issued by your account operator.
        </p>
        <div className="mt-7">
          <TokenPasswordForm purpose="password-reset" />
        </div>
      </article>
    </PublicPageFrame>
  );
}
