function chatApp() {
    return {
        loading: true,
        showUploadModal: false,
        messages: [],
        currentQuery: '',
        isTyping: false,
        documentStatus: { document_count: 0, has_documents: false },
        suggestions: [
            'Summarize the key points from my documents',
            'What are the main themes discussed?',
            'Find information about'
        ],
        
        async init() {
            // Check document status
            try {
                const response = await fetch('/status');
                const status = await response.json();
                this.documentStatus = status.documents;
            } catch (error) {
                console.warn('Could not fetch status:', error);
            }
            
            // Simulate loading time
            setTimeout(() => {
                this.loading = false;
            }, 1500);
            
            // Set up file input reference
            this.$nextTick(() => {
                const fileInput = document.getElementById('fileInput');
                this.$refs.fileInput = fileInput;
            });
        },
        
        async uploadFile(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    this.showUploadModal = false;
                    this.documentStatus.has_documents = true;
                    this.documentStatus.document_count += result.chunks_count || 1;
                    this.showNotification('File uploaded and processed successfully!', 'success');
                } else {
                    this.showNotification(result.error || 'Upload failed', 'error');
                }
            } catch (error) {
                this.showNotification('Upload failed: ' + error.message, 'error');
            }
            
            // Reset file input
            event.target.value = '';
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
                                        console.log('Updated message content:', assistantMessage.content);
                                        
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
                content
            };
            this.messages.push(message);
            this.$nextTick(() => this.scrollToBottom());
            return message;
        },
        
        scrollToBottom() {
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        },
        
        showNotification(message, type = 'info') {
            // Simple notification - could be enhanced with a toast library
            const color = type === 'error' ? 'red' : type === 'success' ? 'green' : 'blue';
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 bg-${color}-500 text-white px-4 py-2 rounded-lg shadow-lg z-50`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }
    }
}