import * as React from "react"
import { cn } from "@/src/lib/utils"
import { Info } from "lucide-react"

export interface FieldHintProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export function FieldHint({ children, className, ...props }: FieldHintProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-2 text-sm text-muted-foreground bg-muted/50 p-3 rounded-md",
        className
      )}
      {...props}
    >
      <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
      <span>{children}</span>
    </div>
  )
}
