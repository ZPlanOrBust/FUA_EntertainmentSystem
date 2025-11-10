// HLS player initialization
const video = document.getElementById('player');
const player = new Plyr('#player');
const MEDIA_PATH = document.body.dataset.mediaPath;
const streamUrl = video.dataset.src;
const fullDuration = Number(video.dataset.duration || 0);

if (Hls.isSupported()) {
  const hls = new Hls({
    lowLatencyMode: false, 
    maxBufferLength: 30, 
    maxMaxBufferLength: 600,
    startPosition: 0  // Always start from beginning
  });
  hls.loadSource(streamUrl);
  hls.attachMedia(video);
  hls.on(Hls.Events.MANIFEST_PARSED, () => {
    // Override duration if we have it from server
    if (fullDuration > 0 && video.duration !== fullDuration) {
      Object.defineProperty(video, 'duration', {
        get: () => fullDuration,
        configurable: true
      });
    }
    // Set start position if provided
    const start = Number(video.dataset.start || 0);
    if (start > 0) {
      video.currentTime = start;
    } else {
      video.currentTime = 0;  // Ensure we start at the beginning
    }
    loadExternalSubtitles();
  });
  hls.on(Hls.Events.LEVEL_LOADED, (event, data) => {
    // Keep trying to set proper duration
    if (fullDuration > 0 && data.details && data.details.totalduration !== fullDuration) {
      data.details.totalduration = fullDuration;
    }
  });
} else if (video.canPlayType('application/vnd.apple.mpegurl')) {
  video.src = streamUrl;
  video.addEventListener('loadedmetadata', () => {
    if (fullDuration > 0 && video.duration !== fullDuration) {
      Object.defineProperty(video, 'duration', {
        get: () => fullDuration,
        configurable: true
      });
    }
    // Set start position if provided
    const start = Number(video.dataset.start || 0);
    if (start > 0) {
      video.currentTime = start;
    } else {
      video.currentTime = 0;  // Ensure we start at the beginning
    }
    loadExternalSubtitles();
  });
} else {
  video.src = streamUrl;
}
