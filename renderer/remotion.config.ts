import {Config} from '@remotion/cli/config';

const studioOutput = process.env.VIDKIT_STUDIO_OUTPUT;

if (studioOutput) {
  Config.setOutputLocation(studioOutput);
}
