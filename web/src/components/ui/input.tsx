"use client";

import * as React from "react";

import { cn } from "@/components/ui/utils";

export type InputProps = React.ComponentProps<"input">;

export function Input({ className, type = "text", ...props }: InputProps): React.JSX.Element {
  return (
    <input
      className={cn(
        "flex h-10 w-full rounded-control border border-control bg-surface px-3 py-2 text-sm text-foreground outline-none placeholder:text-secondary focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      type={type}
      {...props}
    />
  );
}
