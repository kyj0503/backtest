import { describe, it, expect, beforeEach, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { render, screen } from '@/test/utils'
import ThemeSelector from '../ThemeSelector'
import type { ThemeDefinition } from '@/shared/types/theme'

type MinimalTheme = Pick<ThemeDefinition, 'name' | 'cssVars'>

const buildTheme = (name: string, color: string): MinimalTheme => ({
  name,
  cssVars: {
    theme: {
      'font-sans': 'Inter, sans-serif',
      'font-mono': 'JetBrains Mono, monospace',
      'font-serif': 'Newsreader, serif',
      radius: '0.5rem',
    },
    light: {
      background: '#ffffff',
      foreground: '#000000',
      card: '#ffffff',
      'card-foreground': '#000000',
      popover: '#ffffff',
      'popover-foreground': '#000000',
      primary: color,
      'primary-foreground': '#ffffff',
      secondary: '#cccccc',
      'secondary-foreground': '#000000',
      muted: '#eeeeee',
      'muted-foreground': '#555555',
      accent: '#dddddd',
      'accent-foreground': '#000000',
      destructive: '#ff0000',
      'destructive-foreground': '#ffffff',
      border: '#e5e7eb',
      input: '#f3f4f6',
      ring: '#2563eb',
      'chart-1': '#ff0000',
      'chart-2': '#00ff00',
      'chart-3': '#0000ff',
      'chart-4': '#ff00ff',
      'chart-5': '#00ffff',
      sidebar: '#ffffff',
      'sidebar-foreground': '#000000',
      'sidebar-primary': '#2563eb',
      'sidebar-primary-foreground': '#ffffff',
      'sidebar-accent': '#e2e8f0',
      'sidebar-accent-foreground': '#0f172a',
      'sidebar-border': '#cbd5f5',
      'sidebar-ring': '#1d4ed8',
    },
    dark: {
      background: '#111827',
      foreground: '#f9fafb',
      card: '#1f2937',
      'card-foreground': '#f9fafb',
      popover: '#1f2937',
      'popover-foreground': '#f9fafb',
      primary: color,
      'primary-foreground': '#0f172a',
      secondary: '#374151',
      'secondary-foreground': '#f9fafb',
      muted: '#4b5563',
      'muted-foreground': '#d1d5db',
      accent: '#2563eb',
      'accent-foreground': '#ffffff',
      destructive: '#f87171',
      'destructive-foreground': '#111827',
      border: '#374151',
      input: '#1f2937',
      ring: '#60a5fa',
      'chart-1': '#0ea5e9',
      'chart-2': '#22d3ee',
      'chart-3': '#38bdf8',
      'chart-4': '#818cf8',
      'chart-5': '#a855f7',
      sidebar: '#111827',
      'sidebar-foreground': '#f9fafb',
      'sidebar-primary': '#60a5fa',
      'sidebar-primary-foreground': '#0f172a',
      'sidebar-accent': '#1e293b',
      'sidebar-accent-foreground': '#e2e8f0',
      'sidebar-border': '#1f2937',
      'sidebar-ring': '#60a5fa',
    },
  },
})

const mockChangeTheme = vi.fn()
const mockToggleDarkMode = vi.fn()

const themes = {
  claymorphism: buildTheme('claymorphism', '#2563eb'),
  'amber-minimal': buildTheme('amber-minimal', '#f59e0b'),
} as const

const availableThemes = [
  { id: 'claymorphism', name: 'claymorphism', displayName: 'Claymorphism' },
  { id: 'amber-minimal', name: 'amber-minimal', displayName: 'Amber Minimal' },
]

vi.mock('@/shared/hooks/useTheme', () => ({
  useTheme: () => ({
    currentTheme: 'claymorphism' as const,
    isDarkMode: false,
    changeTheme: mockChangeTheme,
    toggleDarkMode: mockToggleDarkMode,
    getAvailableThemes: () => availableThemes,
    getCurrentThemeDefinition: () => themes['claymorphism'],
    themes,
  }),
}))

describe('ThemeSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('displays headings and helper text', () => {
    render(<ThemeSelector />)

    expect(screen.getByRole('heading', { name: /테마 설정/ })).toBeInTheDocument()
    expect(screen.getByText(/원하는 디자인 테마를 선택하세요/)).toBeInTheDocument()
  })

  it('lists available themes with active indicator', () => {
    render(<ThemeSelector />)

    const activeCard = screen.getByRole('button', { name: /Claymorphism/ })
    const inactiveCard = screen.getByRole('button', { name: /Amber Minimal/ })

    expect(activeCard).toHaveAttribute('aria-pressed', 'true')
    expect(inactiveCard).toHaveAttribute('aria-pressed', 'false')
  })

  it('toggles dark mode when the toggle button is clicked', async () => {
    const user = userEvent.setup()
    render(<ThemeSelector />)

    await user.click(screen.getByRole('button', { name: /라이트/ }))

    expect(mockToggleDarkMode).toHaveBeenCalledTimes(1)
  })

  it('invokes changeTheme when a theme is selected', async () => {
    const user = userEvent.setup()
    render(<ThemeSelector />)

    const amberHeading = screen.getByText('Amber Minimal')
    const themeCard = amberHeading.closest('[role="button"]')
    expect(themeCard).not.toBeNull()

    if (themeCard) {
      await user.click(themeCard)
    }

    expect(mockChangeTheme).toHaveBeenCalledWith('amber-minimal')
  })

  it('displays current theme metadata', () => {
    render(<ThemeSelector />)

    expect(screen.getByText(/선택된 테마:/)).toHaveTextContent('Claymorphism')
    expect(screen.getByText(/다크 모드:/)).toHaveTextContent('비활성')
  })
})
