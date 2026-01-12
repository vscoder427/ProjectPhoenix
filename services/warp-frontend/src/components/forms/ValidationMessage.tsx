import * as React from "react"
import { cn } from "@/src/lib/utils"
import { CheckCircle2, Circle, AlertCircle } from "lucide-react"

export interface ValidationMessageProps extends React.HTMLAttributes<HTMLDivElement> {
  type?: "hint" | "error" | "success"
  children: React.ReactNode
}

export function ValidationMessage({
  type = "hint",
  children,
  className,
  ...props
}: ValidationMessageProps) {
  const icons = {
    hint: Circle,
    success: CheckCircle2,
    error: AlertCircle,
  }

  const Icon = icons[type]

  return (
    <div
      className={cn(
        "flex items-start gap-2 text-sm",
        {
          "text-muted-foreground": type === "hint",
          "text-green-600 dark:text-green-400": type === "success",
          "text-destructive": type === "error",
        },
        className
      )}
      {...props}
    >
      <Icon className="h-4 w-4 mt-0.5 flex-shrink-0" />
      <span>{children}</span>
    </div>
  )
}
