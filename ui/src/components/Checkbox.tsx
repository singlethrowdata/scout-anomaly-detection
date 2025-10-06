import { InputHTMLAttributes, forwardRef, ReactNode } from 'react'
import { cn } from '../lib/utils'
import { Check } from 'lucide-react'

// [R13]: Checkbox component for event selection
// → provides: event-selection-ui

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: ReactNode
  description?: ReactNode
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, description, checked, ...props }, ref) => {
    return (
      <label className="flex items-start gap-3 cursor-pointer group">
        <div className="relative flex items-center justify-center">
          <input
            type="checkbox"
            ref={ref}
            checked={checked}
            className="sr-only"
            {...props}
          />
          <div
            className={cn(
              'h-5 w-5 rounded border-2 flex items-center justify-center transition-colors',
              checked
                ? 'bg-scout-blue border-scout-blue'
                : 'border-gray-300 group-hover:border-gray-400',
              className
            )}
          >
            {checked && <Check className="h-3.5 w-3.5 text-white" />}
          </div>
        </div>
        {(label || description) && (
          <div className="flex-1 -mt-0.5">
            {label && (
              <div className="text-sm font-medium text-gray-900">{label}</div>
            )}
            {description && (
              <div className="text-xs text-gray-500 mt-0.5">{description}</div>
            )}
          </div>
        )}
      </label>
    )
  }
)

Checkbox.displayName = 'Checkbox'
