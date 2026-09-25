import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Component as ListReveal} from '../node_modules/remotion-bits/docs/src/bits/examples/staggered-motion/ListReveal';
import {Component as CardStack} from '../node_modules/remotion-bits/docs/src/bits/examples/staggered-motion/CardStack';
import {Component as ChatConversation} from '../node_modules/remotion-bits/docs/src/bits/examples/staggered-motion/ChatConversation';
import {Component as BasicTypewriter} from '../node_modules/remotion-bits/docs/src/bits/examples/typewriter/BasicTypewriter';
import {Component as BlurIn} from '../node_modules/remotion-bits/docs/src/bits/examples/animated-text/BlurSlideWord';
import {Component as CharacterByCharacter} from '../node_modules/remotion-bits/docs/src/bits/examples/animated-text/CharByChar';
import {Component as CliSimulation} from '../node_modules/remotion-bits/docs/src/bits/examples/typewriter/CLISimulation';
import {Component as FadeIn} from '../node_modules/remotion-bits/docs/src/bits/examples/animated-text/FadeIn';
import {Component as MultiTextTypewriter} from '../node_modules/remotion-bits/docs/src/bits/examples/typewriter/MultiTextTypewriter';
import {Component as GlitchCycle} from '../node_modules/remotion-bits/docs/src/bits/examples/animated-text/GlitchCycle';
import {Component as TypingCodeBlock} from '../node_modules/remotion-bits/docs/src/bits/examples/code-block/TypingCodeBlock';
import {Component as WordByWord} from '../node_modules/remotion-bits/docs/src/bits/examples/animated-text/WordByWord';
import {Component as VariableSpeedTypewriter} from '../node_modules/remotion-bits/docs/src/bits/examples/typewriter/VariableSpeedTypewriter';
import {Component as RadialGradient} from '../node_modules/remotion-bits/docs/src/bits/examples/gradient-transition/RadialGradient';
import {Component as Fireflies} from '../node_modules/remotion-bits/docs/src/bits/examples/particle-system/Fireflies';
import {Component as Carousel3D} from '../node_modules/remotion-bits/docs/src/bits/examples/scene-3d/Carousel';
import {Component as Basic3DScene} from '../node_modules/remotion-bits/docs/src/bits/examples/scene-3d/3DBasic';
import {Component as Terminal3D} from '../node_modules/remotion-bits/docs/src/bits/examples/scene-3d/Terminal3D';
import {Component as CursorFlyover} from './vendor/CursorFlyover';
import {Component as Transform3DShowcase} from '../node_modules/remotion-bits/docs/src/bits/examples/scene-3d/Transform3DShowcase';
import {Component as BarChart} from '../node_modules/remotion-bits/docs/src/bits/examples/animated-counter/BarChart';
import {Component as StatRings} from '../node_modules/remotion-bits/docs/src/bits/examples/animated-counter/StatRings';
import {Component as CodeBlock} from '../node_modules/remotion-bits/docs/src/bits/examples/code-block/BasicCodeBlock';

export const bits: Record<string, React.ComponentType> = {
  'bit-list-reveal': ListReveal,
  'bit-card-stack': CardStack,
  'bit-chat-conversation': ChatConversation,
  'basic-typewriter': BasicTypewriter,
  'bit-blur-slide-word': BlurIn,
  'bit-char-by-char': CharacterByCharacter,
  'cli-simulation': CliSimulation,
  'bit-fade-in': FadeIn,
  'multitext-typewriter': MultiTextTypewriter,
  'bit-glitch-cycle': GlitchCycle,
  'bit-typing-code-block': TypingCodeBlock,
  'bit-word-by-word': WordByWord,
  'variable-speed-typewriter': VariableSpeedTypewriter,
  'bit-radial-gradient': RadialGradient,
  'bit-fireflies': Fireflies,
  'bit-carousel-3d': Carousel3D,
  'bit-3d-basic': Basic3DScene,
  'bit-terminal-3d': Terminal3D,
  'bit-cursor-flyover': CursorFlyover,
  'bit-transform3d-showcase': Transform3DShowcase,
  'bit-bar-chart': BarChart,
  'bit-stat-rings': StatRings,
  'bit-basic-code-block': CodeBlock,
};

export type BitsGalleryProps = {
  bitId: string;
  durationFrames: number;
  width: number;
  height: number;
};

export const BitsGallery: React.FC<BitsGalleryProps> = ({bitId}) => {
  const Bit = bits[bitId];
  if (!Bit) throw new Error(`Unknown Remotion Bit: ${bitId}`);
  const textBit = new Set([
    'bit-blur-slide-word', 'bit-char-by-char', 'bit-fade-in', 'bit-glitch-cycle',
    'bit-word-by-word',
  ]).has(bitId);
  const style = {
    backgroundColor: '#080d19', color: '#fff', display: 'flex', alignItems: 'center',
    justifyContent: 'center', overflow: 'hidden', fontSize: textBit ? 96 : 42, fontWeight: 700,
    '--color-background-dark': '#080d19', '--color-surface-dark': '#15233a',
    '--color-surface-light': '#283a59', '--color-primary': '#58aeff',
    '--color-primary-hover': '#85c8ff', '--color-border-light': '#4d668a',
    '--color-border-dark': '#14233a',
  } as React.CSSProperties;
  return <AbsoluteFill style={style}>
    <Bit />
  </AbsoluteFill>;
};
