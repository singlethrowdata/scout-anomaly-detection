import { ButtonHTMLAttributes, forwardRef } from 'react'
import { cn } from '../lib/utils'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'ghost' | 'success' | 'warning' | 'danger'
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        className={cn(
          'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
          'disabled:opacity-50 disabled:pointer-events-none',
          {
            // Variant styles
            'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'default',
            'bg-secondary text-secondary-foreground hover:bg-secondary/80': variant === 'secondary',
            'border border-input hover:bg-accent hover:text-accent-foreground': variant === 'outline',
            'hover:bg-accent hover:text-accent-foreground': variant === 'ghost',
            'bg-scout-green text-white hover:bg-scout-green/90': variant === 'success',
            'bg-scout-yellow text-white hover:bg-scout-yellow/90': variant === 'warning',
            'bg-scout-red text-white hover:bg-scout-red/90': variant === 'danger',
            // Size styles
            'h-10 py-2 px-4': size === 'default',
            'h-9 px-3 rounded-md': size === 'sm',
            'h-11 px-8 rounded-md': size === 'lg',
            'h-10 w-10': size === 'icon',
          },
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)

Button.displayName = 'Button'

export { Button }
