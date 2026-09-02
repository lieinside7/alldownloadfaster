// DownloaderFaster - Download Functionality

async function handleDownload(url) {
    // Create modal
    var modal = document.createElement('div');
    modal.className = 'dl-modal';
    modal.innerHTML = '<div class="dl-modal-content"><div class="dl-loading"><div class="dl-spinner"></div><p>Fetching video info...</p></div></div>';
    document.body.appendChild(modal);
    
    // Close on background click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) modal.remove();
    });
    
    try {
        var response = await fetch('/api/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });
        var data = await response.json();
        
        if (data.error) {
            modal.querySelector('.dl-modal-content').innerHTML = '<div class="dl-error"><p>' + data.error + '</p><button class="dl-close" onclick="this.closest(\'.dl-modal\').remove()">Close</button></div>';
            return;
        }
        
        showDownloadOptions(modal, data, url);
    } catch (error) {
        modal.querySelector('.dl-modal-content').innerHTML = '<div class="dl-error"><p>Gagal mengambil info video</p><button class="dl-close" onclick="this.closest(\'.dl-modal\').remove()">Close</button></div>';
    }
}

function showDownloadOptions(modal, info, url) {
    var duration = formatDuration(info.duration);
    
    var html = '<div class="dl-results">';
    html += '<div class="dl-header">';
    html += '<img src="' + info.thumbnail + '" class="dl-thumb" alt="thumbnail">';
    html += '<div class="dl-meta">';
    html += '<h3>' + escapeHtml(info.title) + '</h3>';
    html += '<p>' + escapeHtml(info.uploader || 'Unknown') + ' | ' + duration + '</p>';
    html += '</div>';
    html += '</div>';
    
    html += '<div class="dl-formats">';
    
    // Video formats
    var videoFormats = info.formats.filter(function(f) { return f.type === 'video' || f.type === 'merged'; });
    if (videoFormats.length > 0) {
        html += '<h4>Video</h4>';
        videoFormats.forEach(function(f) {
            html += '<div class="dl-item" onclick="startDownload(\'' + escapeHtml(url) + '\', \'' + f.format_id + '\')">';
            html += '<span class="dl-quality">' + f.quality + '</span>';
            html += '<span class="dl-ext">' + f.ext.toUpperCase() + '</span>';
            html += '<button class="dl-btn-small">Download</button>';
            html += '</div>';
        });
    }
    
    // Audio formats
    var audioFormats = info.formats.filter(function(f) { return f.type === 'audio'; });
    if (audioFormats.length > 0) {
        html += '<h4>Audio (MP3)</h4>';
        audioFormats.forEach(function(f) {
            html += '<div class="dl-item" onclick="startDownload(\'' + escapeHtml(url) + '\', \'' + f.format_id + '\')">';
            html += '<span class="dl-quality">' + f.quality + '</span>';
            html += '<span class="dl-ext">MP3</span>';
            html += '<button class="dl-btn-small">Download MP3</button>';
            html += '</div>';
        });
    }
    
    html += '</div>';
    html += '<button class="dl-close" onclick="this.closest(\'.dl-modal\').remove()">Close</button>';
    html += '</div>';
    
    modal.querySelector('.dl-modal-content').innerHTML = html;
}

async function startDownload(url, formatId) {
    try {
        var response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url, format_id: formatId })
        });
        var data = await response.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        pollStatus(data.id);
    } catch (error) {
        alert('Download failed');
    }
}

async function pollStatus(downloadId) {
    var interval = setInterval(async function() {
        try {
            var response = await fetch('/api/status/' + downloadId);
            var status = await response.json();
            
            if (status.status === 'completed') {
                clearInterval(interval);
                window.location.href = '/api/file/' + downloadId;
            } else if (status.status === 'error') {
                clearInterval(interval);
                alert(status.error || 'Download failed');
            }
        } catch (error) {
            console.error(error);
        }
    }, 1000);
}

function formatDuration(seconds) {
    if (!seconds) return '0:00';
    var hrs = Math.floor(seconds / 3600);
    var mins = Math.floor((seconds % 3600) / 60);
    var secs = Math.floor(seconds % 60);
    
    if (hrs > 0) {
        return hrs + ':' + String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
    }
    return mins + ':' + String(secs).padStart(2, '0');
}

function escapeHtml(text) {
    if (!text) return '';
    var map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}
