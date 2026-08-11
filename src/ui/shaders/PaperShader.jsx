import React from 'react';
import { SimplexNoise } from '@paper-design/shaders-react';

/**
 * YouParts Paper Shader Accent Component
 * Palette: Off-White / Tactile Cream / Ink Black / YouTube Red
 */
export const PaperShader = ({ width = "100%", height = "100%" }) => {
  return (
    <SimplexNoise
      width={width}
      height={height}
      colors={[
        "#FFFFFF", // Crisp White
        "#FBF9F5", // Tactile Paper Base
        "#FF0000", // YouTube Red Accent
        "#ECE8E0", // Warm Gray Contour
        "#121212", // Stark Ink Black
        "#F2EFE9"  // Mid-tone Paper
      ]}
      stepsPerColor={2}
      softness={0.25}  // Kept crisp to maintain tactile paper grain lines
      speed={0.15}     // Slow, subtle ambient drift
      scale={0.45}     // Organic large-scale topographic contours
      fit="cover"
      minPixelRatio={2}
    />
  );
};

export default PaperShader;