import { describe, expect, it } from 'vitest'

import {
  resolveLanguagePreference,
  resolveThemePreference,
} from './preferences'

describe('console preferences', () => {
  it('resolves supported system languages and falls back to English', () => {
    expect(resolveLanguagePreference('system', ['zh-CN', 'en-US'])).toBe('zh-CN')
    expect(resolveLanguagePreference('system', ['zh-TW'])).toBe('zh-TW')
    expect(resolveLanguagePreference('system', ['ja-JP'])).toBe('ja')
    expect(resolveLanguagePreference('system', ['fr-FR', 'de-DE'])).toBe('en')
    expect(resolveLanguagePreference('en', ['zh-CN'])).toBe('en')
  })

  it('resolves system theme and explicit overrides', () => {
    expect(resolveThemePreference('system', true)).toBe('dark')
    expect(resolveThemePreference('system', false)).toBe('light')
    expect(resolveThemePreference('dark', false)).toBe('dark')
    expect(resolveThemePreference('light', true)).toBe('light')
  })
})
