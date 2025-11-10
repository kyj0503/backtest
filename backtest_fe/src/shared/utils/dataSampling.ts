/**
 * 데이터 샘플링 유틸리티
 * 
 * **역할**:
 * - 대량의 차트 데이터 포인트를 성능 최적화를 위해 샘플링
 * - 시각적 품질을 유지하면서 렌더링 부하 감소
 */

/**
 * 균등 샘플링 - 일정 간격으로 데이터 포인트 추출
 * 
 * @param data 원본 데이터 배열
 * @param maxPoints 최대 포인트 수 (기본: 500)
 * @returns 샘플링된 데이터 배열
 */
export function sampleData<T>(data: T[], maxPoints: number = 500): T[] {
  if (!data || data.length === 0) {
    return [];
  }

  // 데이터가 이미 충분히 작으면 그대로 반환
  if (data.length <= maxPoints) {
    return data;
  }

  const step = Math.ceil(data.length / maxPoints);
  const sampled: T[] = [];

  // 첫 번째 포인트는 항상 포함
  sampled.push(data[0]);

  // 균등 간격으로 샘플링
  for (let i = step; i < data.length - 1; i += step) {
    sampled.push(data[i]);
  }

  // 마지막 포인트는 항상 포함 (종료 값 보존)
  if (data.length > 1) {
    sampled.push(data[data.length - 1]);
  }

  return sampled;
}

/**
 * 적응형 샘플링 - 변화가 큰 구간은 더 많은 포인트 유지
 * 
 * @param data 원본 데이터 배열
 * @param maxPoints 최대 포인트 수 (기본: 500)
 * @param valueKey 비교할 값의 키 (예: 'value', 'close')
 * @returns 샘플링된 데이터 배열
 */
export function adaptiveSampleData<T>(
  data: T[],
  maxPoints: number = 500,
  valueKey: keyof T = 'value' as keyof T
): T[] {
  if (!data || data.length === 0) {
    return [];
  }

  if (data.length <= maxPoints) {
    return data;
  }

  const sampled: T[] = [data[0]]; // 첫 포인트
  const threshold = calculateThreshold(data, valueKey);

  let lastAddedIndex = 0;

  for (let i = 1; i < data.length - 1; i++) {
    const currentValue = data[i][valueKey] as number;
    const lastValue = data[lastAddedIndex][valueKey] as number;

    // 변화가 임계값보다 크면 포인트 추가
    if (Math.abs(currentValue - lastValue) > threshold) {
      sampled.push(data[i]);
      lastAddedIndex = i;
    }

    // 최대 포인트 수에 도달하면 중단
    if (sampled.length >= maxPoints - 1) {
      break;
    }
  }

  // 마지막 포인트 추가
  sampled.push(data[data.length - 1]);

  // 여전히 포인트가 부족하면 균등 샘플링으로 보완
  if (sampled.length < maxPoints * 0.5) {
    return sampleData(data, maxPoints);
  }

  return sampled;
}

/**
 * 변화 임계값 계산 (표준편차 기반)
 */
function calculateThreshold<T>(data: T[], valueKey: keyof T): number {
  const values = data.map((d) => d[valueKey] as number).filter((v) => !isNaN(v));

  if (values.length === 0) return 0;

  const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
  const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
  const stdDev = Math.sqrt(variance);

  return stdDev * 0.5; // 0.5 표준편차를 임계값으로 사용
}

/**
 * 리밸런싱 마커 필터링 - 화면에 보이는 마커만 유지
 * 
 * @param markers 리밸런싱 마커 배열
 * @param maxMarkers 최대 마커 수 (기본: 20)
 * @returns 필터링된 마커 배열
 */
export function filterRebalanceMarkers<T extends { date?: string; timestamp?: string }>(
  markers: T[],
  maxMarkers: number = 20
): T[] {
  if (!markers || markers.length <= maxMarkers) {
    return markers;
  }

  // 최신 마커를 우선적으로 유지
  return markers.slice(-maxMarkers);
}
