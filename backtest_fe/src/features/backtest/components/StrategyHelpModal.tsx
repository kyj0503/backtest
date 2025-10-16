import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog';
import { Badge } from '@/shared/ui/badge';
import { ScrollArea } from '@/shared/ui/scroll-area';
import { Separator } from '@/shared/ui/separator';
import {
  CheckCircle2,
  XCircle,
  Target,
  TrendingUp,
  Settings,
  Lightbulb,
  Link2
} from 'lucide-react';
import { STRATEGY_DETAILS, StrategyDetail } from '../constants/strategyDetails';

interface StrategyHelpModalProps {
  strategyId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const StrategyHelpModal: React.FC<StrategyHelpModalProps> = ({
  strategyId,
  open,
  onOpenChange,
}) => {
  const strategy = STRATEGY_DETAILS[strategyId];

  if (!strategy) {
    return null;
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case '초급':
        return 'bg-green-500/10 text-green-600 border-green-500/20';
      case '중급':
        return 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20';
      case '고급':
        return 'bg-red-500/10 text-red-600 border-red-500/20';
      default:
        return 'bg-gray-500/10 text-gray-600 border-gray-500/20';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] p-0">
        <ScrollArea className="max-h-[90vh] p-6">
          <DialogHeader className="space-y-3 mb-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <DialogTitle className="text-2xl font-bold mb-2">
                  {strategy.name}
                </DialogTitle>
                <DialogDescription className="text-base">
                  {strategy.description}
                </DialogDescription>
              </div>
              <div className="flex flex-col gap-2">
                <Badge variant="outline" className="whitespace-nowrap">
                  {strategy.category}
                </Badge>
                <Badge
                  variant="outline"
                  className={getDifficultyColor(strategy.difficulty)}
                >
                  {strategy.difficulty}
                </Badge>
              </div>
            </div>
          </DialogHeader>

          <div className="space-y-6">
            {/* 개요 */}
            <section>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-primary" />
                전략 개요
              </h3>
              <div className="bg-muted/30 rounded-lg p-4 text-sm leading-relaxed whitespace-pre-line">
                {strategy.overview}
              </div>
            </section>

            <Separator />

            {/* 작동 원리 */}
            <section>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Settings className="w-5 h-5 text-primary" />
                작동 원리
              </h3>
              <ol className="space-y-2">
                {strategy.howItWorks.map((step, index) => (
                  <li key={index} className="text-sm flex items-start gap-2">
                    <span className="font-medium text-primary min-w-[1.5rem]">
                      {step.match(/^\d+\./)?.[0] || `${index + 1}.`}
                    </span>
                    <span className="flex-1">
                      {step.replace(/^\d+\.\s*/, '')}
                    </span>
                  </li>
                ))}
              </ol>
            </section>

            <Separator />

            {/* 장단점 */}
            <section>
              <div className="grid md:grid-cols-2 gap-6">
                {/* 장점 */}
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2 text-green-600">
                    <CheckCircle2 className="w-5 h-5" />
                    장점
                  </h3>
                  <ul className="space-y-2">
                    {strategy.advantages.map((advantage, index) => (
                      <li key={index} className="text-sm flex items-start gap-2">
                        <span className="text-green-600 mt-0.5">✓</span>
                        <span>{advantage.replace(/^✓\s*/, '')}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 단점 */}
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2 text-red-600">
                    <XCircle className="w-5 h-5" />
                    단점
                  </h3>
                  <ul className="space-y-2">
                    {strategy.disadvantages.map((disadvantage, index) => (
                      <li key={index} className="text-sm flex items-start gap-2">
                        <span className="text-red-600 mt-0.5">✗</span>
                        <span>{disadvantage.replace(/^✗\s*/, '')}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>

            <Separator />

            {/* 추천 대상 */}
            <section>
              <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Target className="w-5 h-5 text-primary" />
                이런 분께 추천합니다
              </h3>
              <ul className="space-y-2">
                {strategy.bestFor.map((target, index) => (
                  <li key={index} className="text-sm flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>{target}</span>
                  </li>
                ))}
              </ul>
            </section>

            {/* 파라미터 */}
            {strategy.parameters && strategy.parameters.length > 0 && (
              <>
                <Separator />
                <section>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <Settings className="w-5 h-5 text-primary" />
                    전략 파라미터
                  </h3>
                  <div className="space-y-3">
                    {strategy.parameters.map((param, index) => (
                      <div
                        key={index}
                        className="bg-muted/30 rounded-lg p-4 space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium text-sm">{param.name}</h4>
                          <Badge variant="outline" className="text-xs">
                            기본값: {param.defaultValue}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {param.description}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          권장 범위: {param.range}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>
              </>
            )}

            {/* 예시 */}
            {strategy.example && (
              <>
                <Separator />
                <section>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-primary" />
                    실전 예시
                  </h3>
                  <div className="bg-muted/30 rounded-lg p-4 text-sm leading-relaxed whitespace-pre-line font-mono">
                    {strategy.example}
                  </div>
                </section>
              </>
            )}

            {/* 연관 전략 */}
            {strategy.relatedStrategies && strategy.relatedStrategies.length > 0 && (
              <>
                <Separator />
                <section>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <Link2 className="w-5 h-5 text-primary" />
                    연관 전략
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {strategy.relatedStrategies.map((relatedId) => {
                      const related = STRATEGY_DETAILS[relatedId];
                      return related ? (
                        <Badge
                          key={relatedId}
                          variant="secondary"
                          className="cursor-default"
                        >
                          {related.name}
                        </Badge>
                      ) : null;
                    })}
                  </div>
                </section>
              </>
            )}

            {/* 하단 안내 */}
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mt-6">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                💡 <strong>팁:</strong> 모든 전략은 과거 데이터를 기반으로 하므로,
                미래 수익을 보장하지 않습니다. 여러 전략을 테스트하고
                자신의 투자 성향에 맞는 전략을 선택하세요.
              </p>
            </div>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};

export default StrategyHelpModal;
