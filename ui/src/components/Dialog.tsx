import { forwardRef, HTMLAttributes, ReactNode } from 'react'
import { cn } from '../lib/utils'
import { X } from 'lucide-react'

// [R13]: Dialog component for configuration modal
// → provides: modal-ui-foundation

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: ReactNode
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      {/* Content wrapper */}
      <div className="relative z-50 max-h-[90vh] w-full max-w-4xl overflow-auto">
        {children}
      </div>
    </div>
  )
}

interface DialogContentProps extends HTMLAttributes<HTMLDivElement> { }

export const DialogContent = forwardRef<HTMLDivElement, DialogContentProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'relative bg-white rounded-lg shadow-xl border border-gray-200',
        'mx-4 my-8',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
)
DialogContent.displayName = 'DialogContent'

interface DialogHeaderProps extends HTMLAttributes<HTMLDivElement> {
  onClose?: () => void
}

export const DialogHeader = forwardRef<HTMLDivElement, DialogHeaderProps>(
  ({ className, children, onClose, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center justify-between p-6 border-b', className)}
      {...props}
    >
      <div className="flex-1">{children}</div>
      {onClose && (
        <button
          onClick={onClose}
          className="ml-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
      )}
    </div>
  )
)
DialogHeader.displayName = 'DialogHeader'

export const DialogTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h2
      ref={ref}
      className={cn('text-xl font-semibold text-gray-900', className)}
      {...props}
    />
  )
)
DialogTitle.displayName = 'DialogTitle'

export const DialogDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-gray-500 mt-1', className)}
      {...props}
    />
  )
)
DialogDescription.displayName = 'DialogDescription'

export const DialogBody = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('p-6', className)}
      {...props}
    />
  )
)
DialogBody.displayName = 'DialogBody'

export const DialogFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center justify-end gap-3 p-6 border-t bg-gray-50', className)}
      {...props}
    />
  )
)
DialogFooter.displayName = 'DialogFooter'
