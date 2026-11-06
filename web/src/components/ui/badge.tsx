import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/components/ui/utils";

const badgeVariants = cva("inline-flex items-center gap-1.5 rounded-control px-2 py-1 text-xs font-medium", {
  variants: {
    variant: {
      neutral: "bg-raised text-secondary",
      accent: "bg-accent/10 text-accent",
      positive: "bg-positive/10 text-positive",
      negative: "bg-negative/10 text-negative",
      warning: "bg-warning/10 text-warning",
      demo: "border border-warning/50 bg-warning/10 text-warning",
    },
  },
  defaultVariants: { variant: "neutral" },
});

export type BadgeProps = React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>;

export function Badge({ className, variant, ...props }: BadgeProps): React.JSX.Element {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { badgeVariants };
