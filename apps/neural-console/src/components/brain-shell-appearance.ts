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

interface NeuropilGlowMaterialAppearanceInput {
  baseColor: string
  glowStrength: number
  theme: ResolvedTheme
}

export function getNeuropilGlowMaterialAppearance({
  baseColor,
  glowStrength,
  theme,
}: NeuropilGlowMaterialAppearanceInput) {
  const resolvedStrength = Math.min(1, Math.max(0, glowStrength))
  const minOpacity = theme === 'dark' ? 0.12 : 0.1
  const maxOpacity = theme === 'dark' ? 0.72 : 0.64
  const opacity = minOpacity + (maxOpacity - minOpacity) * resolvedStrength
  const baseEmissiveStrength = theme === 'dark' ? 0.32 : 0.26
  const emissiveStrength = baseEmissiveStrength + resolvedStrength * 0.88
  const base = new Color(baseColor)

  return {
    color: base,
    opacity,
    transparent: true,
    roughness: theme === 'dark' ? 0.42 : 0.38,
    metalness: 0.06,
    depthWrite: false,
    emissive: base.clone().multiplyScalar(0.45 + 0.55 * resolvedStrength),
    emissiveIntensity: emissiveStrength,
  }
}
