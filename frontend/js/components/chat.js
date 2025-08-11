/* ==========================================================================
   Chat Component
   Handles chat interface, message display, and user interactions
   ========================================================================== */

class ChatComponent {
    constructor() {
        this.messages = [];
        this.isTyping = false;
        this.currentMessageId = null;
        
        // Elements
        this.chatMessages = null;
        this.messageInput = null;
        this.sendBtn = null;
        this.typingIndicator = null;
        this.charCount = null;
        this.connectionStatus = null;
        
        // Settings
        this.maxMessageLength = 1000;
        this.autoScrollEnabled = true;
        
        this.init();
    }

    /**
     * Initialize chat component
     */
    init() {
        this.bindElements();
        this.bindEvents();
        this.loadStoredMessages();
        this.checkConnection();
        
        console.log('Chat component initialized');
    }

    /**
     * Bind DOM elements
     */
    bindElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.charCount = document.getElementById('charCount');
        this.connectionStatus = document.getElementById('connectionStatus');
        
        if (!this.chatMessages || !this.messageInput || !this.sendBtn) {
            console.error('Required chat elements not found');
            return;
        }
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Send button click
        this.sendBtn?.addEventListener('click', () => this.handleSendMessage());
        
        // Input events
        this.messageInput?.addEventListener('keydown', (e) => this.handleInputKeydown(e));
        this.messageInput?.addEventListener('input', (e) => this.handleInputChange(e));
        this.messageInput?.addEventListener('paste', (e) => this.handleInputPaste(e));
        
