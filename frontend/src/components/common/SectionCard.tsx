import { ReactNode } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface SectionCardProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  headerClassName?: string;
  contentClassName?: string;
}

export const SectionCard = ({
  title,
  description,
  actions,
  children,
  className,
  headerClassName,
  contentClassName,
}: SectionCardProps) => {
  return (
    <Card className={cn('border border-border/70 bg-card/70 shadow-sm', className)}>
      <CardHeader
        className={cn(
          'flex flex-col gap-2 border-b border-border/60 text-left sm:flex-row sm:items-start sm:justify-between',
          headerClassName,
        )}
      >
        <div className="space-y-1">
          <CardTitle className="text-lg font-semibold text-foreground">{title}</CardTitle>
          {description ? (
            <CardDescription className="text-sm text-muted-foreground">{description}</CardDescription>
          ) : null}
        </div>
        {actions ? <div className="flex shrink-0 items-center gap-3">{actions}</div> : null}
      </CardHeader>
      <CardContent className={cn('px-5 py-5', contentClassName)}>{children}</CardContent>
    </Card>
  );
};

export default SectionCard;
