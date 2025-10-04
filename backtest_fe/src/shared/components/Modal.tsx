import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { cn } from '@/shared/lib/core/utils';

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  size?: ModalSize;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  showCloseButton?: boolean;
  className?: string;
  overlayClassName?: string;
  contentClassName?: string;
  footer?: React.ReactNode;
}

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  closeOnOverlayClick = true,
  className = '',
  contentClassName = '',
  footer,
}) => {
  const getSizeClasses = (size: ModalSize): string => {
    const sizes = {
      sm: 'sm:max-w-sm',
      md: 'sm:max-w-md',
      lg: 'sm:max-w-lg',
      xl: 'sm:max-w-xl',
      full: 'sm:max-w-full sm:mx-4',
    };
    return sizes[size];
  };

  const fallbackDescription = '이 창의 자세한 내용을 아래에서 확인할 수 있습니다.';

  return (
    <Dialog 
      open={isOpen} 
      onOpenChange={(open: boolean) => !open && onClose()}
    >
      <DialogContent 
        className={cn(getSizeClasses(size), className, contentClassName)}
        onInteractOutside={(e: Event) => {
          if (!closeOnOverlayClick) {
            e.preventDefault();
          }
        }}
      >
        <DialogHeader className={!title && !description ? 'sr-only' : undefined}>
          {title && <DialogTitle>{title}</DialogTitle>}
          <DialogDescription className={description ? undefined : 'sr-only'}>
            {description ?? fallbackDescription}
          </DialogDescription>
        </DialogHeader>
        
        {children}
        
        {footer && (
          <DialogFooter>
            {footer}
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default Modal;