        // Suggestion buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion-btn')) {
                const question = e.target.getAttribute('data-question');
                if (question) {
                    this.messageInput.value = question;
                    this.handleSendMessage();
                }
            }
        });
        
        // Network status monitoring
        Utils.onNetworkChange((isOnline) => {
            this.updateConnectionStatus(isOnline ? 'connected' : 'offline');
        });
    }

    /**
     * Handle input keydown events
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleInputKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.handleSendMessage();
        }
    }

    /**
     * Handle input change events
     * @param {Event} e - Input event
     */
    handleInputChange(e) {
        const value = e.target.value;
        
        // Update character count
        if (this.charCount) {
            this.charCount.textContent = value.length;
        }
        
        // Auto-resize textarea
        Utils.autoResizeTextarea(e.target);
        
        // Update send button state
        this.updateSendButtonState();
    }

    /**
     * Handle input paste events
     * @param {ClipboardEvent} e - Paste event
     */
    handleInputPaste(e) {
        setTimeout(() => {
            const value = this.messageInput.value;
            if (value.length > this.maxMessageLength) {
                this.messageInput.value = value.substring(0, this.maxMessageLength);
                Utils.showToast('Tin nhắn đã được cắt ngắn do vượt quá giới hạn ký tự', 'warning');
            }
            this.updateSendButtonState();
        }, 0);
    }

    /**
     * Handle send message action
     */
    async handleSendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isTyping) {
            return;
        }

        // Validate message
        const validation = chatAPI.validateMessage(message);
        if (!validation.valid) {
            Utils.showToast(validation.error, 'error');
            return;
        }

        // Clear input and hide welcome message
        this.messageInput.value = '';
        this.updateSendButtonState();
        this.hideWelcomeMessage();
        
        // Add user message to chat
        const userMessage = this.addMessage('user', validation.message);
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {

            const response = await chatAPI.sendMessage(validation.message);
            
            if (response.success) {
                // Add bot response
                this.addMessage('assistant', response.message, {
                    processingTime: response.processingTime
                });
                
                // Store conversation
                this.saveMessagesToStorage();
                
                Utils.showToast('Tin nhắn đã được gửi thành công', 'success', 2000);
            } else {
                // Handle error
                this.addMessage('assistant', `Kết nối mạng không ổn định, vui lòng kiểm tra lại!`, {
                    isError: true
                });
                Utils.showToast(`Lỗi: ${response.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Send message error:', error);
            this.addMessage('assistant', 'Xin lỗi, không thể kết nối đến server. Vui lòng thử lại sau.', {
                isError: true
            });
            Utils.showToast('Không thể gửi tin nhắn', 'error');
        } finally {
            this.hideTypingIndicator();
        }
    }

    /**
     * Add message to chat
     * @param {string} type - Message type ('user' | 'assistant')
     * @param {string} content - Message content
     * @param {Object} options - Additional options
     * @returns {Object} Message object
     */
    addMessage(type, content, options = {}) {
        // Validate input
        if (!type || (content == null)) {
            console.warn('❌ Invalid message data:', { type, content });
            return null;
        }

        // Ensure content is a string
        const safeContent = String(content || '');

        const message = {
            id: Utils.generateId(),
            type: type,
            content: safeContent,
            timestamp: Date.now() / 1000,
            ...options
        };

        this.messages.push(message);
        this.renderMessage(message);
        
        if (this.autoScrollEnabled) {
            this.scrollToBottom();
        }

        return message;
    }

    /**
     * Render message in chat
     * @param {Object} message - Message object
     */
    renderMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${message.type}`;
        messageEl.setAttribute('data-message-id', message.id);

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = message.type === 'user' ? 
            '<i class="fas fa-user"></i>' : 
            '<i class="fas fa-robot"></i>';

        const content = document.createElement('div');
        content.className = 'message-content';
        
        // Handle error messages
        if (message.isError) {
            content.classList.add('error');
        }
        
        // Use markdown parsing for assistant messages, escape HTML for user messages
        if (message.type === 'assistant') {
            content.innerHTML = Utils.parseMarkdown(message.content);
        } else {
            content.innerHTML = Utils.escapeHtml(message.content);
        }

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = Utils.formatMessageTime(message.timestamp);

        // Add processing time for assistant messages
        if (message.type === 'assistant' && message.processingTime) {
            time.textContent += ` • ${message.processingTime.toFixed(2)}s`;
        }

        messageEl.appendChild(avatar);
        
        const messageBody = document.createElement('div');
        messageBody.appendChild(content);
        messageBody.appendChild(time);
        messageEl.appendChild(messageBody);

        this.chatMessages.appendChild(messageEl);
        
        // Animate message appearance
        requestAnimationFrame(() => {
            messageEl.classList.add('show');
        });
    }

    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        this.isTyping = true;
        this.updateSendButtonState();
        
        if (this.typingIndicator) {
            this.typingIndicator.classList.add('show');
            if (this.autoScrollEnabled) {
                this.scrollToBottom();
            }
        }
    }

    /**
     * Hide typing indicator
     */
    hideTypingIndicator() {
        this.isTyping = false;
        this.updateSendButtonState();
        
        if (this.typingIndicator) {
            this.typingIndicator.classList.remove('show');
        }
    }

    /**
     * Hide welcome message
     */
    hideWelcomeMessage() {
        const welcomeMessage = this.chatMessages?.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }
    }

    /**
     * Show welcome message
     */
    showWelcomeMessage() {
        const welcomeMessage = this.chatMessages?.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.style.display = 'block';
        }
    }

    /**
     * Clear chat messages
     */
    async clearChat() {
        try {
            const response = await chatAPI.clearChatHistory();
            
            if (response.success) {
                this.messages = [];
                this.clearChatDisplay();
                this.showWelcomeMessage();
                this.saveMessagesToStorage();
                Utils.showToast('Đã xóa lịch sử chat', 'success');
            } else {
                Utils.showToast(`Không thể xóa lịch sử: ${response.error}`, 'error');
            }
        } catch (error) {
            console.error('Clear chat error:', error);
            Utils.showToast('Không thể xóa lịch sử chat', 'error');
        }
    }

    /**
     * Clear chat display
     */
    clearChatDisplay() {
        if (this.chatMessages) {
            const messages = this.chatMessages.querySelectorAll('.message');
            messages.forEach(msg => msg.remove());
        }
    }

    /**
     * Scroll to bottom of chat
     */
    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }

    /**
     * Update send button state
     */
    updateSendButtonState() {
        if (!this.sendBtn) return;
        
        const hasText = this.messageInput?.value.trim().length > 0;
        const canSend = hasText && !this.isTyping;
        
        this.sendBtn.disabled = !canSend;
    }

    /**
     * Update connection status display
     * @param {string} status - Connection status
     */
    updateConnectionStatus(status) {
        if (!this.connectionStatus) return;
        
        const statusDot = this.connectionStatus.querySelector('.status-dot');
        const statusText = this.connectionStatus.querySelector('.status-text');
        
        // Remove existing status classes
        statusDot?.classList.remove('connected', 'error');
        
        switch (status) {
            case 'connected':
                statusDot?.classList.add('connected');
                if (statusText) statusText.textContent = 'Đã kết nối';
                break;
            case 'error':
                statusDot?.classList.add('error');
                if (statusText) statusText.textContent = 'Lỗi kết nối';
                break;
            case 'offline':
                if (statusText) statusText.textContent = 'Không có mạng';
                break;
            default:
                if (statusText) statusText.textContent = 'Đang kết nối...';
        }
    }

    /**
     * Check API connection status
     */
    async checkConnection() {
        try {

            const status = await chatAPI.getConnectionStatus();
            
            if (status.connected) {
                this.updateConnectionStatus('connected');
            } else {
                this.updateConnectionStatus('error');
            }
        } catch (error) {
            console.error('Connection check failed:', error);
            this.updateConnectionStatus('error');
        }
    }

    /**
     * Load chat history from API
     */
    async loadChatHistory() {
        try {
            const response = await chatAPI.getChatHistory();
            
            if (response.success && response.history.length > 0) {
                this.hideWelcomeMessage();
                
                // Clear existing messages
                this.clearChatDisplay();
                this.messages = [];
                
                // Add messages from history
                response.history.forEach(item => {
                    if (item.user_message) {
                        this.addMessage('user', item.user_message);
                    }
                    if (item.bot_response) {
                        this.addMessage('assistant', item.bot_response);
                    }
                });
                
                this.saveMessagesToStorage();
                Utils.showToast(`Đã tải ${response.count} tin nhắn từ lịch sử`, 'info');
            }
        } catch (error) {
            console.error('Load chat history error:', error);
        }
    }

    /**
     * Save messages to local storage
     */
    saveMessagesToStorage() {
        Utils.storage.set('chat_messages', this.messages);
    }

    /**
     * Load messages from local storage
     */
    loadStoredMessages() {
        try {
            const stored = Utils.storage.get('chat_messages', []);
            if (stored.length > 0) {
                // Validate and filter messages
                const validMessages = stored.filter(message => {
                    return message && 
                           typeof message === 'object' && 
                           message.type && 
                           message.content !== undefined &&
                           message.timestamp;
                });
                
                if (validMessages.length > 0) {
                    this.messages = validMessages;
                    this.hideWelcomeMessage();
                    
                    validMessages.forEach(message => {
                        try {
                            this.renderMessage(message);
                        } catch (error) {
                            console.warn('❌ Error rendering stored message:', error, message);
                        }
                    });
                    
                    // Update storage with valid messages only
                    if (validMessages.length !== stored.length) {
                        this.saveMessagesToStorage();
                    }
                }
            }
        } catch (error) {
            console.error('❌ Error loading stored messages:', error);
            // Clear corrupted data
            Utils.storage.remove('chat_messages');
        }
    }

    /**
     * Export chat history
     */
    async exportChat() {
        try {
            const response = await chatAPI.exportHistory();
            
            if (response.success) {
                const exportData = {
                    exported_at: new Date().toISOString(),
                    chat_history: response.history,
                    message_count: response.count
                };
                
                const jsonString = JSON.stringify(exportData, null, 2);
                const filename = `chat_history_${new Date().toISOString().split('T')[0]}.json`;
                
                Utils.downloadTextAsFile(jsonString, filename, 'application/json');
                Utils.showToast('Đã xuất lịch sử chat thành công', 'success');
            } else {
                Utils.showToast(`Không thể xuất lịch sử: ${response.error}`, 'error');
            }
        } catch (error) {
            console.error('Export chat error:', error);
            Utils.showToast('Không thể xuất lịch sử chat', 'error');
        }
    }

    /**
     * Copy message content
     * @param {string} messageId - Message ID
     */
    async copyMessage(messageId) {
        const message = this.messages.find(m => m.id === messageId);
        if (message) {
            const success = await Utils.copyToClipboard(message.content);
            if (success) {
                Utils.showToast('Đã sao chép tin nhắn', 'success', 2000);
            } else {
                Utils.showToast('Không thể sao chép tin nhắn', 'error');
            }
        }
    }

    /**
     * Regenerate last response
     */
    async regenerateResponse() {
        const lastUserMessage = [...this.messages].reverse().find(m => m.type === 'user');
        if (lastUserMessage) {
            // Remove last assistant message if exists
            const lastMessage = this.messages[this.messages.length - 1];
            if (lastMessage.type === 'assistant') {
                this.messages.pop();
                const messageEl = this.chatMessages.querySelector(`[data-message-id="${lastMessage.id}"]`);
                messageEl?.remove();
            }
            
            // Regenerate response
            this.showTypingIndicator();
            
            try {
                const response = await chatAPI.sendMessage(lastUserMessage.content);
                
                if (response.success) {
                    this.addMessage('assistant', response.message, {
                        processingTime: response.processingTime
                    });
                    this.saveMessagesToStorage();
                } else {
                    this.addMessage('assistant', `Kết nối mạng không ổn định, vui lòng kiểm tra lại!}`, {
                        isError: true
                    });
                }
            } catch (error) {
                console.error('Regenerate response error:', error);
                this.addMessage('assistant', 'Không thể tạo phản hồi mới', { isError: true });
            } finally {
                this.hideTypingIndicator();
            }
        }
    }

    /**
     * Set auto scroll behavior
     * @param {boolean} enabled - Enable auto scroll
     */
    setAutoScroll(enabled) {
        this.autoScrollEnabled = enabled;
    }

    /**
     * Get chat statistics
     * @returns {Object} Chat statistics
     */
    getStats() {
        const userMessages = this.messages.filter(m => m.type === 'user').length;
        const assistantMessages = this.messages.filter(m => m.type === 'assistant').length;
        
        return {
            totalMessages: this.messages.length,
            userMessages,
            assistantMessages,
            firstMessage: this.messages[0]?.timestamp,
            lastMessage: this.messages[this.messages.length - 1]?.timestamp
        };
    }

    /**
     * Destroy chat component
     */
    destroy() {
        // Remove event listeners and clean up
        this.messageInput?.removeEventListener('keydown', this.handleInputKeydown);
        this.messageInput?.removeEventListener('input', this.handleInputChange);
        this.sendBtn?.removeEventListener('click', this.handleSendMessage);
        
        console.log('Chat component destroyed');
    }
}

// Export for global use
window.ChatComponent = ChatComponent; 