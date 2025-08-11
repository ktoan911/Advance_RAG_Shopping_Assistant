/* ==========================================================================
   Sidebar Component
   Handles navigation, chat history, and sidebar interactions
   ========================================================================== */

class SidebarComponent {
    constructor() {
        this.isCollapsed = false;
        this.chatHistory = [];
        this.currentChatId = null;
        
        // Elements
        this.sidebar = null;
        this.sidebarToggle = null;
        this.newChatBtn = null;
        this.chatHistoryList = null;
        this.exportHistoryBtn = null;
        this.settingsBtn = null;
        
        this.init();
    }

    /**
     * Initialize sidebar component
     */
    init() {
        this.bindElements();
        this.bindEvents();
        this.loadChatHistory();
        this.restoreSidebarState();
        
        console.log('Sidebar component initialized');
    }

    /**
     * Bind DOM elements
     */
    bindElements() {
        this.sidebar = document.querySelector('.sidebar');
        this.sidebarToggle = document.getElementById('sidebarToggle');
        this.newChatBtn = document.getElementById('newChatBtn');
        this.chatHistoryList = document.getElementById('chatHistoryList');
        this.exportHistoryBtn = document.getElementById('exportHistoryBtn');
        this.settingsBtn = document.getElementById('settingsBtn');
        
        if (!this.sidebar) {
            console.error('Sidebar element not found');
            return;
        }
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Sidebar toggle
        this.sidebarToggle?.addEventListener('click', () => this.toggleSidebar());
        
        // New chat button
        this.newChatBtn?.addEventListener('click', () => this.createNewChat());
        
        // Export history button
        this.exportHistoryBtn?.addEventListener('click', () => this.exportHistory());
        
        // Settings button
        this.settingsBtn?.addEventListener('click', () => this.openSettings());
        
        // Chat history item clicks
        this.chatHistoryList?.addEventListener('click', (e) => this.handleHistoryItemClick(e));
        
        // Mobile sidebar overlay
        if (Utils.isMobile()) {
            this.createMobileOverlay();
        }
        
        // Window resize handler
        window.addEventListener('resize', Utils.debounce(() => this.handleResize(), 250));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }

    /**
     * Handle keyboard shortcuts
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + B: Toggle sidebar
        if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
            e.preventDefault();
            this.toggleSidebar();
        }
        
        // Ctrl/Cmd + N: New chat
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            this.createNewChat();
        }
    }

    /**
     * Toggle sidebar visibility
     */
    toggleSidebar() {
        this.isCollapsed = !this.isCollapsed;
        
        if (Utils.isMobile()) {
            this.sidebar?.classList.toggle('open');
            this.showMobileOverlay(this.sidebar?.classList.contains('open'));
        } else {
            this.sidebar?.classList.toggle('collapsed', this.isCollapsed);
        }
        
        // Save state
        Utils.storage.set('sidebar_collapsed', this.isCollapsed);
        
        // Dispatch event for other components
        window.dispatchEvent(new CustomEvent('sidebarToggled', {
            detail: { collapsed: this.isCollapsed }
        }));
    }

    /**
     * Create new chat session
     */
    createNewChat() {
        // Clear current chat
        if (window.chatComponent) {
            window.chatComponent.clearChatDisplay();
            window.chatComponent.showWelcomeMessage();
            window.chatComponent.messages = [];
            window.chatComponent.saveMessagesToStorage();
        }
        
        // Reset current chat ID
        this.currentChatId = null;
        this.updateActiveHistoryItem();
        
        // Close mobile sidebar
        if (Utils.isMobile()) {
            this.closeMobileSidebar();
        }
        
        Utils.showToast('Đã bắt đầu cuộc trò chuyện mới', 'info', 2000);
    }

    /**
     * Load chat history from storage and API
     */
    async loadChatHistory() {
        try {
            // Load from local storage first
            const localHistory = Utils.storage.get('chat_history', []);
            if (localHistory.length > 0) {
                this.chatHistory = localHistory;
                this.renderChatHistory();
            }
            
            const response = await chatAPI.getChatHistory();
            
            if (response.success && response.history.length > 0) {
                this.processChatHistoryFromAPI(response.history);
                this.renderChatHistory();
                this.saveChatHistoryToStorage();
            } else if (this.chatHistory.length === 0) {
                this.renderEmptyState();
            }
            
        } catch (error) {
            console.error('Load chat history error:', error);
            if (this.chatHistory.length === 0) {
                this.renderEmptyState();
            }
        }
    }

    /**
     * Process chat history from API response
     * @param {Array} apiHistory - History from API
     */
    processChatHistoryFromAPI(apiHistory) {
        this.chatHistory = apiHistory.map((item, index) => ({
            id: item.id || Utils.generateId(),
            title: this.generateChatTitle(item.user_message || item.query),
            preview: this.generatePreview(item.user_message || item.query),
            timestamp: item.timestamp || Date.now() / 1000,
            messageCount: 1,
            lastMessage: item.user_message || item.query
        }));
    }

