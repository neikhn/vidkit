import React from 'react';
import {Composition} from 'remotion';
import {BitsGallery, BitsGalleryProps} from './BitsGallery';

const defaultProps: BitsGalleryProps = {bitId: 'bit-list-reveal', durationFrames: 90, width: 1080, height: 1080};

export const BitsRoot: React.FC = () => (
  <Composition
    id="BitsGallery"
    component={BitsGallery}
    width={1080}
    height={1080}
    fps={30}
    durationInFrames={90}
    defaultProps={defaultProps}
    calculateMetadata={({props}) => ({
      durationInFrames: props.durationFrames,
      width: props.width,
      height: props.height,
      props,
    })}
  />
);
