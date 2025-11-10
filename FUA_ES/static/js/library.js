// Library page functionality

async function flushHLS() {
  if (!confirm('Clear all HLS cache? This will terminate all active HLS streams.')) return;
  try {
    const resp = await fetch('/api/flush-hls', { method: 'POST' });
    const data = await resp.json();
    alert(data.message || 'HLS cache cleared');
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

async function killFFmpeg() {
  if (!confirm('Terminate ALL active FFmpeg processes? This will stop all video transcoding immediately.')) return;
  try {
    const resp = await fetch('/api/kill-ffmpeg', { method: 'POST' });
    const data = await resp.json();
    alert(data.message || 'FFmpeg processes terminated');
  } catch (e) {
    alert('Error: ' + e.message);
  }
}
