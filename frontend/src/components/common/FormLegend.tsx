import { ReactNode } from 'react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface FormLegendProps {
  items: Array<{ label: string; tone?: 'default' | 'muted' | 'accent' | 'warn' }>;
  icon?: ReactNode;
  className?: string;
}

export const FormLegend = ({ items, icon, className }: FormLegendProps) => {
  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-2 rounded-full border border-border/60 bg-background px-3 py-1.5 text-xs text-muted-foreground shadow-sm',
        className,
      )}
    >
      {icon ? <span className="text-muted-foreground/80">{icon}</span> : null}
      {items.map(({ label, tone = 'default' }) => (
        <Badge
          key={label}
          variant="outline"
          className={cn('rounded-full border-border/50 bg-transparent font-medium', {
            'text-muted-foreground': tone === 'muted',
            'text-primary border-primary/40': tone === 'accent',
            'text-amber-600 border-amber-300': tone === 'warn',
          })}
        >
          {label}
        </Badge>
      ))}
    </div>
  );
};

export default FormLegend;
