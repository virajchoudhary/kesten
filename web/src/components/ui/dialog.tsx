"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/components/ui/utils";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogPortal = DialogPrimitive.Portal;
export const DialogClose = DialogPrimitive.Close;

export const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(function DialogOverlay({ className, ...props }, ref) {
  return (
    <DialogPrimitive.Overlay
      className={cn("fixed inset-0 z-50 bg-black/40 backdrop-blur-[1px]", className)}
      ref={ref}
      {...props}
    />
  );
});

export const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> & { hideClose?: boolean; placement?: "center" | "left" }
>(function DialogContent({ className, children, hideClose = false, placement = "center", ...props }, ref) {
  return (
    <DialogPortal>
      <DialogOverlay />
      <DialogPrimitive.Content
        className={cn(
          "fixed z-50 overflow-y-auto border border-border-subtle bg-surface text-foreground shadow-2xl outline-none",
          placement === "center"
            ? "left-1/2 top-1/2 grid max-h-[min(90vh,760px)] w-[min(92vw,560px)] -translate-x-1/2 -translate-y-1/2 gap-4 rounded-dialog p-5"
            : "inset-y-0 left-0 flex h-dvh max-h-dvh w-[min(88vw,360px)] flex-col p-0",
          className,
        )}
        ref={ref}
        {...props}
      >
        {children}
        {!hideClose && (
          <DialogPrimitive.Close asChild>
            <Button
              aria-label="Close dialog"
              className="absolute right-3 top-3"
              size="icon"
              variant="ghost"
            >
              <X aria-hidden="true" size={16} />
            </Button>
          </DialogPrimitive.Close>
        )}
      </DialogPrimitive.Content>
    </DialogPortal>
  );
});

export function DialogHeader({
  className,
  ...props
}: React.ComponentProps<"div">): React.JSX.Element {
  return <div className={cn("flex flex-col gap-1.5 pr-9", className)} {...props} />;
}

export function DialogTitle({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>): React.JSX.Element {
  return (
    <DialogPrimitive.Title
      className={cn("text-lg font-semibold leading-6", className)}
      {...props}
    />
  );
}

export function DialogDescription({
  className,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>): React.JSX.Element {
  return (
    <DialogPrimitive.Description
      className={cn("text-sm leading-5 text-secondary", className)}
      {...props}
    />
  );
}
