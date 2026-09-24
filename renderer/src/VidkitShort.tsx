import React from 'react';
import {Audio} from '@remotion/media';
import {
  AbsoluteFill,
  continueRender,
  delayRender,
  Img,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type CaptionToken = {text: string; start_ms?: number; end_ms?: number; startMs?: number; endMs?: number};
type Caption = {text: string; startMs: number; endMs: number; tokens: CaptionToken[]};
type Asset = {id: string; src?: string; description?: string; width?: number; height?: number};
type Crop = {x: number; y: number; width: number; height: number};
type Callout = {text?: string; x?: number; y?: number};
type SafeArea = {top: number; right: number; bottom: number; left: number};
type Scene = {
  id: string;
  layout: 'hook' | 'screenshot' | 'steps' | 'takeaway';
  purpose?: string;
  title: string;
  body: string;
  startMs: number;
  endMs: number;
  status?: string;
  asset?: Asset | null;
  assetRequired?: boolean;
  crop?: Crop;
  callout?: Callout | null;
};

export type VidkitShortProps = {
  schemaVersion: number;
  language: string;
  title: string;
  audioSrc: string;
  durationSeconds: number;
  captions: Caption[];
  scenes: Scene[];
  safeArea?: SafeArea;
};

const defaultSafeArea: SafeArea = {top: 88, right: 150, bottom: 260, left: 64};
const nfc = (value: string | undefined) => (value ?? '').normalize('NFC');

const captionFontSize = (text: string, maxWidth = 820) => {
  if (typeof document === 'undefined') return text.length > 32 ? 43 : 49;
  const context = document.createElement('canvas').getContext('2d');
  if (!context) return 43;
  for (const size of [49, 46, 43, 40, 38]) {
    context.font = `800 ${size}px "Noto Sans"`;
    let lines = 1;
    let width = 0;
    for (const word of text.split(/\s+/)) {
      const wordWidth = context.measureText(`${width ? ' ' : ''}${word}`).width;
      if (width && width + wordWidth > maxWidth) {
        lines += 1;
        width = context.measureText(word).width;
      } else {
        width += wordWidth;
      }
    }
    if (lines <= 2) return size;
  }
  return 38;
};

const revealStyle = (frame: number, fps: number): React.CSSProperties => {
  const enter = spring({frame, fps, config: {damping: 18, stiffness: 120}});
  return {
    opacity: enter,
    transform: `translateY(${interpolate(enter, [0, 1], [42, 0])}px)`,
  };
};

const Eyebrow: React.FC<{children: React.ReactNode}> = ({children}) => (
  <div style={{fontSize: 25, fontWeight: 800, color: '#1677ff', letterSpacing: 1.2, textTransform: 'uppercase'}}>
    {children}
  </div>
);

const Title: React.FC<{children: React.ReactNode; compact?: boolean}> = ({children, compact}) => {
  const length = String(children ?? '').length;
  const fontSize = compact ? (length > 34 ? 60 : 68) : length > 34 ? 72 : 90;
  return (
    <div
      style={{
        fontSize,
        lineHeight: 1.08,
        fontWeight: 900,
        color: '#10233f',
        letterSpacing: -2.4,
        marginTop: 18,
        display: '-webkit-box',
        WebkitBoxOrient: 'vertical',
        WebkitLineClamp: 2,
        overflow: 'hidden',
      }}
    >
      {children}
    </div>
  );
};

const Body: React.FC<{children: React.ReactNode}> = ({children}) => (
  <div style={{fontSize: 38, lineHeight: 1.35, fontWeight: 600, color: '#526176', marginTop: 24}}>{children}</div>
);

const AssetPanel: React.FC<{scene: Scene}> = ({scene}) => {
  const asset = scene.asset;
  const crop = scene.crop ?? {x: 0, y: 0, width: 1, height: 1};
  if (!asset?.src) {
    return (
      <div
        style={{
          height: 790,
          borderRadius: 38,
          background: '#e8edf5',
          border: '3px dashed #9aa8ba',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          padding: 72,
          color: '#607087',
          fontSize: 34,
          fontWeight: 700,
        }}
      >
        Cần bổ sung ảnh minh họa cho cảnh này
      </div>
    );
  }
  const imageStyle: React.CSSProperties = {
    position: 'absolute',
    width: `${100 / crop.width}%`,
    height: `${100 / crop.height}%`,
    left: `${(-crop.x / crop.width) * 100}%`,
    top: `${(-crop.y / crop.height) * 100}%`,
    objectFit: 'cover',
  };
  return (
    <div style={{height: 790, borderRadius: 38, background: '#fff', overflow: 'hidden', position: 'relative', boxShadow: '0 24px 80px rgba(35, 60, 90, .18)', border: '1px solid #dfe6ef'}}>
      <Img src={staticFile(asset.src)} style={imageStyle} />
      {scene.callout?.text ? (
        <div
          style={{
            position: 'absolute',
            left: `${(scene.callout.x ?? 0.08) * 100}%`,
            top: `${(scene.callout.y ?? 0.74) * 100}%`,
            transform: 'translate(-5%, -50%)',
            maxWidth: 660,
            padding: '16px 24px',
            borderRadius: 20,
            background: '#1677ff',
            color: '#fff',
            fontSize: 28,
            lineHeight: 1.25,
            fontWeight: 800,
            boxShadow: '0 12px 35px rgba(22, 119, 255, .35)',
          }}
        >
          {nfc(scene.callout.text)}
        </div>
      ) : null}
    </div>
  );
};

const HookScene: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{padding: '300px 84px 420px', justifyContent: 'center', ...revealStyle(frame, fps)}}>
      <Eyebrow>Điểm đáng chú ý</Eyebrow>
      <Title>{nfc(scene.title)}</Title>
      {scene.body ? <Body>{nfc(scene.body)}</Body> : null}
      <div style={{width: 120, height: 10, borderRadius: 99, background: '#1677ff', marginTop: 38}} />
    </AbsoluteFill>
  );
};

