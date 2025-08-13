function chatApp() {
    return {
        loading: true,
        messages: [],
        currentQuery: '',
        isTyping: false,
        suggestions: [
            'What paperwork do I need before releasing my music?',
            'How do I set up the essential accounts for music distribution?',
            'What are ISRC codes and why do I need them?',
            'How can I build my artist profile on streaming platforms?'
        ],
        
        init() {
            // Simulate loading time with logo animation
            setTimeout(() => {
                this.loading = false;
            }, 2000);
        },
        
        selectSuggestion(suggestion) {
            this.currentQuery = suggestion;
            // Focus on input after selection
            this.$nextTick(() => {
                const input = document.querySelector('input[type="text"]');
                if (input) input.focus();
            });
        },
        
        async sendMessage() {
            if (!this.currentQuery.trim() || this.isTyping) return;
            
            const query = this.currentQuery.trim();
            this.currentQuery = '';
            
            // Add user message
            this.addMessage('user', query);
            
            // Start typing indicator
            this.isTyping = true;
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query })
                });
                
                if (!response.ok) {
                    throw new Error('Chat request failed');
                }
                
                // Handle streaming response
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let assistantMessage = this.addMessage('assistant', '');
                let buffer = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    
                    // Keep the last incomplete line in buffer
                    buffer = lines.pop() || '';
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const jsonStr = line.substring(6).trim();
                                if (jsonStr) {
                                    const data = JSON.parse(jsonStr);
                                    console.log('Received data:', data);
                                    
                                    if (data.response) {
                                        assistantMessage.content += data.response;
                                        this.updateMessageContent(assistantMessage, assistantMessage.content);
                                        
                                        // Force Alpine.js reactivity update
                                        const messageIndex = this.messages.findIndex(m => m.id === assistantMessage.id);
                                        if (messageIndex !== -1) {
                                            this.messages[messageIndex] = { ...assistantMessage };
                                        }
                                        
                                        this.$nextTick(() => this.scrollToBottom());
                                    }
                                    
                                    if (data.done) {
                                        console.log('Stream complete');
                                        this.isTyping = false;
                                        return;
                                    }
                                    
                                    if (data.error) {
                                        assistantMessage.content = 'Error: ' + data.error;
                                        this.isTyping = false;
                                        return;
                                    }
                                }
                            } catch (e) {
                                console.warn('JSON parse error:', e, 'Line:', line);
                            }
                        }
                    }
                }
                
                // Process any remaining buffer
                if (buffer.startsWith('data: ')) {
                    try {
                        const jsonStr = buffer.substring(6).trim();
                        if (jsonStr) {
                            const data = JSON.parse(jsonStr);
                            if (data.done) {
                                this.isTyping = false;
                            }
                        }
                    } catch (e) {
                        console.warn('Final buffer parse error:', e);
                    }
                }
                
                this.isTyping = false;
                
            } catch (error) {
                this.isTyping = false;
                this.addMessage('assistant', 'Sorry, there was an error processing your request.');
                this.showNotification('Error: ' + error.message, 'error');
                console.error('Chat error:', error);
            }
        },
        
        addMessage(type, content) {
            const message = {
                id: Date.now() + Math.random(),
                type,
                content,
                renderedContent: type === 'assistant' ? this.renderMarkdown(content) : content
            };
            this.messages.push(message);
            this.$nextTick(() => this.scrollToBottom());
            return message;
        },
        
        renderMarkdown(content) {
            if (!content || typeof content !== 'string') return '';
            
            try {
                // Configure marked for safe rendering
                marked.setOptions({
                    breaks: true,
                    gfm: true,
                    headerIds: false,
                    mangle: false
                });
                
                // Parse markdown
                const html = marked.parse(content);
                
                // Sanitize HTML to prevent XSS
                const cleanHtml = DOMPurify.sanitize(html, {
                    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote'],
                    ALLOWED_ATTR: []
                });
                
                return cleanHtml;
            } catch (error) {
                console.warn('Markdown rendering error:', error);
                return content; // Fallback to plain text
            }
        },
        
        updateMessageContent(message, newContent) {
            message.content = newContent;
            if (message.type === 'assistant') {
                message.renderedContent = this.renderMarkdown(newContent);
            }
        },
        
        autoResize() {
            const textarea = this.$refs.textarea;
            if (textarea) {
                textarea.style.height = 'auto';
                textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
            }
        },
        
        scrollToBottom() {
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        },
        
        showNotification(message, type = 'info') {
            // Simple notification with dark theme
            const colorClass = type === 'error' ? 'bg-red-600' : type === 'success' ? 'bg-green-600' : 'bg-gray-700';
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 ${colorClass} text-white px-4 py-2 rounded-lg shadow-lg z-50 border border-gray-600`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }
    }
}