export type ThemePreference = 'system' | 'light' | 'dark'
export type ResolvedTheme = 'light' | 'dark'

export type LanguagePreference = 'system' | 'en' | 'zh-CN' | 'zh-TW' | 'ja'
export type ResolvedLanguage = 'en' | 'zh-CN' | 'zh-TW' | 'ja'

export const THEME_STORAGE_KEY = 'fruitfly-console-theme'
export const LANGUAGE_STORAGE_KEY = 'fruitfly-console-language'

export function resolveThemePreference(
  preference: ThemePreference,
  prefersDark: boolean,
): ResolvedTheme {
  if (preference === 'light' || preference === 'dark') {
    return preference
  }

  return prefersDark ? 'dark' : 'light'
}

export function resolveLanguagePreference(
  preference: LanguagePreference,
  languages: readonly string[],
): ResolvedLanguage {
  if (preference !== 'system') {
    return preference
  }

  for (const language of languages) {
    const normalized = normalizeLanguageTag(language)
    if (normalized) {
      return normalized
    }
  }

  return 'en'
}

function normalizeLanguageTag(language: string): ResolvedLanguage | null {
  const tag = language.toLowerCase()

  if (tag.startsWith('zh-cn') || tag.startsWith('zh-sg') || tag.startsWith('zh-hans')) {
    return 'zh-CN'
  }
  if (
    tag.startsWith('zh-tw') ||
    tag.startsWith('zh-hk') ||
    tag.startsWith('zh-mo') ||
    tag.startsWith('zh-hant')
  ) {
    return 'zh-TW'
  }
  if (tag.startsWith('ja')) {
    return 'ja'
  }
  if (tag.startsWith('en')) {
    return 'en'
  }

  return null
}