    /**
     * Generate chat title from first message
     * @param {string} message - First message
     * @returns {string} Chat title
     */
    generateChatTitle(message) {
        if (!message) return 'Cuộc trò chuyện mới';
        
        // Truncate and clean message for title
        const cleaned = message.replace(/\s+/g, ' ').trim();
        return cleaned.length > 30 ? cleaned.substring(0, 30) + '...' : cleaned;
    }

    /**
     * Generate preview text
     * @param {string} message - Message content
     * @returns {string} Preview text
     */
    generatePreview(message) {
        if (!message) return 'Không có tin nhắn';
        
        const cleaned = message.replace(/\s+/g, ' ').trim();
        return cleaned.length > 50 ? cleaned.substring(0, 50) + '...' : cleaned;
    }

    /**
     * Render chat history list
     */
    renderChatHistory() {
        if (!this.chatHistoryList) return;
        
        if (this.chatHistory.length === 0) {
            this.renderEmptyState();
            return;
        }
        
        // Sort by timestamp (newest first)
        const sortedHistory = [...this.chatHistory].sort((a, b) => b.timestamp - a.timestamp);
        
        this.chatHistoryList.innerHTML = sortedHistory.map(chat => `
            <div class="chat-history-item ${chat.id === this.currentChatId ? 'active' : ''}" 
                 data-chat-id="${chat.id}">
                <div class="chat-history-icon">
                    <i class="fas fa-comment"></i>
                </div>
                <div class="chat-history-content">
                    <div class="chat-history-title">${Utils.escapeHtml(chat.title)}</div>
                    <div class="chat-history-preview">${Utils.escapeHtml(chat.preview)}</div>
                </div>
                <div class="chat-history-time">${Utils.formatTime(chat.timestamp)}</div>
                <div class="chat-history-actions">
                    <button class="history-action-btn" data-action="load" title="Tải cuộc trò chuyện">
                        <i class="fas fa-folder-open"></i>
                    </button>
                    <button class="history-action-btn delete" data-action="delete" title="Xóa">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * Render empty state
     */
    renderEmptyState() {
        if (!this.chatHistoryList) return;
        
        this.chatHistoryList.innerHTML = `
            <div class="chat-history-empty">
                <div class="empty-icon">
                    <i class="fas fa-comments"></i>
                </div>
                <div class="empty-text">
                    Chưa có cuộc trò chuyện nào.<br>
                    Bắt đầu chat để xem lịch sử.
                </div>
            </div>
        `;
    }

    /**
     * Handle chat history item clicks
     * @param {Event} e - Click event
     */
    handleHistoryItemClick(e) {
        const actionBtn = e.target.closest('.history-action-btn');
        const historyItem = e.target.closest('.chat-history-item');
        
        if (!historyItem) return;
        
        const chatId = historyItem.getAttribute('data-chat-id');
        
        if (actionBtn) {
            e.stopPropagation();
            const action = actionBtn.getAttribute('data-action');
            
            switch (action) {
                case 'load':
                    this.loadChatSession(chatId);
                    break;
                case 'delete':
                    this.deleteChatSession(chatId);
                    break;
            }
        } else {
            // Load chat session on item click
            this.loadChatSession(chatId);
        }
    }

    /**
     * Load specific chat session
     * @param {string} chatId - Chat session ID
     */
    async loadChatSession(chatId) {
        try {
            const chat = this.chatHistory.find(c => c.id === chatId);
            if (!chat) return;
            

            this.currentChatId = chatId;
            this.updateActiveHistoryItem();
            
            // Clear current chat and load session
            if (window.chatComponent) {
                window.chatComponent.clearChatDisplay();
                window.chatComponent.hideWelcomeMessage();
                
                // Load messages for this session (placeholder)
                // TODO: Implement actual message loading from API
                window.chatComponent.addMessage('user', chat.lastMessage);
                window.chatComponent.addMessage('assistant', 'Đây là cuộc trò chuyện đã được tải từ lịch sử.');
            }
            
            // Close mobile sidebar
            if (Utils.isMobile()) {
                this.closeMobileSidebar();
            }
            
            Utils.showToast(`Đã tải cuộc trò chuyện: ${chat.title}`, 'success', 2000);
            
        } catch (error) {
            console.error('Load chat session error:', error);
            Utils.showToast('Không thể tải cuộc trò chuyện', 'error');
        }
    }

    /**
     * Delete chat session
     * @param {string} chatId - Chat session ID
     */
    async deleteChatSession(chatId) {
        try {
            const chat = this.chatHistory.find(c => c.id === chatId);
            if (!chat) return;
            
            // Confirm deletion
            if (!confirm(`Bạn có chắc muốn xóa cuộc trò chuyện "${chat.title}"?`)) {
                return;
            }
            
            // Remove from local history
            this.chatHistory = this.chatHistory.filter(c => c.id !== chatId);
            
            // Update display
            this.renderChatHistory();
            this.saveChatHistoryToStorage();
            
            // Clear current chat if it was the deleted one
            if (this.currentChatId === chatId) {
                this.currentChatId = null;
                if (window.chatComponent) {
                    window.chatComponent.clearChatDisplay();
                    window.chatComponent.showWelcomeMessage();
                }
            }
            
            Utils.showToast('Đã xóa cuộc trò chuyện', 'success');
            
        } catch (error) {
            console.error('Delete chat session error:', error);
            Utils.showToast('Không thể xóa cuộc trò chuyện', 'error');
        }
    }

    /**
     * Update active history item highlight
     */
    updateActiveHistoryItem() {
        if (!this.chatHistoryList) return;
        
        // Remove active class from all items
        this.chatHistoryList.querySelectorAll('.chat-history-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to current chat
        if (this.currentChatId) {
            const activeItem = this.chatHistoryList.querySelector(`[data-chat-id="${this.currentChatId}"]`);
            activeItem?.classList.add('active');
        }
    }

    /**
     * Export chat history
     */
    async exportHistory() {
        try {
            if (window.chatComponent) {
                await window.chatComponent.exportChat();
            } else {
                // Fallback: export local history
                const exportData = {
                    exported_at: new Date().toISOString(),
                    chat_history: this.chatHistory,
                    total_chats: this.chatHistory.length
                };
                
                const jsonString = JSON.stringify(exportData, null, 2);
                const filename = `chat_history_${new Date().toISOString().split('T')[0]}.json`;
                
                Utils.downloadTextAsFile(jsonString, filename, 'application/json');
                Utils.showToast('Đã xuất lịch sử chat', 'success');
            }
        } catch (error) {
            console.error('Export history error:', error);
            Utils.showToast('Không thể xuất lịch sử', 'error');
        }
    }

    /**
     * Open settings modal
     */
    openSettings() {
        if (window.modalComponent) {
            window.modalComponent.openSettingsModal();
        }
    }

    /**
     * Create mobile overlay
     */
    createMobileOverlay() {
        if (document.querySelector('.sidebar-overlay')) return;
        
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.addEventListener('click', () => this.closeMobileSidebar());
        
        document.body.appendChild(overlay);
    }

    /**
     * Show mobile overlay
     * @param {boolean} show - Show overlay
     */
    showMobileOverlay(show) {
        const overlay = document.querySelector('.sidebar-overlay');
        if (overlay) {
            overlay.classList.toggle('show', show);
        }
    }

    /**
     * Close mobile sidebar
     */
    closeMobileSidebar() {
        if (Utils.isMobile()) {
            this.sidebar?.classList.remove('open');
            this.showMobileOverlay(false);
        }
    }

    /**
     * Handle window resize
     */
    handleResize() {
        if (Utils.isMobile()) {
            // Ensure sidebar is properly positioned on mobile
            this.sidebar?.classList.remove('collapsed');
            this.isCollapsed = false;
        } else {
            // Close mobile sidebar if switching to desktop
            this.closeMobileSidebar();
        }
    }

    /**
     * Restore sidebar state from storage
     */
    restoreSidebarState() {
        const collapsed = Utils.storage.get('sidebar_collapsed', false);
        
        if (!Utils.isMobile() && collapsed) {
            this.isCollapsed = true;
            this.sidebar?.classList.add('collapsed');
        }
    }

    /**
     * Save chat history to storage
     */
    saveChatHistoryToStorage() {
        Utils.storage.set('chat_history', this.chatHistory);
    }

    /**
     * Add new chat to history
     * @param {Object} chatData - Chat data
     */
    addChatToHistory(chatData) {
        const newChat = {
            id: Utils.generateId(),
            title: this.generateChatTitle(chatData.firstMessage),
            preview: this.generatePreview(chatData.firstMessage),
            timestamp: Date.now() / 1000,
            messageCount: chatData.messageCount || 1,
            lastMessage: chatData.firstMessage
        };
        
        this.chatHistory.unshift(newChat);
        this.currentChatId = newChat.id;
        
        this.renderChatHistory();
        this.saveChatHistoryToStorage();
        
        return newChat;
    }

    /**
     * Update chat in history
     * @param {string} chatId - Chat ID
     * @param {Object} updates - Updates to apply
     */
    updateChatInHistory(chatId, updates) {
        const chatIndex = this.chatHistory.findIndex(c => c.id === chatId);
        
        if (chatIndex !== -1) {
            this.chatHistory[chatIndex] = {
                ...this.chatHistory[chatIndex],
                ...updates,
                timestamp: Date.now() / 1000
            };
            
            this.renderChatHistory();
            this.saveChatHistoryToStorage();
        }
    }

    /**
     * Get current chat
     * @returns {Object|null} Current chat data
     */
    getCurrentChat() {
        return this.chatHistory.find(c => c.id === this.currentChatId) || null;
    }

    /**
     * Destroy sidebar component
     */
    destroy() {
        // Remove event listeners
        this.sidebarToggle?.removeEventListener('click', this.toggleSidebar);
        this.newChatBtn?.removeEventListener('click', this.createNewChat);
        window.removeEventListener('resize', this.handleResize);
        
        // Remove mobile overlay
        document.querySelector('.sidebar-overlay')?.remove();
        
        console.log('Sidebar component destroyed');
    }
}

// Export for global use
window.SidebarComponent = SidebarComponent; 