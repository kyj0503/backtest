/**
 * ThemeSelector 컴포넌트 테스트
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@/test/utils'
import userEvent from '@testing-library/user-event'
import ThemeSelector from '../ThemeSelector'

// useTheme 훅 모킹
const mockChangeTheme = vi.fn()
const mockToggleDarkMode = vi.fn()

vi.mock('@/shared/hooks/useTheme', () => ({
  useTheme: () => ({
    currentTheme: 'default' as const,
    isDarkMode: false,
    changeTheme: mockChangeTheme,
    toggleDarkMode: mockToggleDarkMode,
    getAvailableThemes: () => [
      { id: 'default', displayName: 'Default Theme', name: 'default' },
      { id: 'blue', displayName: 'Blue Theme', name: 'blue' },
    ],
    themes: {
      default: {
        name: 'default',
        cssVars: {
          light: {
            background: '#ffffff',
            foreground: '#000000',
            primary: '#0000ff',
            secondary: '#00ff00',
            accent: '#ff0000',
            card: '#f0f0f0',
            muted: '#e0e0e0',
            border: '#cccccc',
            input: '#dddddd',
            ring: '#aaaaaa',
            'card-foreground': '#000000',
            'primary-foreground': '#ffffff',
            'secondary-foreground': '#000000',
            'muted-foreground': '#666666',
            'accent-foreground': '#ffffff',
            'destructive': '#ff0000',
            'destructive-foreground': '#ffffff',
            'popover': '#ffffff',
            'popover-foreground': '#000000',
          },
          dark: {
            background: '#000000',
            foreground: '#ffffff',
            primary: '#0000ff',
            secondary: '#00ff00',
            accent: '#ff0000',
            card: '#1a1a1a',
            muted: '#2a2a2a',
            border: '#333333',
            input: '#222222',
            ring: '#555555',
            'card-foreground': '#ffffff',
            'primary-foreground': '#ffffff',
            'secondary-foreground': '#000000',
            'muted-foreground': '#999999',
            'accent-foreground': '#ffffff',
            'destructive': '#ff0000',
            'destructive-foreground': '#ffffff',
            'popover': '#1a1a1a',
            'popover-foreground': '#ffffff',
          },
          theme: {
            'font-sans': 'Inter, sans-serif',
            radius: '0.5rem',
          }
        }
      },
      blue: {
        name: 'blue',
        cssVars: {
          light: {
            background: '#ffffff',
            foreground: '#000000',
            primary: '#0066cc',
            secondary: '#00aaff',
            accent: '#3399ff',
            card: '#f0f8ff',
            muted: '#e0f0ff',
            border: '#cce5ff',
            input: '#ddeeff',
            ring: '#aaccee',
            'card-foreground': '#000000',
            'primary-foreground': '#ffffff',
            'secondary-foreground': '#000000',
            'muted-foreground': '#666666',
            'accent-foreground': '#ffffff',
            'destructive': '#ff0000',
            'destructive-foreground': '#ffffff',
            'popover': '#ffffff',
            'popover-foreground': '#000000',
          },
          dark: {
            background: '#001122',
            foreground: '#ffffff',
            primary: '#0066cc',
            secondary: '#00aaff',
            accent: '#3399ff',
            card: '#002244',
            muted: '#003355',
            border: '#004466',
            input: '#002233',
            ring: '#005577',
            'card-foreground': '#ffffff',
            'primary-foreground': '#ffffff',
            'secondary-foreground': '#000000',
            'muted-foreground': '#999999',
            'accent-foreground': '#ffffff',
            'destructive': '#ff0000',
            'destructive-foreground': '#ffffff',
            'popover': '#002244',
            'popover-foreground': '#ffffff',
          },
          theme: {
            'font-sans': 'Inter, sans-serif',
            radius: '0.5rem',
          }
        }
      }
    }
  })
}))

describe('ThemeSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('컴포넌트가 올바르게 렌더링된다', () => {
    render(<ThemeSelector />)
    
    expect(screen.getByText('테마 설정')).toBeInTheDocument()
    expect(screen.getByText(/원하는 디자인 테마를 선택하세요/i)).toBeInTheDocument()
  })

  it('사용 가능한 모든 테마를 표시한다', () => {
    render(<ThemeSelector />)
    
    // theme.name을 기반으로 렌더링되므로 'Default'와 'Blue'를 찾음
    expect(screen.getByText(/^Default$/i)).toBeInTheDocument()
    expect(screen.getByText(/^Blue$/i)).toBeInTheDocument()
  })

  it('현재 활성화된 테마에 배지를 표시한다', () => {
    render(<ThemeSelector />)
    
    const activeBadges = screen.getAllByText('활성')
    expect(activeBadges).toHaveLength(1)
  })

  it('다크 모드 토글 버튼이 정상 작동한다', async () => {
    const user = userEvent.setup()
    render(<ThemeSelector />)
    
    const darkModeButton = screen.getByRole('button', { name: /라이트/i })
    await user.click(darkModeButton)
    
    expect(mockToggleDarkMode).toHaveBeenCalledTimes(1)
  })

  it('테마를 클릭하면 changeTheme이 호출된다', async () => {
    const user = userEvent.setup()
    render(<ThemeSelector />)
    
    // 'Blue' 텍스트를 포함한 카드를 찾아서 클릭
    const blueThemeCard = screen.getByText(/^Blue$/i).closest('.rounded-lg')
    expect(blueThemeCard).toBeInTheDocument()
    
    if (blueThemeCard) {
      await user.click(blueThemeCard)
      expect(mockChangeTheme).toHaveBeenCalledWith('blue')
    }
  })

  it('현재 테마 정보를 표시한다', () => {
    render(<ThemeSelector />)
    
    expect(screen.getByText(/현재 테마 정보/i)).toBeInTheDocument()
    // displayName이 표시됨
    expect(screen.getByText(/Default Theme/i)).toBeInTheDocument()
    expect(screen.getByText(/다크 모드:/i)).toBeInTheDocument()
    expect(screen.getByText(/비활성/i)).toBeInTheDocument()
  })

  it('각 테마의 색상 프리뷰를 표시한다', () => {
    render(<ThemeSelector />)
    
    // 각 테마마다 6개의 색상 프리뷰가 있어야 함
    const colorPreviews = screen.getAllByTitle(/Primary|Secondary|Accent|Card|Background|Muted/i)
    expect(colorPreviews.length).toBeGreaterThan(0)
  })
})
