import { Color } from 'three'

import type { ResolvedTheme } from '@/lib/preferences'

interface BrainShellMaterialAppearanceInput {
  baseColor: string
  opacity: number
  theme: ResolvedTheme
}

export function getBrainShellMaterialAppearance({
  baseColor,
  opacity,
  theme,
}: BrainShellMaterialAppearanceInput) {
  const minimumOpacity = theme === 'dark' ? 0.4 : 0.34
  const resolvedOpacity = Math.max(opacity, minimumOpacity)
  const emissiveStrength = theme === 'dark' ? 0.1 : 0.08

  return {
    color: new Color(baseColor),
    opacity: resolvedOpacity,
    transparent: true,
    roughness: theme === 'dark' ? 0.4 : 0.36,
    metalness: 0.05,
    emissive: new Color(baseColor).multiplyScalar(emissiveStrength),
    emissiveStrength,
  }
}
