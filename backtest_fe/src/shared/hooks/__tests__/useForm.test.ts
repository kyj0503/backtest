/**
 * useForm 훅 테스트
 */

import { describe, it, expect, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useForm } from '../useForm'

interface TestFormData {
  name: string
  email: string
  age: number
}

describe('useForm', () => {
  const initialData: TestFormData = {
    name: '',
    email: '',
    age: 0,
  }

  const validationRules = {
    name: (value: string) => value.length < 2 ? 'Name must be at least 2 characters' : null,
    email: (value: string) => !value.includes('@') ? 'Invalid email' : null,
  }

  it('should initialize with initial data', () => {
    const { result } = renderHook(() => useForm(initialData))

    expect(result.current.data).toEqual(initialData)
    expect(result.current.isValid).toBe(true)
    expect(result.current.isSubmitting).toBe(false)
    expect(result.current.errors).toEqual({})
  })

  it('should update field values', () => {
    const { result } = renderHook(() => useForm(initialData))

    act(() => {
      result.current.setFieldValue('name', 'John')
    })

    expect(result.current.data.name).toBe('John')
  })

  it('should validate fields on change', () => {
    const { result } = renderHook(() => useForm(initialData, validationRules))

    act(() => {
      result.current.setFieldValue('name', 'J')
    })

    expect(result.current.errors.name).toBe('Name must be at least 2 characters')
    expect(result.current.isValid).toBe(false)

    act(() => {
      result.current.setFieldValue('name', 'John')
    })

    expect(result.current.errors.name).toBeUndefined()
  })

  it('should validate entire form', () => {
    const { result } = renderHook(() => useForm(initialData, validationRules))

    act(() => {
      result.current.setFieldValue('name', 'J')
      result.current.setFieldValue('email', 'invalid')
    })

    act(() => {
      const isValid = result.current.validateForm()
      expect(isValid).toBe(false)
    })

    expect(result.current.errors.name).toBe('Name must be at least 2 characters')
    expect(result.current.errors.email).toBe('Invalid email')
  })

  it('should reset form', () => {
    const { result } = renderHook(() => useForm(initialData))

    act(() => {
      result.current.setFieldValue('name', 'John')
      result.current.setFieldError('email', 'Some error')
    })

    expect(result.current.data.name).toBe('John')
    expect(result.current.errors.email).toBe('Some error')

    act(() => {
      result.current.resetForm()
    })

    expect(result.current.data).toEqual(initialData)
    expect(result.current.errors).toEqual({})
  })

  it('should handle form submission', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const { result } = renderHook(() => useForm(initialData, validationRules))

    act(() => {
      result.current.setFieldValue('name', 'John')
      result.current.setFieldValue('email', 'john@example.com')
    })

    const submitHandler = result.current.handleSubmit(onSubmit)

    await act(async () => {
      await submitHandler()
    })

    expect(onSubmit).toHaveBeenCalledWith({
      name: 'John',
      email: 'john@example.com',
      age: 0,
    })
  })

  it('should not submit if form is invalid', async () => {
    const onSubmit = vi.fn()
    const { result } = renderHook(() => useForm(initialData, validationRules))

    act(() => {
      result.current.setFieldValue('name', 'J') // Invalid
    })

    const submitHandler = result.current.handleSubmit(onSubmit)

    await act(async () => {
      await submitHandler()
    })

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('should create input handlers', () => {
    const { result } = renderHook(() => useForm(initialData))

    const nameHandler = result.current.createInputHandler('name')
    const mockEvent = {
      target: { value: 'John' }
    } as React.ChangeEvent<HTMLInputElement>

    act(() => {
      nameHandler(mockEvent)
    })

    expect(result.current.data.name).toBe('John')
  })

  it('should create checkbox handlers', () => {
    interface CheckboxForm {
      isChecked: boolean
    }

    const { result } = renderHook(() => useForm<CheckboxForm>({ isChecked: false }))

    const checkboxHandler = result.current.createCheckboxHandler('isChecked')
    const mockEvent = {
      target: { checked: true }
    } as React.ChangeEvent<HTMLInputElement>

    act(() => {
      checkboxHandler(mockEvent)
    })

    expect(result.current.data.isChecked).toBe(true)
  })

  it('should track dirty state', () => {
    const { result } = renderHook(() => useForm(initialData))

    expect(result.current.isDirty).toBe(false)

    act(() => {
      result.current.setFieldValue('name', 'John')
    })

    expect(result.current.isDirty).toBe(true)
  })
})