const ScreenshotScene: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{padding: '150px 66px 350px', ...revealStyle(frame, fps)}}>
      <Eyebrow>Demo sản phẩm</Eyebrow>
      <Title compact>{nfc(scene.title)}</Title>
      <div style={{marginTop: 34}}><AssetPanel scene={scene} /></div>
    </AbsoluteFill>
  );
};

const StepsScene: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{padding: '220px 76px 390px', justifyContent: 'center', ...revealStyle(frame, fps)}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 22}}>
        <div style={{width: 62, height: 62, borderRadius: 18, background: '#1677ff', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 30, fontWeight: 900}}>→</div>
        <Eyebrow>Cách hoạt động</Eyebrow>
      </div>
      <Title compact>{nfc(scene.title)}</Title>
      {scene.body ? <Body>{nfc(scene.body)}</Body> : null}
      {scene.asset ? <div style={{marginTop: 38, transform: 'scale(.86)', transformOrigin: 'top center'}}><AssetPanel scene={scene} /></div> : null}
    </AbsoluteFill>
  );
};

const TakeawayScene: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{padding: '300px 82px 430px', justifyContent: 'center', ...revealStyle(frame, fps)}}>
      <div style={{padding: '54px 48px', borderRadius: 42, background: '#10233f', boxShadow: '0 30px 90px rgba(16, 35, 63, .28)'}}>
        <Eyebrow>Kết luận</Eyebrow>
        <div style={{fontSize: scene.title.length > 34 ? 62 : 72, lineHeight: 1.12, fontWeight: 900, color: '#fff', marginTop: 20, display: '-webkit-box', WebkitBoxOrient: 'vertical', WebkitLineClamp: 2, overflow: 'hidden'}}>{nfc(scene.title)}</div>
        {scene.body ? <div style={{fontSize: 36, lineHeight: 1.38, fontWeight: 600, color: '#cbd7e8', marginTop: 24}}>{nfc(scene.body)}</div> : null}
      </div>
    </AbsoluteFill>
  );
};

