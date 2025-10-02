/**
 * 테스트 헬퍼 함수들
 */

import { waitFor, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect } from 'vitest'

/**
 * 로딩 완료 대기
 */
export const waitForLoadingToFinish = async () => {
  await waitFor(() => {
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
    expect(screen.queryByText(/로딩/i)).not.toBeInTheDocument()
  }, { timeout: 3000 })
}

/**
 * 백테스트 폼 입력
 */
export const fillBacktestForm = async (data: {
  ticker?: string
  strategy?: string
  startDate?: string
  endDate?: string
  capital?: number
}) => {
  const user = userEvent.setup()
  
  if (data.ticker) {
    const tickerInput = screen.getByLabelText(/티커|ticker/i)
    await user.clear(tickerInput)
    await user.type(tickerInput, data.ticker)
  }
  
  if (data.strategy) {
    const strategySelect = screen.getByLabelText(/전략|strategy/i)
    await user.selectOptions(strategySelect, data.strategy)
  }
  
  if (data.startDate) {
    const startDateInput = screen.getByLabelText(/시작일|start date/i)
    await user.clear(startDateInput)
    await user.type(startDateInput, data.startDate)
  }
  
  if (data.endDate) {
    const endDateInput = screen.getByLabelText(/종료일|end date/i)
    await user.clear(endDateInput)
    await user.type(endDateInput, data.endDate)
  }
  
  if (data.capital) {
    const capitalInput = screen.getByLabelText(/초기 자본금|initial capital/i)
    await user.clear(capitalInput)
    await user.type(capitalInput, data.capital.toString())
  }
}

/**
 * 백테스트 실행 버튼 클릭
 */
export const clickRunBacktest = async () => {
  const user = userEvent.setup()
  const runButton = screen.getByRole('button', { name: /실행|run|시작/i })
  await user.click(runButton)
}

/**
 * 로그인 폼 입력 및 제출
 */
export const loginUser = async (email: string, password: string) => {
  const user = userEvent.setup()
  
  const emailInput = screen.getByLabelText(/이메일|email/i)
  await user.type(emailInput, email)
  
  const passwordInput = screen.getByLabelText(/비밀번호|password/i)
  await user.type(passwordInput, password)
  
  const submitButton = screen.getByRole('button', { name: /로그인|login|제출/i })
  await user.click(submitButton)
}

/**
 * 에러 메시지 확인
 */
export const expectErrorMessage = (message: string | RegExp) => {
  const errorElement = screen.getByRole('alert') || screen.getByText(message)
  expect(errorElement).toBeInTheDocument()
}

/**
 * 성공 메시지 확인
 */
export const expectSuccessMessage = (message: string | RegExp) => {
  const successElement = screen.getByText(message)
  expect(successElement).toBeInTheDocument()
}

/**
 * API 에러 모킹
 */
export const mockApiError = (statusCode: number = 500, message: string = 'Internal Server Error') => ({
  response: {
    status: statusCode,
    data: { message }
  }
})

/**
 * 비동기 테스트를 위한 지연
 */
export const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))
