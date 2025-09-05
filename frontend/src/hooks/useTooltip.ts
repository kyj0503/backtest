import { useState, useCallback, useRef, useEffect } from 'react';

interface Position {
  x: number;
  y: number;
}

interface UseTooltipOptions {
  delay?: number;
  offset?: number;
  placement?: 'top' | 'bottom' | 'left' | 'right' | 'auto';
}

interface UseTooltipReturn {
  isVisible: boolean;
  position: Position;
  show: (event?: MouseEvent) => void;
  hide: () => void;
  targetRef: React.RefObject<HTMLElement>;
  tooltipRef: React.RefObject<HTMLDivElement>;
}

/**
 * 툴팁 상태 관리를 위한 커스텀 훅
 * 마우스 호버, 포지셔닝, 지연 표시 기능 제공
 */
export const useTooltip = ({
  delay = 300,
  offset = 8,
  placement = 'auto'
}: UseTooltipOptions = {}): UseTooltipReturn => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState<Position>({ x: 0, y: 0 });
  const targetRef = useRef<HTMLElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const calculatePosition = useCallback((event?: MouseEvent): Position => {
    if (!targetRef.current) {
      return { x: 0, y: 0 };
    }

    const targetRect = targetRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current?.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let x = 0;
    let y = 0;

    if (event) {
      // 마우스 이벤트가 있는 경우 마우스 위치 기준
      x = event.clientX;
      y = event.clientY;
    } else {
      // 타겟 엘리먼트 기준
      x = targetRect.left + targetRect.width / 2;
      y = targetRect.top;
    }

    if (tooltipRect && placement !== 'auto') {
      switch (placement) {
        case 'top':
          x -= tooltipRect.width / 2;
          y -= tooltipRect.height + offset;
          break;
        case 'bottom':
          x -= tooltipRect.width / 2;
          y += targetRect.height + offset;
          break;
        case 'left':
          x -= tooltipRect.width + offset;
          y -= tooltipRect.height / 2;
          break;
        case 'right':
          x += targetRect.width + offset;
          y -= tooltipRect.height / 2;
          break;
      }
    } else {
      // auto 배치: 화면 경계를 고려한 자동 배치
      if (tooltipRect) {
        // 오른쪽 경계 체크
        if (x + tooltipRect.width > viewportWidth) {
          x = viewportWidth - tooltipRect.width - offset;
        }
        // 왼쪽 경계 체크
        if (x < offset) {
          x = offset;
        }
        // 아래쪽 경계 체크
        if (y + tooltipRect.height > viewportHeight) {
          y = y - tooltipRect.height - offset;
        }
        // 위쪽 경계 체크
        if (y < offset) {
          y = offset;
        }
      }
    }

    return { x, y };
  }, [placement, offset]);

  const show = useCallback((event?: MouseEvent) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      const newPosition = calculatePosition(event);
      setPosition(newPosition);
      setIsVisible(true);
    }, delay);
  }, [calculatePosition, delay]);

  const hide = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  }, []);

  // 스크롤이나 리사이즈 시 툴팁 숨기기
  useEffect(() => {
    const handleScroll = () => hide();
    const handleResize = () => hide();

    if (isVisible) {
      window.addEventListener('scroll', handleScroll, true);
      window.addEventListener('resize', handleResize);
    }

    return () => {
      window.removeEventListener('scroll', handleScroll, true);
      window.removeEventListener('resize', handleResize);
    };
  }, [isVisible, hide]);

  // 컴포넌트 언마운트 시 타이머 정리
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    isVisible,
    position,
    show,
    hide,
    targetRef,
    tooltipRef
  };
};
