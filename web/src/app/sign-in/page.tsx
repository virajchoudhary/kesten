import type { Metadata } from "next";
import { LockKeyhole } from "lucide-react";

import { PublicPageFrame } from "@/components/public-page-frame";
import { SignInForm } from "@/features/session/sign-in-form";

export const metadata: Metadata = { title: "Sign in" };

export default function SignInPage(): React.JSX.Element {
  return (
    <PublicPageFrame>
      <div className="mx-auto max-w-md border-y border-border-subtle py-8 sm:py-10">
        <div className="mb-6 flex size-10 items-center justify-center rounded-control bg-accent/10 text-accent">
          <LockKeyhole aria-hidden="true" size={18} />
        </div>
        <h1 className="text-2xl font-semibold leading-8">Sign in to your workspace</h1>
        <p className="mt-2 text-sm text-secondary">Private access for invited research accounts.</p>
        <div className="mt-7">
          <SignInForm />
        </div>
      </div>
    </PublicPageFrame>
  );
}
