import { describe, expect, it } from 'vitest'

import { getBrainShellMaterialAppearance } from './brain-shell-appearance'

describe('getBrainShellMaterialAppearance', () => {
  it('raises overly transparent shells in light theme for readability', () => {
    const appearance = getBrainShellMaterialAppearance({
      baseColor: '#89a5ff',
      opacity: 0.18,
      theme: 'light',
    })

    expect(appearance.opacity).toBe(0.34)
    expect(appearance.emissiveStrength).toBe(0.08)
  })

  it('keeps dark theme shells slightly denser than light theme shells', () => {
    const darkAppearance = getBrainShellMaterialAppearance({
      baseColor: '#89a5ff',
      opacity: 0.18,
      theme: 'dark',
    })

    expect(darkAppearance.opacity).toBe(0.4)
    expect(darkAppearance.emissiveStrength).toBe(0.1)
  })

  it('does not reduce already-opaque shells', () => {
    const appearance = getBrainShellMaterialAppearance({
      baseColor: '#89a5ff',
      opacity: 0.56,
      theme: 'light',
    })

    expect(appearance.opacity).toBe(0.56)
  })
})
