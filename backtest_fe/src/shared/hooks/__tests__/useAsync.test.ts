/**
 * useAsync 훅 테스트
 */

import { describe, it, expect, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAsync } from '../useAsync'

describe('useAsync', () => {
  it('should handle successful async operation', async () => {
    const mockFn = vi.fn().mockResolvedValue('success')
    
    const { result } = renderHook(() => useAsync(mockFn, [], { immediate: false }))

    expect(result.current.isLoading).toBe(false)
    expect(result.current.data).toBe(null)

    await act(async () => {
      await result.current.execute()
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.data).toBe('success')
    expect(result.current.error).toBe(null)
    expect(result.current.isSuccess).toBe(true)
  })

  it('should handle async operation error', async () => {
    const mockFn = vi.fn().mockRejectedValue(new Error('Test error'))
    
    const { result } = renderHook(() => useAsync(mockFn, [], { immediate: false }))

    await act(async () => {
      await result.current.execute()
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.data).toBe(null)
    expect(result.current.error).toBe('Test error')
    expect(result.current.isError).toBe(true)
  })

  it('should reset state correctly', async () => {
    const mockFn = vi.fn().mockResolvedValue('success')
    
    const { result } = renderHook(() => useAsync(mockFn, [], { immediate: false }))

    await act(async () => {
      await result.current.execute()
    })

    expect(result.current.data).toBe('success')

    act(() => {
      result.current.reset()
    })

    expect(result.current.data).toBe(null)
    expect(result.current.error).toBe(null)
    expect(result.current.isLoading).toBe(false)
  })

  it('should execute immediately when immediate is true', async () => {
    const mockFn = vi.fn().mockResolvedValue('immediate')
    
    const { result } = renderHook(() => useAsync(mockFn, [], { immediate: true }))

    expect(result.current.isLoading).toBe(true)

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.data).toBe('immediate')
    expect(mockFn).toHaveBeenCalledTimes(1)
  })

  it('should call success callback', async () => {
    const mockFn = vi.fn().mockResolvedValue('success')
    const onSuccess = vi.fn()
    
    const { result } = renderHook(() => 
      useAsync(mockFn, [], { immediate: false, onSuccess })
    )

    await act(async () => {
      await result.current.execute()
    })

    expect(onSuccess).toHaveBeenCalledWith('success')
  })

  it('should call error callback', async () => {
    const mockFn = vi.fn().mockRejectedValue(new Error('Test error'))
    const onError = vi.fn()
    
    const { result } = renderHook(() => 
      useAsync(mockFn, [], { immediate: false, onError })
    )

    await act(async () => {
      await result.current.execute()
    })

    expect(onError).toHaveBeenCalledWith('Test error')
  })
})