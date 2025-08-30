// 现代化设计主题配置
export const modernTheme = {
  colors: {
    // 主色调 - 深蓝渐变
    primary: {
      50: '#f0f9ff',
      100: '#e0f2fe',
      200: '#bae6fd',
      300: '#7dd3fc',
      400: '#38bdf8',
      500: '#0ea5e9',
      600: '#0284c7',
      700: '#0369a1',
      800: '#075985',
      900: '#0c4a6e',
    },
    // 辅助色 - 紫色
    secondary: {
      50: '#faf5ff',
      100: '#f3e8ff',
      200: '#e9d5ff',
      300: '#d8b4fe',
      400: '#c084fc',
      500: '#a855f7',
      600: '#9333ea',
      700: '#7c3aed',
      800: '#6b21a8',
      900: '#581c87',
    },
    // 成功色 - 绿色
    success: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      300: '#86efac',
      400: '#4ade80',
      500: '#22c55e',
      600: '#16a34a',
      700: '#15803d',
      800: '#166534',
      900: '#14532d',
    },
    // 警告色 - 橙色
    warning: {
      50: '#fffbeb',
      100: '#fef3c7',
      200: '#fde68a',
      300: '#fcd34d',
      400: '#fbbf24',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
      800: '#92400e',
      900: '#78350f',
    },
    // 错误色 - 红色
    error: {
      50: '#fef2f2',
      100: '#fee2e2',
      200: '#fecaca',
      300: '#fca5a5',
      400: '#f87171',
      500: '#ef4444',
      600: '#dc2626',
      700: '#b91c1c',
      800: '#991b1b',
      900: '#7f1d1d',
    },
    // 中性色
    gray: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },
    // 背景色
    background: {
      primary: '#ffffff',
      secondary: '#f8fafc',
      tertiary: '#f1f5f9',
      dark: '#0f172a',
      darkSecondary: '#1e293b',
    },
    // 文本色
    text: {
      primary: '#0f172a',
      secondary: '#475569',
      tertiary: '#64748b',
      inverse: '#ffffff',
      muted: '#94a3b8',
    },
    // 边框色
    border: {
      light: '#e2e8f0',
      medium: '#cbd5e1',
      dark: '#475569',
    }
  },
  
  // 阴影
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    glow: '0 0 20px rgb(59 130 246 / 0.5)',
    glowPurple: '0 0 20px rgb(168 85 247 / 0.5)',
  },
  
  // 圆角
  borderRadius: {
    none: '0',
    sm: '0.125rem',
    md: '0.375rem',
    lg: '0.5rem',
    xl: '0.75rem',
    '2xl': '1rem',
    '3xl': '1.5rem',
    full: '9999px',
  },
  
  // 间距
  spacing: {
    xs: '0.5rem',
    sm: '0.75rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
    '4xl': '6rem',
  },
  
  // 字体
  typography: {
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
      mono: ['JetBrains Mono', 'Consolas', 'monospace'],
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem',
      '5xl': '3rem',
    },
    fontWeight: {
      light: '300',
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
      extrabold: '800',
    },
    lineHeight: {
      tight: '1.25',
      normal: '1.5',
      relaxed: '1.75',
    },
  },
  
  // 动画
  animation: {
    duration: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms',
    },
    easing: {
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    },
  },
  
  // 断点
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
  
  // Z-index
  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modal: 1040,
    popover: 1050,
    tooltip: 1060,
  },
};

// Ant Design 主题配置
export const antdTheme = {
  token: {
    colorPrimary: modernTheme.colors.primary[600],
    colorSuccess: modernTheme.colors.success[500],
    colorWarning: modernTheme.colors.warning[500],
    colorError: modernTheme.colors.error[500],
    colorInfo: modernTheme.colors.primary[500],
    
    borderRadius: 8,
    borderRadiusLG: 12,
    borderRadiusSM: 6,
    
    fontFamily: modernTheme.typography.fontFamily.sans.join(', '),
    fontSize: 14,
    fontSizeLG: 16,
    fontSizeSM: 12,
    
    boxShadow: modernTheme.shadows.md,
    boxShadowSecondary: modernTheme.shadows.sm,
    
    colorBgContainer: modernTheme.colors.background.primary,
    colorBgElevated: modernTheme.colors.background.secondary,
    colorBgLayout: modernTheme.colors.background.tertiary,
    
    colorText: modernTheme.colors.text.primary,
    colorTextSecondary: modernTheme.colors.text.secondary,
    colorTextTertiary: modernTheme.colors.text.tertiary,
    
    colorBorder: modernTheme.colors.border.light,
    colorBorderSecondary: modernTheme.colors.border.medium,
  },
  components: {
    Button: {
      borderRadius: 8,
      controlHeight: 40,
      controlHeightLG: 48,
      controlHeightSM: 32,
      fontWeight: 500,
    },
    Card: {
      borderRadius: 12,
      paddingLG: 24,
    },
    Input: {
      borderRadius: 8,
      controlHeight: 40,
      controlHeightLG: 48,
    },
    Select: {
      borderRadius: 8,
      controlHeight: 40,
    },
    Tabs: {
      borderRadius: 8,
      cardPadding: 16,
    },
    Modal: {
      borderRadius: 16,
    },
    Drawer: {
      borderRadius: 16,
    },
  },
};

export type Theme = typeof modernTheme;
