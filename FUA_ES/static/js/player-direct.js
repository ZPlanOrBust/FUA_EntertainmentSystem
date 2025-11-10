// Direct player initialization
const video = document.getElementById('player');
const MEDIA_PATH = document.body.dataset.mediaPath;
const fullDuration = Number(video.dataset.duration || 0);

// Set src before Plyr initialization
video.src = video.dataset.src;
console.log('[DirectPlayer] Video src set to:', video.src);
console.log('[DirectPlayer] Full duration from server:', fullDuration);

// Initialize Plyr
const player = new Plyr('#player');
console.log('[DirectPlayer] Plyr initialized');

// Error handling
video.addEventListener('error', (e) => {
  console.error('[DirectPlayer] Video error:', e, video.error);
  showStatus('Video load error: ' + (video.error ? video.error.message : 'Unknown'), 'error', 5000);
});

// Handle metadata loaded
video.addEventListener('loadedmetadata', () => {
  console.log('[DirectPlayer] Metadata loaded, duration:', video.duration);
  // Override duration if we have it from server (for transcoded streams)
  if (fullDuration > 0 && (video.duration === 0 || isNaN(video.duration) || video.duration === Infinity)) {
    console.log('[DirectPlayer] Overriding duration with server value:', fullDuration);
    Object.defineProperty(video, 'duration', {
      get: () => fullDuration,
      configurable: true
    });
  }
  const start = Number(video.dataset.start || 0);
  if (start > 0) { video.currentTime = start; }
  loadExternalSubtitles();
});

// Also try to set duration early for transcoded streams
if (fullDuration > 0) {
  setTimeout(() => {
    if (video.duration === 0 || isNaN(video.duration) || video.duration === Infinity) {
      console.log('[DirectPlayer] Setting duration before metadata loaded');
      Object.defineProperty(video, 'duration', {
        get: () => fullDuration,
        configurable: true
      });
      player.duration = fullDuration;
    }
  }, 500);
}
