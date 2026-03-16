import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import {
  LANGUAGE_STORAGE_KEY,
  THEME_STORAGE_KEY,
  resolveLanguagePreference,
  resolveThemePreference,
  type LanguagePreference,
  type ResolvedLanguage,
  type ResolvedTheme,
  type ThemePreference,
} from '@/lib/preferences'
import { translate } from '@/lib/messages'

interface ConsolePreferencesContextValue {
  themePreference: ThemePreference
  resolvedTheme: ResolvedTheme
  setThemePreference: (value: ThemePreference) => void
  languagePreference: LanguagePreference
  resolvedLanguage: ResolvedLanguage
  setLanguagePreference: (value: LanguagePreference) => void
  t: (key: string) => string
}

const ConsolePreferencesContext = createContext<ConsolePreferencesContextValue | null>(null)

export function ConsolePreferencesProvider({ children }: { children: ReactNode }) {
  const [themePreference, setThemePreferenceState] = useState<ThemePreference>(() =>
    readStoredPreference(THEME_STORAGE_KEY, ['system', 'light', 'dark'], 'system'),
  )
  const [languagePreference, setLanguagePreferenceState] = useState<LanguagePreference>(() =>
    readStoredPreference(LANGUAGE_STORAGE_KEY, ['system', 'en', 'zh-CN', 'zh-TW', 'ja'], 'system'),
  )
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>(() =>
    resolveThemePreference(themePreference, getSystemPrefersDark()),
  )
  const [resolvedLanguage, setResolvedLanguage] = useState<ResolvedLanguage>(() =>
    resolveLanguagePreference(languagePreference, getSystemLanguages()),
  )

  useEffect(() => {
    const mediaQuery =
      typeof window !== 'undefined' && typeof window.matchMedia === 'function'
        ? window.matchMedia('(prefers-color-scheme: dark)')
        : null

    const updateTheme = () => {
      setResolvedTheme(resolveThemePreference(themePreference, getSystemPrefersDark()))
    }

    updateTheme()
    mediaQuery?.addEventListener('change', updateTheme)
    return () => mediaQuery?.removeEventListener('change', updateTheme)
  }, [themePreference])

  useEffect(() => {
    const updateLanguage = () => {
      setResolvedLanguage(resolveLanguagePreference(languagePreference, getSystemLanguages()))
    }

    updateLanguage()
    window.addEventListener('languagechange', updateLanguage)
    return () => window.removeEventListener('languagechange', updateLanguage)
  }, [languagePreference])

  useEffect(() => {
    const root = document.documentElement
    root.classList.toggle('dark', resolvedTheme === 'dark')
    root.dataset.theme = resolvedTheme
    root.style.colorScheme = resolvedTheme
  }, [resolvedTheme])

  const value = useMemo<ConsolePreferencesContextValue>(
    () => ({
      themePreference,
      resolvedTheme,
      setThemePreference: (nextTheme) => {
        setThemePreferenceState(nextTheme)
        writeStoredPreference(THEME_STORAGE_KEY, nextTheme)
      },
      languagePreference,
      resolvedLanguage,
      setLanguagePreference: (nextLanguage) => {
        setLanguagePreferenceState(nextLanguage)
        writeStoredPreference(LANGUAGE_STORAGE_KEY, nextLanguage)
      },
      t: (key) => translate(resolvedLanguage, key),
    }),
    [themePreference, resolvedTheme, languagePreference, resolvedLanguage],
  )

  return (
    <ConsolePreferencesContext.Provider value={value}>
      {children}
    </ConsolePreferencesContext.Provider>
  )
}

export function useConsolePreferences() {
  const context = useContext(ConsolePreferencesContext)

  if (!context) {
    throw new Error('useConsolePreferences must be used within ConsolePreferencesProvider')
  }

  return context
}

function readStoredPreference<T extends string>(
  key: string,
  supported: readonly T[],
  fallback: T,
): T {
  if (typeof window === 'undefined') {
    return fallback
  }

  const value = window.localStorage.getItem(key)
  if (value && supported.includes(value as T)) {
    return value as T
  }

  return fallback
}

function writeStoredPreference(key: string, value: string) {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(key, value)
}

function getSystemPrefersDark() {
  return typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    ? window.matchMedia('(prefers-color-scheme: dark)').matches
    : true
}

function getSystemLanguages() {
  if (typeof navigator === 'undefined') {
    return ['en']
  }

  return navigator.languages && navigator.languages.length
    ? navigator.languages
    : [navigator.language]
}
