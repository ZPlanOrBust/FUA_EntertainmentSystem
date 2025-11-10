// Shared player functionality for both Direct and HLS players
let subtitleOffset = 0;

function showStatus(message, type = 'success', duration = 2500) {
  const box = document.getElementById('status-box');
  box.textContent = message;
  box.className = 'status-box ' + (type === 'error' ? 'status-error' : type === 'warning' ? 'status-warning' : 'status-success');
  box.style.display = 'block';
  setTimeout(() => { box.style.display = 'none'; }, duration);
}

async function extractEmbeddedSubtitles(){
  const encoded = encodeURIComponent(MEDIA_PATH);
  showStatus('Extracting embedded subtitles...', 'warning', 3000);
  try {
    const resp = await fetch(`/extract_subtitles/${encoded}`, { method: 'POST' });
    const data = await resp.json();
    if (data.status === 'success') {
      showStatus(data.message, 'success', 3000);
      setTimeout(() => location.reload(), 1500);
    } else {
      showStatus(data.message || 'Extraction failed', 'error', 4000);
    }
  } catch (e) {
    showStatus('Error extracting subtitles: ' + e.message, 'error', 4000);
  }
}

function adjustSubtitleTiming(seconds) {
  const tracks = video.textTracks;
  subtitleOffset += seconds;
  document.getElementById('subtitle-offset').textContent = (subtitleOffset >= 0 ? '+' : '') + subtitleOffset.toFixed(1) + 's';
  for (let i = 0; i < tracks.length; i++) {
    if (tracks[i].mode === 'showing') { updateTrackTiming(tracks[i]); }
  }
  showStatus(`Subtitle timing adjusted by ${seconds > 0 ? '+' : ''}${seconds}s`);
}

function resetSubtitleTiming() {
  const tracks = video.textTracks;
  subtitleOffset = 0;
  document.getElementById('subtitle-offset').textContent = '0.0s';
  let resetCount = 0;
  for (let i = 0; i < tracks.length; i++) {
    if (tracks[i].mode === 'showing' && tracks[i].cues) {
      for (let j = 0; j < tracks[i].cues.length; j++) {
        const cue = tracks[i].cues[j];
        if (cue.originalStartTime !== undefined) {
          cue.startTime = cue.originalStartTime;
          cue.endTime = cue.originalEndTime;
          resetCount++;
        }
      }
    }
  }
  if (resetCount > 0) {
    showStatus('Subtitle timing reset');
  }
}

function updateTrackTiming(track) {
  if (!track.cues) return;
  for (let i = 0; i < track.cues.length; i++) {
    const cue = track.cues[i];
    if (typeof cue.originalStartTime === 'undefined') {
      cue.originalStartTime = cue.startTime; cue.originalEndTime = cue.endTime;
    }
    cue.startTime = cue.originalStartTime + subtitleOffset;
    cue.endTime = cue.originalEndTime + subtitleOffset;
  }
}

async function loadExternalSubtitles() {
  try {
    const encoded = encodeURIComponent(MEDIA_PATH);
    const resp = await fetch(`/list_subtitles/${encoded}`);
    if (!resp.ok) throw new Error('Subtitles list failed');
    const data = await resp.json();
    if (data.status !== 'success') return [];
    const existing = Array.from(video.querySelectorAll('track[data-external="true"]')); existing.forEach(t => t.remove());
    const added = [];
    for (const sub of data.subtitles) {
      const track = document.createElement('track');
      track.kind = 'subtitles';
      track.label = `${sub.label} (${sub.language.toUpperCase()})`;
      track.srclang = sub.language;
      track.src = `/get_subtitle?media_path=${encodeURIComponent(MEDIA_PATH)}&subtitle_path=${encodeURIComponent(sub.path)}`;
      track.setAttribute('data-external','true');
      track.setAttribute('data-subtitle-path', sub.path);
      track.default = false;
      video.appendChild(track);
      console.log('[Subtitles] Added track:', track.label, track.src);
      added.push(track);
    }
    return added;
  } catch (e) { console.warn('No external subtitles', e); return []; }
}

