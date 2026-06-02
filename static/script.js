document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('download-form');
    const urlInput = document.getElementById('url-input');
    const downloadBtn = document.getElementById('download-btn');
    const statusArea = document.getElementById('status-area');
    const statusText = document.getElementById('status-text');
    
    const alertBanner = document.getElementById('alert-banner');
    const alertMessage = document.getElementById('alert-message');
    const alertCloseBtn = document.getElementById('alert-close');
    
    const progressContainer = document.getElementById('progress-container');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressPercent = document.getElementById('progress-percent');
    const progressSize = document.getElementById('progress-size');
    const spinnerRing = document.getElementById('spinner-ring');

    // Close alert banner
    alertCloseBtn.addEventListener('click', () => {
        alertBanner.classList.add('hidden');
    });

    let alertTimeout;

    const showAlert = (message, duration = 5000) => {
        alertMessage.textContent = message;
        alertBanner.classList.remove('hidden');
        
        // Auto-dismiss alert for reliability
        clearTimeout(alertTimeout);
        if (duration > 0) {
            alertTimeout = setTimeout(() => {
                alertBanner.classList.add('hidden');
            }, duration);
        }
    };

    const isValidYouTubeUrl = (url) => {
        const pattern = /^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$/;
        return pattern.test(url);
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Hide any existing alerts
        alertBanner.classList.add('hidden');
        clearTimeout(alertTimeout);
        
        const url = urlInput.value.trim();
        const format = document.querySelector('input[name="format"]:checked').value;

        if (!url || !isValidYouTubeUrl(url)) {
            showAlert("Please enter a valid YouTube video URL.");
            return;
        }

        // Update UI for loading state
        downloadBtn.style.display = 'none';
        statusArea.classList.remove('hidden');
        progressContainer.classList.remove('hidden');
        spinnerRing.style.display = 'block';
        progressBarFill.style.width = '0%';
        progressPercent.textContent = '0%';
        progressSize.textContent = '';
        
        if (format === 'video') {
            statusText.textContent = "Processing high definition video. This may take a few moments...";
        } else {
            statusText.textContent = "Extracting standard audio. This may take a few moments...";
        }

        const taskId = 'task_' + Math.random().toString(36).substr(2, 9);
        
        let progressInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/progress/${taskId}`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.status === 'downloading') {
                        const percent = data.percent.toFixed(1);
                        progressBarFill.style.width = `${percent}%`;
                        progressPercent.textContent = `${percent}%`;
                        
                        if (data.total > 0) {
                            const mbDownloaded = (data.downloaded / (1024 * 1024)).toFixed(1);
                            const mbTotal = (data.total / (1024 * 1024)).toFixed(1);
                            progressSize.textContent = `${mbDownloaded} MB / ${mbTotal} MB`;
                        }
                    } else if (data.status === 'processing') {
                        progressBarFill.style.width = '100%';
                        progressPercent.textContent = '100%';
                        progressSize.textContent = 'Processing and finalizing...';
                    }
                }
            } catch (err) {
                console.error("Error fetching progress", err);
            }
        }, 500);

        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url, format, task_id: taskId })
            });

            clearInterval(progressInterval);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Download failed. Please check the URL and try again.");
            }

            // Get filename from Content-Disposition header if available
            let filename = `download.${format === 'audio' ? 'mp3' : 'mp4'}`;
            const disposition = response.headers.get('content-disposition');
            if (disposition && disposition.indexOf('filename=') !== -1) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) { 
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            // Convert response to blob
            const blob = await response.blob();
            
            // Create a temporary link to trigger download
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = decodeURIComponent(filename);
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
            
            // Reset UI
            urlInput.value = '';
            statusArea.classList.add('hidden');
            progressContainer.classList.add('hidden');
            downloadBtn.style.display = 'block';
            
        } catch (error) {
            clearInterval(progressInterval);
            console.error("Download error:", error);
            showAlert(error.message);
            // Reset UI
            statusArea.classList.add('hidden');
            progressContainer.classList.add('hidden');
            downloadBtn.style.display = 'block';
        }
    });
});
