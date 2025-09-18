import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface FormSectionProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
}

export const FormSection = ({
  title,
  description,
  actions,
  footer,
  children,
  className,
  contentClassName,
}: FormSectionProps) => {
  return (
    <section
      className={cn(
        'overflow-hidden rounded-2xl border border-border/70 bg-card/60 shadow-sm backdrop-blur-sm',
        className,
      )}
    >
      <header className="flex flex-col gap-4 border-b border-border/60 px-5 py-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <h3 className="text-lg font-semibold leading-tight text-foreground">{title}</h3>
          {description ? (
            <p className="text-sm text-muted-foreground">{description}</p>
          ) : null}
        </div>
        {actions ? <div className="flex items-center gap-3 sm:min-w-[200px] sm:justify-end">{actions}</div> : null}
      </header>
      <div className={cn('px-5 py-5', contentClassName)}>{children}</div>
      {footer ? (
        <footer className="border-t border-border/60 bg-card/60 px-5 py-4 text-sm text-muted-foreground">
          {footer}
        </footer>
      ) : null}
    </section>
  );
};

export default FormSection;
