import type { Metadata } from "next";

import { AccountSecurityPage } from "@/features/account/account-security-page";

export const metadata: Metadata = { title: "Account security" };

export default function AccountPage(): React.JSX.Element {
  return <AccountSecurityPage />;
}
