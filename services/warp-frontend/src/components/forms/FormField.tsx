import * as React from "react"
import { Label } from "@/src/components/ui/label"
import { cn } from "@/src/lib/utils"

export interface FormFieldProps extends React.HTMLAttributes<HTMLDivElement> {
  label?: string
  hint?: string
  error?: string
  required?: boolean
  children: React.ReactNode
}

export function FormField({
  label,
  hint,
  error,
  required,
  children,
  className,
  ...props
}: FormFieldProps) {
  const id = React.useId()

  return (
    <div className={cn("space-y-2", className)} {...props}>
      {label && (
        <Label htmlFor={id} className="text-base">
          {label}
          {required && (
            <span className="ml-1 text-sm text-muted-foreground">
              (Helps us support you better)
            </span>
          )}
        </Label>
      )}

      {React.cloneElement(children as React.ReactElement, {
        id,
        "aria-invalid": error ? "true" : "false",
        "aria-describedby": error ? `${id}-error` : hint ? `${id}-hint` : undefined,
      })}

      {hint && !error && (
        <p id={`${id}-hint`} className="text-sm text-muted-foreground">
          {hint}
        </p>
      )}

      {error && (
        <p id={`${id}-error`} className="text-sm text-destructive font-medium">
          {error}
        </p>
      )}
    </div>
  )
}
