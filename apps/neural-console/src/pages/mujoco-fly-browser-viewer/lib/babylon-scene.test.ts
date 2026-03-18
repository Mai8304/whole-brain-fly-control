import { describe, expect, it } from 'vitest'

import {
  materialColorFromRgba,
  resolveCameraPresetConfig,
} from './babylon-scene'

describe('babylon-scene helpers', () => {
  it('converts official rgba into a viewer material config instead of a single hardcoded dark color', () => {
    const material = materialColorFromRgba([0.67, 0.35, 0.14, 1])

    expect(material.diffuse).toEqual([0.67, 0.35, 0.14])
    expect(material.alpha).toBe(1)
  })

  it('derives preset camera placement from the official camera manifest', () => {
    const preset = resolveCameraPresetConfig(
      {
        preset: 'track',
        camera_name: 'walker/track1',
        mode: 'trackcom',
        position: [0.6, 0.6, 0.22],
        quaternion: [0.312, 0.221, 0.533, 0.754],
        xyaxes: null,
        fovy: null,
      },
      [0, 0, 0.13],
    )

    expect(preset.radius).toBeGreaterThan(0.45)
    expect(preset.target).toEqual([0, 0, 0.13])
  })
})
