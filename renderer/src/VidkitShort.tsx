import React from 'react';
import {Audio} from '@remotion/media';
import {
  AbsoluteFill,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type CaptionToken = {text: string; start_ms?: number; end_ms?: number; startMs?: number; endMs?: number};
type Caption = {text: string; startMs: number; endMs: number; tokens: CaptionToken[]};
type Scene = {
  id: string;
  type: string;
  title: string;
  body: string;
  startMs: number;
  endMs: number;
  status?: string;
};

export type VidkitShortProps = {
  schemaVersion: number;
  language: string;
  title: string;
  audioSrc: string;
  durationSeconds: number;
  captions: Caption[];
  scenes: Scene[];
};

const palette: Record<string, string> = {
  headline: '#6ee7ff',
  'tool-identity': '#fb7185',
  process: '#a78bfa',
  comparison: '#fbbf24',
  takeaway: '#34d399',
};

const SceneCard: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 16, stiffness: 120}});
  const glow = palette[scene.type] ?? '#6ee7ff';
  return (
    <AbsoluteFill
      style={{
        padding: '190px 76px 330px',
        justifyContent: 'center',
        transform: `translateY(${interpolate(enter, [0, 1], [70, 0])}px)`,
        opacity: enter,
      }}
    >
      <div style={{fontSize: 26, letterSpacing: 5, color: glow, textTransform: 'uppercase', fontWeight: 800}}>
        {scene.type.replace('-', ' ')}
      </div>
      <div style={{fontSize: 94, lineHeight: 0.98, fontWeight: 900, marginTop: 26}}>
        {scene.title}
      </div>
      <div style={{height: 8, width: 180, backgroundColor: glow, borderRadius: 99, margin: '34px 0'}} />
      <div style={{fontSize: 43, lineHeight: 1.22, color: '#cbd5e1', fontWeight: 600}}>{scene.body}</div>
    </AbsoluteFill>
  );
};

const Captions: React.FC<{captions: Caption[]}> = ({captions}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const now = (frame / fps) * 1000;
  const cue = captions.find((caption) => now >= caption.startMs && now <= caption.endMs);
  if (!cue) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: 80,
        right: 150,
        bottom: 190,
        textAlign: 'center',
        fontSize: 52,
        lineHeight: 1.15,
        fontWeight: 900,
        textShadow: '0 5px 20px rgba(0,0,0,.9)',
      }}
    >
      {cue.tokens.map((token, index) => {
        const start = token.startMs ?? token.start_ms ?? 0;
        const end = token.endMs ?? token.end_ms ?? start;
        const active = now >= start && now <= end;
        return (
          <React.Fragment key={`${start}-${index}`}>
            {index > 0 ? ' ' : ''}
            <span style={{color: active ? '#38bdf8' : '#fff', transform: active ? 'scale(1.06)' : undefined, display: 'inline-block'}}>
              {token.text}
            </span>
          </React.Fragment>
        );
      })}
    </div>
  );
};

export const VidkitShort: React.FC<VidkitShortProps> = (props) => {
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(circle at 50% 20%, #12304b 0%, #07111f 42%, #030712 100%)',
        color: '#fff',
        fontFamily: 'Arial, sans-serif',
        overflow: 'hidden',
      }}
    >
      <AbsoluteFill style={{opacity: 0.25, backgroundImage: 'linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px)', backgroundSize: '60px 60px'}} />
      {props.audioSrc ? <Audio src={staticFile(props.audioSrc)} /> : null}
      {props.scenes.map((scene) => {
        const from = Math.max(0, Math.floor((scene.startMs / 1000) * fps));
        const duration = Math.max(1, Math.ceil(((scene.endMs - scene.startMs) / 1000) * fps));
        return (
          <Sequence key={scene.id} from={from} durationInFrames={duration} premountFor={Math.min(fps, from)}>
            <SceneCard scene={scene} />
          </Sequence>
        );
      })}
      <Captions captions={props.captions} />
      <div style={{position: 'absolute', top: 62, left: 72, fontSize: 25, fontWeight: 800, letterSpacing: 2, color: '#94a3b8'}}>
        VIDKIT · {props.language.toUpperCase()}
      </div>
    </AbsoluteFill>
  );
};
