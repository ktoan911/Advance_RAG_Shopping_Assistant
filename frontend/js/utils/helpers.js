/* ==========================================================================
   Utility Helper Functions
   Common utility functions used throughout the application
   ========================================================================== */

/**
 * Format timestamp to human readable time
 * @param {number} timestamp - Unix timestamp
 * @returns {string} Formatted time string
 */
function formatTime(timestamp) {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) {
        return 'Vừa xong';
    }
    
    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} phút trước`;
    }
    
    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} giờ trước`;
    }
    
    // Less than 7 days
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days} ngày trước`;
    }
    
    // More than 7 days, show date
    return date.toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

/**
 * Format message time for display
 * @param {number} timestamp - Unix timestamp
 * @returns {string} Formatted time string
 */
function formatMessageTime(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Parse basic Markdown to HTML
 * @param {string} text - Markdown text
 * @returns {string} HTML string
 */
function parseMarkdown(text) {
    if (!text || typeof text !== 'string') return '';
    
    // Escape HTML entities first
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Convert markdown formatting
    html = html
        // Bold text: **text** or __text__
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.*?)__/g, '<strong>$1</strong>')
        
        // Italic text: *text* or _text_
        .replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em>$1</em>')
        .replace(/(?<!_)_([^_]+?)_(?!_)/g, '<em>$1</em>')
        
        // Code inline: `code`
        .replace(/`([^`]+?)`/g, '<code>$1</code>')
        
        // Line breaks
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    
    // Handle bullet points and lists
    const lines = html.split('<br>');
    let inList = false;
    let result = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Check if line is a bullet point
        if (line.match(/^\*\s+/) || line.match(/^-\s+/) || line.match(/^\+\s+/)) {
            if (!inList) {
                result.push('<ul>');
                inList = true;
            }
            // Remove bullet marker and wrap in li
            const content = line.replace(/^[\*\-\+]\s+/, '');
            result.push(`<li>${content}</li>`);
        } else if (line.match(/^\d+\.\s+/)) {
            if (!inList) {
                result.push('<ol>');
                inList = true;
            }
            // Remove number and wrap in li
            const content = line.replace(/^\d+\.\s+/, '');
            result.push(`<li>${content}</li>`);
        } else {
            if (inList) {
                result.push('</ul>');
                inList = false;
            }
            if (line.length > 0) {
                result.push(line);
            }
        }
    }
    
    // Close any open list
    if (inList) {
        result.push('</ul>');
    }
    
    html = result.join('<br>');
    
    // Wrap in paragraph tags if not already wrapped
    if (!html.includes('<p>') && !html.includes('<ul>') && !html.includes('<ol>')) {
        html = `<p>${html}</p>`;
    }
    
    // Clean up extra line breaks
    html = html
        .replace(/<br><br>/g, '<br>')
        .replace(/<br><\/p>/g, '</p>')
        .replace(/<p><br>/g, '<p>')
        .replace(/<br><ul>/g, '<ul>')
        .replace(/<\/ul><br>/g, '</ul>')
        .replace(/<br><ol>/g, '<ol>')
        .replace(/<\/ol><br>/g, '</ol>');
    
    return html;
}

/**
 * Debounce function to limit function calls
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

/**
 * Throttle function to limit function calls
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Generate unique ID
 * @returns {string} Unique ID
 */
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} Is valid email
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Sanitize HTML to prevent XSS
 * @param {string} str - String to sanitize
 * @returns {string} Sanitized string
 */
function sanitizeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Escape HTML entities
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
    // Handle null, undefined, or non-string values
    if (str == null || typeof str !== 'string') {
        return '';
    }
    
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * Format file size to human readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
async function copyToClipboard(text) {
    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            return true;
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            const result = document.execCommand('copy');
            document.body.removeChild(textArea);
            return result;
        }
    } catch (error) {
        console.error('Failed to copy text:', error);
        return false;
    }
}

/**
 * Download text as file
 * @param {string} text - Text content
 * @param {string} filename - File name
 * @param {string} type - MIME type
 */
function downloadTextAsFile(text, filename, type = 'text/plain') {
    const blob = new Blob([text], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

/**
 * Check if device is mobile
 * @returns {boolean} Is mobile device
 */
function isMobile() {
    return window.innerWidth <= 768 || /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

/**
 * Get preferred theme from system
 * @returns {string} Theme preference ('light' | 'dark')
 */
function getSystemTheme() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/**
 * Set theme
 * @param {string} theme - Theme name ('light' | 'dark' | 'auto')
 */
function setTheme(theme) {
    let actualTheme = theme;
    
    if (theme === 'auto') {
        actualTheme = getSystemTheme();
    }
    
    document.documentElement.setAttribute('data-theme', actualTheme);
    localStorage.setItem('theme', theme);
}

/**
 * Get stored theme preference
 * @returns {string} Theme preference
 */
function getStoredTheme() {
    return localStorage.getItem('theme') || 'light';
}

/**
 * Show toast notification
 * @param {string} message - Message to show
 * @param {string} type - Toast type ('success' | 'error' | 'warning' | 'info')
 * @param {number} duration - Duration in milliseconds
 */
function showToast(message, type = 'info', duration = 3000) {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-header">
            <span class="toast-title">${getToastTitle(type)}</span>
            <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="toast-message">${message}</div>
    `;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto remove
    if (duration > 0) {
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

/**
 * Get toast title based on type
 * @param {string} type - Toast type
 * @returns {string} Toast title
 */
function getToastTitle(type) {
    const titles = {
        success: 'Thành công',
        error: 'Lỗi',
        warning: 'Cảnh báo',
        info: 'Thông báo'
    };
    return titles[type] || 'Thông báo';
}

/**
 * Scroll element into view smoothly
 * @param {HTMLElement} element - Element to scroll to
 * @param {string} block - Scroll position ('start' | 'center' | 'end')
 */
function scrollIntoView(element, block = 'start') {
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: block
        });
    }
}

/**
 * Auto resize textarea based on content
 * @param {HTMLTextAreaElement} textarea - Textarea element
 */
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

/**
 * Local storage wrapper with error handling
 */
const storage = {
    get: (key, defaultValue = null) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return defaultValue;
        }
    },
    
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error writing to localStorage:', error);
            return false;
        }
    },
    
    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    }
};

/**
 * Check if user is online
 * @returns {boolean} Online status
 */
function isOnline() {
    return navigator.onLine;
}

/**
 * Add event listener for online/offline status
 * @param {Function} callback - Callback function
 */
function onNetworkChange(callback) {
    window.addEventListener('online', () => callback(true));
    window.addEventListener('offline', () => callback(false));
}

// Export functions for use in other modules
window.Utils = {
    formatTime,
    formatMessageTime,
    parseMarkdown,
    debounce,
    throttle,
    generateId,
    isValidEmail,
    sanitizeHtml,
    escapeHtml,
    formatFileSize,
    copyToClipboard,
    downloadTextAsFile,
    isMobile,
    getSystemTheme,
    setTheme,
    getStoredTheme,
    showToast,
    scrollIntoView,
    autoResizeTextarea,
    storage,
    isOnline,
    onNetworkChange
}; 