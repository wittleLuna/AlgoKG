import { useState, useEffect } from 'react';

export type Theme = 'light' | 'dark';

interface ThemeConfig {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

export const useTheme = (): ThemeConfig => {
  const [theme, setThemeState] = useState<Theme>(() => {
    // 从localStorage读取主题设置
    const saved = localStorage.getItem('app_theme');
    if (saved && (saved === 'light' || saved === 'dark')) {
      return saved as Theme;
    }
    
    // 检查系统主题偏好
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    
    return 'light';
  });

  // 应用主题到DOM
  useEffect(() => {
    const root = document.documentElement;
    
    if (theme === 'dark') {
      root.classList.add('theme-dark');
      root.classList.remove('theme-light');
    } else {
      root.classList.add('theme-light');
      root.classList.remove('theme-dark');
    }
    
    // 保存到localStorage
    localStorage.setItem('app_theme', theme);
  }, [theme]);

  // 监听系统主题变化
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      // 只有在用户没有手动设置主题时才跟随系统
      const savedTheme = localStorage.getItem('app_theme');
      if (!savedTheme) {
        setThemeState(e.matches ? 'dark' : 'light');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  const toggleTheme = () => {
    setThemeState(prev => prev === 'light' ? 'dark' : 'light');
  };

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  return {
    theme,
    toggleTheme,
    setTheme
  };
};

// 主题相关的CSS变量和样式
export const getThemeStyles = (theme: Theme) => {
  const lightTheme = {
    '--bg-primary': '#ffffff',
    '--bg-secondary': '#f5f5f5',
    '--bg-tertiary': '#fafafa',
    '--text-primary': '#262626',
    '--text-secondary': '#595959',
    '--text-tertiary': '#8c8c8c',
    '--border-color': '#d9d9d9',
    '--border-color-light': '#f0f0f0',
    '--shadow-light': '0 2px 8px rgba(0, 0, 0, 0.06)',
    '--shadow-medium': '0 4px 12px rgba(0, 0, 0, 0.1)',
    '--shadow-heavy': '0 8px 24px rgba(0, 0, 0, 0.15)',
    '--primary-color': '#1890ff',
    '--primary-hover': '#40a9ff',
    '--success-color': '#52c41a',
    '--warning-color': '#faad14',
    '--error-color': '#ff4d4f',
  };

  const darkTheme = {
    '--bg-primary': '#1f1f1f',
    '--bg-secondary': '#2f2f2f',
    '--bg-tertiary': '#262626',
    '--text-primary': '#ffffff',
    '--text-secondary': '#d9d9d9',
    '--text-tertiary': '#8c8c8c',
    '--border-color': '#434343',
    '--border-color-light': '#303030',
    '--shadow-light': '0 2px 8px rgba(0, 0, 0, 0.2)',
    '--shadow-medium': '0 4px 12px rgba(0, 0, 0, 0.3)',
    '--shadow-heavy': '0 8px 24px rgba(0, 0, 0, 0.4)',
    '--primary-color': '#1890ff',
    '--primary-hover': '#40a9ff',
    '--success-color': '#52c41a',
    '--warning-color': '#faad14',
    '--error-color': '#ff4d4f',
  };

  return theme === 'dark' ? darkTheme : lightTheme;
};

// 应用主题样式到根元素
export const applyThemeStyles = (theme: Theme) => {
  const styles = getThemeStyles(theme);
  const root = document.documentElement;
  
  Object.entries(styles).forEach(([property, value]) => {
    root.style.setProperty(property, value);
  });
};

export default useTheme;