const SceneView: React.FC<{scene: Scene}> = ({scene}) => {
  if (scene.layout === 'screenshot') return <ScreenshotScene scene={scene} />;
  if (scene.layout === 'steps') return <StepsScene scene={scene} />;
  if (scene.layout === 'takeaway') return <TakeawayScene scene={scene} />;
  return <HookScene scene={scene} />;
};

const Captions: React.FC<{captions: Caption[]; safeArea: SafeArea}> = ({captions, safeArea}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const now = (frame / fps) * 1000;
  const cue = captions.find((caption) => now >= caption.startMs && now <= caption.endMs);
  if (!cue) return null;
  const size = captionFontSize(cue.text);
  return (
    <div style={{position: 'absolute', left: safeArea.left + 12, right: safeArea.right + 12, bottom: safeArea.bottom, textAlign: 'center'}}>
      <div style={{display: '-webkit-inline-box', WebkitBoxOrient: 'vertical', WebkitLineClamp: 2, overflow: 'hidden', maxWidth: 820, borderRadius: 24, padding: '18px 24px 20px', background: 'rgba(16, 35, 63, .92)', fontSize: size, lineHeight: 1.22, fontWeight: 800, color: '#fff', boxShadow: '0 12px 40px rgba(0, 0, 0, .22)'}}>
        {cue.tokens.map((token, index) => {
          const start = token.startMs ?? token.start_ms ?? 0;
          const end = token.endMs ?? token.end_ms ?? start;
          const active = now >= start && now <= end;
          return (
            <React.Fragment key={`${start}-${index}`}>
              {index > 0 ? ' ' : ''}
              <span style={{color: active ? '#62b0ff' : '#fff'}}>{nfc(token.text)}</span>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export const VidkitShort: React.FC<VidkitShortProps> = (props) => {
  const {fps} = useVideoConfig();
  const safeArea = props.safeArea ?? defaultSafeArea;
  const [fontHandle] = React.useState(() => delayRender('Loading bundled Noto Sans fonts'));
  React.useEffect(() => {
    let finished = false;
    const finish = () => {
      if (!finished) {
        finished = true;
        continueRender(fontHandle);
      }
    };
    Promise.all([
      document.fonts.load('400 32px "Noto Sans"'),
      document.fonts.load('600 32px "Noto Sans"'),
      document.fonts.load('700 32px "Noto Sans"'),
      document.fonts.load('800 32px "Noto Sans"'),
      document.fonts.load('900 32px "Noto Sans"'),
      document.fonts.ready,
    ]).then(finish, finish);
    return finish;
  }, [fontHandle]);
  return (
    <AbsoluteFill style={{background: 'linear-gradient(145deg, #f8fafc 0%, #edf3f9 65%, #e7eef8 100%)', color: '#10233f', fontFamily: 'Noto Sans, sans-serif', overflow: 'hidden'}}>
      <AbsoluteFill style={{opacity: 0.45, backgroundImage: 'radial-gradient(circle at 12% 10%, rgba(22,119,255,.12), transparent 28%), radial-gradient(circle at 90% 60%, rgba(80,145,255,.10), transparent 32%)'}} />
      {props.audioSrc ? <Audio src={staticFile(props.audioSrc)} /> : null}
      {props.scenes.map((scene) => {
        const from = Math.max(0, Math.floor((scene.startMs / 1000) * fps));
        const duration = Math.max(1, Math.ceil(((scene.endMs - scene.startMs) / 1000) * fps));
        return <Sequence key={scene.id} from={from} durationInFrames={duration} premountFor={Math.min(fps, from)}><SceneView scene={scene} /></Sequence>;
      })}
      <Captions captions={props.captions} safeArea={safeArea} />
      <div style={{position: 'absolute', top: safeArea.top, left: safeArea.left, fontSize: 22, fontWeight: 800, letterSpacing: 1.4, color: '#718096'}}>VIDKIT · {props.language.toUpperCase()}</div>
    </AbsoluteFill>
  );
};
