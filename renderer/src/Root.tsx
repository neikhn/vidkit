import React from 'react';
import {CalculateMetadataFunction, Composition} from 'remotion';
import {VidkitShort, VidkitShortProps} from './VidkitShort';

const defaultProps: VidkitShortProps = {
  schemaVersion: 1,
  language: 'vi',
  title: 'Vidkit preview',
  audioSrc: '',
  durationSeconds: 10,
  captions: [],
  scenes: [
    {
      id: 'scene-1',
      type: 'headline',
      title: 'Vidkit preview',
      body: 'Truyền timeline JSON để dựng video.',
      startMs: 0,
      endMs: 10000,
      status: 'provisional',
    },
  ],
};

const calculateMetadata: CalculateMetadataFunction<VidkitShortProps> = ({props}) => ({
  durationInFrames: Math.max(1, Math.ceil(props.durationSeconds * 30)),
  props,
});

export const RemotionRoot: React.FC = () => (
  <Composition
    id="VidkitShort"
    component={VidkitShort}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={300}
    defaultProps={defaultProps}
    calculateMetadata={calculateMetadata}
  />
);
