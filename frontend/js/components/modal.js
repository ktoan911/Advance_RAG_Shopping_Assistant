/* ==========================================================================
   Modal Component
   Handles modals, dialogs, and overlay interactions
   ========================================================================== */

class ModalComponent {
    constructor() {
        this.activeModal = null;
        this.settings = {
            historyCount: 10,
            apiEndpoint: 'http://localhost:5000',
            theme: 'light'
        };
        
        this.init();
    }

    /**
     * Initialize modal component
     */
    init() {
        this.loadSettings();
        this.bindEvents();
        this.initializeTheme();
        
        console.log('Modal component initialized');
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Settings modal events
        const settingsModal = document.getElementById('settingsModal');
        const closeSettingsModal = document.getElementById('closeSettingsModal');
        const cancelSettings = document.getElementById('cancelSettings');
        const saveSettings = document.getElementById('saveSettings');
        
        closeSettingsModal?.addEventListener('click', () => this.closeModal('settingsModal'));
        cancelSettings?.addEventListener('click', () => this.closeModal('settingsModal'));
        saveSettings?.addEventListener('click', () => this.saveSettingsAndClose());
        
        // Theme buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('theme-btn')) {
                this.handleThemeChange(e.target);
            }
        });
        
        // Modal backdrop clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });
        
        // ESC key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                this.closeModal(this.activeModal);
            }
        });
        
        // Prevent modal content clicks from closing modal
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-content') || 
                e.target.closest('.modal-content')) {
                e.stopPropagation();
            }
        });
    }

    /**
     * Open settings modal
     */
    openSettingsModal() {
        this.populateSettingsForm();
        this.openModal('settingsModal');
    }

    /**
     * Populate settings form with current values
     */
    populateSettingsForm() {
        const historyCountInput = document.getElementById('historyCount');
        const apiEndpointInput = document.getElementById('apiEndpoint');
        
        if (historyCountInput) {
            historyCountInput.value = this.settings.historyCount;
        }
        
        if (apiEndpointInput) {
            apiEndpointInput.value = this.settings.apiEndpoint;
        }
        
        // Update theme buttons
        this.updateThemeButtons();
    }

    /**
     * Update theme button states
     */
    updateThemeButtons() {
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-theme') === this.settings.theme) {
                btn.classList.add('active');
            }
        });
    }

    /**
     * Handle theme change
     * @param {HTMLElement} button - Theme button
     */
    handleThemeChange(button) {
        const theme = button.getAttribute('data-theme');
        
        // Update button states
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        button.classList.add('active');
        
        // Apply theme immediately
        this.settings.theme = theme;
        Utils.setTheme(theme);
    }

    /**
     * Save settings and close modal
     */
    async saveSettingsAndClose() {
        try {
            // Get form values
            const historyCountInput = document.getElementById('historyCount');
            const apiEndpointInput = document.getElementById('apiEndpoint');
            
            const newSettings = {
                historyCount: parseInt(historyCountInput?.value || 10),
                apiEndpoint: apiEndpointInput?.value || 'http://localhost:5000',
                theme: this.settings.theme
            };
            
            // Validate settings
            const validation = this.validateSettings(newSettings);
            if (!validation.valid) {
                Utils.showToast(validation.error, 'error');
                return;
            }
            
            // Show loading
            this.showLoadingOverlay();
            
            // Update API configuration if endpoint changed
            if (newSettings.apiEndpoint !== this.settings.apiEndpoint) {
                chatAPI.setBaseURL(newSettings.apiEndpoint);
                
                // Test connection to new endpoint
                const connectionTest = await chatAPI.isConnected();
                if (!connectionTest) {
                    Utils.showToast('Không thể kết nối đến API endpoint mới', 'warning');
                }
            }
            
            if (newSettings.historyCount !== this.settings.historyCount) {
                const response = await chatAPI.updateConfig({
                    numHistory: newSettings.historyCount
                });
                
                if (!response.success) {
                    Utils.showToast(`Không thể cập nhật cấu hình: ${response.error}`, 'error');
                    this.hideLoadingOverlay();
                    return;
                }
            }
            
            // Save settings
            this.settings = newSettings;
            this.saveSettingsToStorage();
            
            // Apply theme
            Utils.setTheme(newSettings.theme);
            
            // Update connection status
            if (window.chatComponent) {
                window.chatComponent.checkConnection();
            }
            
            this.hideLoadingOverlay();
            this.closeModal('settingsModal');
            
            Utils.showToast('Đã lưu cài đặt thành công', 'success');
            
        } catch (error) {
            console.error('Save settings error:', error);
            this.hideLoadingOverlay();
            Utils.showToast('Không thể lưu cài đặt', 'error');
        }
    }

    /**
     * Validate settings
     * @param {Object} settings - Settings to validate
     * @returns {Object} Validation result
     */
    validateSettings(settings) {
        if (!settings.historyCount || settings.historyCount < 1 || settings.historyCount > 100) {
            return {
                valid: false,
                error: 'Số lượng tin nhắn lưu trữ phải từ 1 đến 100'
            };
        }
        
        if (!settings.apiEndpoint || !settings.apiEndpoint.match(/^https?:\/\/.+/)) {
            return {
                valid: false,
                error: 'API Endpoint không hợp lệ'
            };
        }
        
        if (!['light', 'dark', 'auto'].includes(settings.theme)) {
            return {
                valid: false,
                error: 'Theme không hợp lệ'
            };
        }
        
        return { valid: true };
    }

    /**
     * Open modal
     * @param {string} modalId - Modal ID
     */
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        // Close any existing modal
        if (this.activeModal) {
            this.closeModal(this.activeModal);
        }
        
        this.activeModal = modalId;
        modal.classList.add('show');
        
        // Focus first input
        const firstInput = modal.querySelector('input, textarea, select');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }

    /**
     * Close modal
     * @param {string} modalId - Modal ID
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        modal.classList.remove('show');
        this.activeModal = null;
        
        // Restore body scroll
        document.body.style.overflow = '';
        
        // Reset form if it's settings modal
        if (modalId === 'settingsModal') {
            this.populateSettingsForm();
        }
    }

    /**
     * Show confirmation dialog
     * @param {Object} options - Dialog options
     * @returns {Promise<boolean>} User confirmation
     */
    showConfirmDialog(options = {}) {
        return new Promise((resolve) => {
            const {
                title = 'Xác nhận',
                message = 'Bạn có chắc chắn?',
                confirmText = 'Xác nhận',
                cancelText = 'Hủy',
                type = 'warning'
            } = options;
            
            // Create confirmation modal
            const modalHtml = `
                <div class="modal confirmation-modal" id="confirmationModal">
                    <div class="modal-content">
                        <div class="modal-body">
                            <div class="confirmation-icon ${type}">
                                <i class="fas fa-${this.getIconForType(type)}"></i>
                            </div>
                            <div class="confirmation-text">
                                <div class="confirmation-title">${Utils.escapeHtml(title)}</div>
                                <div class="confirmation-message">${Utils.escapeHtml(message)}</div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button class="btn btn-secondary" id="confirmCancel">${cancelText}</button>
                            <button class="btn btn-primary" id="confirmOk">${confirmText}</button>
                        </div>
                    </div>
                </div>
            `;
            
            // Add to page
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            const modal = document.getElementById('confirmationModal');
            const cancelBtn = document.getElementById('confirmCancel');
            const okBtn = document.getElementById('confirmOk');
            
            // Event handlers
            const cleanup = () => {
                modal.remove();
                document.body.style.overflow = '';
            };
            
            const handleCancel = () => {
                cleanup();
                resolve(false);
            };
            
            const handleConfirm = () => {
                cleanup();
                resolve(true);
            };
            
            cancelBtn.addEventListener('click', handleCancel);
            okBtn.addEventListener('click', handleConfirm);
            modal.addEventListener('click', (e) => {
                if (e.target === modal) handleCancel();
            });
            
            // ESC key
            const handleEsc = (e) => {
                if (e.key === 'Escape') {
                    document.removeEventListener('keydown', handleEsc);
                    handleCancel();
                }
            };
            document.addEventListener('keydown', handleEsc);
            
            // Show modal
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            
            // Focus confirm button
            setTimeout(() => okBtn.focus(), 100);
        });
    }

    /**
     * Get icon for dialog type
     * @param {string} type - Dialog type
     * @returns {string} Icon name
     */
    getIconForType(type) {
        const icons = {
            warning: 'exclamation-triangle',
            error: 'times-circle',
            info: 'info-circle',
            success: 'check-circle'
        };
        return icons[type] || 'question-circle';
    }

    /**
     * Show loading overlay
     */
    showLoadingOverlay() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('show');
        }
    }

    /**
     * Hide loading overlay
     */
    hideLoadingOverlay() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('show');
        }
    }

    /**
     * Show loading dialog
     * @param {string} message - Loading message
     * @returns {Function} Close function
     */
    showLoadingDialog(message = 'Đang xử lý...') {
        const modalHtml = `
            <div class="modal loading-dialog" id="loadingDialog">
                <div class="modal-content">
                    <div class="modal-body">
                        <div class="loading-animation"></div>
                        <div class="loading-text">${Utils.escapeHtml(message)}</div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = document.getElementById('loadingDialog');
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        return () => {
            modal.remove();
            document.body.style.overflow = '';
        };
    }

    /**
     * Initialize theme from settings
     */
    initializeTheme() {
        Utils.setTheme(this.settings.theme);
    }

    /**
     * Load settings from storage
     */
    loadSettings() {
        const stored = Utils.storage.get('app_settings', {});
        this.settings = {
            ...this.settings,
            ...stored
        };
        
        // Load theme preference
        const storedTheme = Utils.getStoredTheme();
        if (storedTheme) {
            this.settings.theme = storedTheme;
        }
    }

    /**
     * Save settings to storage
     */
    saveSettingsToStorage() {
        Utils.storage.set('app_settings', this.settings);
    }

    /**
     * Get current settings
     * @returns {Object} Current settings
     */
    getSettings() {
        return { ...this.settings };
    }

    /**
     * Update specific setting
     * @param {string} key - Setting key
     * @param {*} value - Setting value
     */
    updateSetting(key, value) {
        this.settings[key] = value;
        this.saveSettingsToStorage();
        
        // Apply changes immediately
        if (key === 'theme') {
            Utils.setTheme(value);
        } else if (key === 'apiEndpoint') {
            chatAPI.setBaseURL(value);
        }
    }

    /**
     * Reset settings to defaults
     */
    async resetSettings() {
        const confirmed = await this.showConfirmDialog({
            title: 'Đặt lại cài đặt',
            message: 'Bạn có muốn đặt lại tất cả cài đặt về mặc định không?',
            confirmText: 'Đặt lại',
            type: 'warning'
        });
        
        if (confirmed) {
            this.settings = {
                historyCount: 10,
                apiEndpoint: 'http://localhost:5000',
                theme: 'light'
            };
            
            this.saveSettingsToStorage();
            this.populateSettingsForm();
            Utils.setTheme('light');
            chatAPI.setBaseURL('http://localhost:5000');
            
            Utils.showToast('Đã đặt lại cài đặt về mặc định', 'success');
        }
    }

    /**
     * Export settings
     */
    exportSettings() {
        const exportData = {
            exported_at: new Date().toISOString(),
            settings: this.settings,
            version: '1.0.0'
        };
        
        const jsonString = JSON.stringify(exportData, null, 2);
        const filename = `chatbot_settings_${new Date().toISOString().split('T')[0]}.json`;
        
        Utils.downloadTextAsFile(jsonString, filename, 'application/json');
        Utils.showToast('Đã xuất cài đặt', 'success');
    }

    /**
     * Import settings from file
     * @param {File} file - Settings file
     */
    async importSettings(file) {
        try {
            const text = await file.text();
            const data = JSON.parse(text);
            
            if (data.settings) {
                const validation = this.validateSettings(data.settings);
                if (validation.valid) {
                    this.settings = { ...this.settings, ...data.settings };
                    this.saveSettingsToStorage();
                    this.populateSettingsForm();
                    this.initializeTheme();
                    
                    Utils.showToast('Đã import cài đặt thành công', 'success');
                } else {
                    Utils.showToast(`Cài đặt không hợp lệ: ${validation.error}`, 'error');
                }
            } else {
                Utils.showToast('File cài đặt không hợp lệ', 'error');
            }
        } catch (error) {
            console.error('Import settings error:', error);
            Utils.showToast('Không thể import cài đặt', 'error');
        }
    }

    /**
     * Destroy modal component
     */
    destroy() {
        // Close any open modals
        if (this.activeModal) {
            this.closeModal(this.activeModal);
        }
        
        // Remove event listeners (if needed)
        console.log('Modal component destroyed');
    }
}

// Export for global use
window.ModalComponent = ModalComponent; 