async function loadSubtitleTracks() {
  const container = document.getElementById('subtitle-tracks-container');
  const info = document.getElementById('track-info');
  container.innerHTML = '';
  const disabled = document.createElement('div'); disabled.className='list-item'; disabled.innerHTML = '<button class="btn btn-sm btn-muted" onclick="activateTrack(-1)">None (Disable Subtitles)</button>';
  container.appendChild(disabled);
  const tracks = Array.from(video.textTracks || []);
  let count = 0;
  tracks.forEach((track, idx) => {
    if (track.kind !== 'subtitles') return;
    const label = track.label || track.language || `Track ${idx+1}`;
    const isExternal = track.mode !== 'disabled' ? false : (video.querySelector(`track[data-external="true"]`) ? true : false);
    const trackEl = video.querySelectorAll('track')[idx];
    const isExternalTrack = trackEl && trackEl.getAttribute('data-external') === 'true';
    const trackSrc = trackEl ? trackEl.src : '';
    const deleteBtn = isExternalTrack && trackSrc ? `<button class='btn btn-sm' style='background:#b91c1c;color:white;margin-left:4px' onclick='event.stopPropagation();deleteSubtitle("${trackSrc}",${idx})' title='Delete subtitle file'>🗑️</button>` : '';
    const item = document.createElement('div');
    item.className = 'list-item';
    item.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><div>${label}</div><div style="display:flex;gap:4px"><button class='btn btn-sm btn-accent' onclick='activateTrack(${idx})'>Activate</button>${deleteBtn}</div></div>`;
    container.appendChild(item); count++;
  });
  info.textContent = count>0?`Found ${count} subtitle track(s).`:'No subtitle tracks found.';
}

function activateTrack(index){
  const tracks = video.textTracks;
  console.log('[Subtitles] Activating track index:', index, 'Total tracks:', tracks.length);
  
  // Disable all tracks first
  for (let i=0;i<tracks.length;i++){ 
    tracks[i].mode = 'disabled';
  }
  
  // Activate selected track
  if (index>=0 && index<tracks.length){ 
    const track = tracks[index];
    track.mode = 'showing';
    console.log('[Subtitles] Track activated:', track.label, 'Mode:', track.mode);
    
    // Wait for cues to load before applying timing
    const checkCues = () => {
      if (track.cues && track.cues.length > 0) {
        console.log('[Subtitles] Track loaded with', track.cues.length, 'cues');
        updateTrackTiming(track);
      } else {
        console.log('[Subtitles] Waiting for cues to load...');
        setTimeout(checkCues, 100);
      }
    };
    setTimeout(checkCues, 50);
    
    showStatus('Subtitle track activated: ' + track.label); 
  } else { 
    console.log('[Subtitles] All tracks disabled');
    showStatus('Subtitles disabled'); 
  }
  
  document.getElementById('subtitle-track-modal').classList.remove('show');
}

async function showSubtitleTrackSelector(){
  const modal = document.getElementById('subtitle-track-modal');
  modal.classList.add('show');
  await loadExternalSubtitles();
  await loadSubtitleTracks();
}

async function deleteSubtitle(trackSrc, trackIndex) {
  if (!confirm('Are you sure you want to delete this subtitle file? This cannot be undone.')) return;
  try {
    const trackEl = video.querySelectorAll('track')[trackIndex];
    if (!trackEl) { showStatus('Track not found', 'error'); return; }
    const subtitlePath = trackEl.getAttribute('data-subtitle-path');
    if (!subtitlePath) { showStatus('Subtitle path not found', 'error'); return; }
    showStatus('Deleting subtitle...', 'warning');
    const url = `/delete_subtitle?media_path=${encodeURIComponent(MEDIA_PATH)}&subtitle_path=${encodeURIComponent(subtitlePath)}`;
    const resp = await fetch(url, { method: 'DELETE' });
    const data = await resp.json();
    if (data.status === 'success') {
      showStatus(data.message || 'Subtitle deleted', 'success');
      trackEl.remove();
      setTimeout(async () => { await showSubtitleTrackSelector(); }, 600);
    } else {
      showStatus(data.message || 'Delete failed', 'error');
    }
  } catch (e) {
    showStatus('Error deleting subtitle: ' + e.message, 'error');
  }
}

async function findSubtitles(language) {
  const modal = document.getElementById('subtitle-modal');
  const resultContainer = document.getElementById('subtitle-results');
  const statusDiv = document.getElementById('subtitle-status');
  resultContainer.innerHTML = '';
  statusDiv.textContent = 'Searching...';
  statusDiv.style.display = 'block';
  try {
    const encoded = encodeURIComponent(MEDIA_PATH);
    const resp = await fetch(`/find_subs/${encoded}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language: language })
    });
    const data = await resp.json();
    statusDiv.style.display = 'none';
    if (data.status === 'error') {
      showStatus(data.message || 'Search failed', 'error', 4000);
      return;
    }
    if (!data.results || data.results.length === 0) {
      resultContainer.innerHTML = '<div style="padding:12px;text-align:center;color:#888">No subtitles found</div>';
      return;
    }
    data.results.forEach((sub, idx) => {
      const item = document.createElement('div');
      item.className = 'list-item';
      item.style.cursor = 'pointer';
      item.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
        <div style="flex:1"><strong>${sub.title}</strong></div>
        <button class='btn btn-sm btn-accent' onclick='downloadSelectedSubtitle(${JSON.stringify(sub).replace(/'/g, "&#39;")})'>Download</button>
      </div>`;
      resultContainer.appendChild(item);
    });
  } catch (e) {
    statusDiv.style.display = 'none';
    showStatus('Error searching subtitles: ' + e.message, 'error', 4000);
  }
}

async function downloadSelectedSubtitle(subData) {
  showStatus('Downloading subtitle...', 'warning', 3000);
  try {
    const encoded = encodeURIComponent(MEDIA_PATH);
    const resp = await fetch(`/download_sub/${encoded}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subtitle_data: subData })
    });
    const data = await resp.json();
    if (data.status === 'success') {
      showStatus(data.message, 'success', 3000);
      document.getElementById('subtitle-modal').classList.remove('show');
      setTimeout(() => location.reload(), 1500);
    } else {
      showStatus(data.message || 'Download failed', 'error', 4000);
    }
  } catch (e) {
    showStatus('Error downloading subtitle: ' + e.message, 'error', 4000);
  }
}
