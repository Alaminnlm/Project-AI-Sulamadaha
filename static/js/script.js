// Get elements
const messageInput = document.getElementById('messageInput');
const messagesContainer = document.getElementById('messagesContainer');
const loadingIndicator = document.getElementById('loadingIndicator');

// Session ID will be initialized after fetching latest session
let sessionId = null;

// Handle keypress on input
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Send message function
async function sendMessage(message = null) {
    const text = message || messageInput.value.trim();

    if (!text) return;

    // Clear input
    messageInput.value = '';
    messageInput.focus();

    // Remove welcome message if it exists
    const welcomeMessage = messagesContainer.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    // Add user message to UI
    addMessage(text, 'user');

    // Show loading indicator
    showLoading(true);

    try {
        // Send to server
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: text,
                session_id: sessionId
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Add bot response
            addMessage(data.response, 'assistant');
            // Refresh sidebar history
            await loadChatHistory();
        } else {
            addMessage('❌ ' + (data.error || 'Terjadi kesalahan saat memproses pesan'), 'assistant');
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('❌ Gagal terhubung ke server. Pastikan Flask sedang berjalan.', 'assistant');
    } finally {
        showLoading(false);
    }
}

// Add message to chat
function addMessage(text, role, messageData = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="message-icon">
                <i class="fas fa-user"></i>
            </div>
            <div class="message-body">
                <div class="message-content">${escapeHtml(text)}</div>
                <div class="message-actions">
                    <button class="message-edit-btn" title="Edit pesan" onclick="editMessage(this)">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="message-delete-btn" title="Hapus pesan" onclick="deleteMessage(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    } else {
        // Format response text (convert newlines to breaks, basic markdown)
        const formattedText = formatResponse(text);
        
        // Buat ID unik untuk pesan ini agar bisa dicopy
        const messageId = 'msg-' + Date.now() + Math.random().toString(36).substr(2, 5);
        
        messageDiv.innerHTML = `
            <div class="message-icon">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-body">
                <div class="message-content" id="${messageId}">${formattedText}</div>
                <div class="message-actions">
                    <button class="copy-btn" title="Salin teks" onclick="copyToClipboard('${messageId}', this)">
                        <i class="far fa-copy"></i>
                        <span>Copy response</span>
                    </button>
                </div>
            </div>
        `;
    }

    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 100);
}

// Format response text manually without external libraries
function formatResponse(text) {
    if (!text) return '';
    
    // First, escape HTML to prevent XSS but keep it ready for our formatting
    let formatted = escapeHtml(text);
    
    // 1. Format Code Blocks: ```language\ncode\n```
    formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, function(match, lang, code) {
        return `<pre style="background:#0f172a; padding:10px; border-radius:8px; overflow-x:auto; margin:10px 0; border:1px solid rgba(255,255,255,0.1);"><code>${code}</code></pre>`;
    });
    
    // 2. Format Inline Code: `code`
    formatted = formatted.replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.1); padding:2px 5px; border-radius:4px; font-family:monospace;">$1</code>');
    
    // 3. Format Headers: ### Header
    formatted = formatted.replace(/^### (.*$)/gim, '<h3 style="margin-top:15px; margin-bottom:10px; color:var(--accent-color); font-size:1.1rem;">$1</h3>');
    formatted = formatted.replace(/^## (.*$)/gim, '<h2 style="margin-top:18px; margin-bottom:10px; color:var(--accent-color); font-size:1.25rem;">$1</h2>');
    formatted = formatted.replace(/^# (.*$)/gim, '<h1 style="margin-top:20px; margin-bottom:12px; color:var(--accent-color); font-size:1.5rem;">$1</h1>');
    
    // 4. Format Bold: **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // 5. Format Italic: *text*
    formatted = formatted.replace(/\*([^\*]+)\*/g, '<em>$1</em>');
    
    // 6. Format Numbered Lists: 1. Item
    formatted = formatted.replace(/^\d+\.\s+(.*)$/gim, '<div style="margin-left:5px; margin-bottom:5px;">✓ $1</div>');
    
    // 7. Format Bullet Lists: * Item or - Item
    formatted = formatted.replace(/^[\*-]\s+(.*)$/gim, '<div style="margin-left:15px; margin-bottom:5px; position:relative;"><span style="position:absolute; left:-12px; top:0; color:var(--accent-color);">•</span>$1</div>');
    
    // 8. Convert remaining newlines to <br> for regular paragraphs
    // Only convert newlines that aren't inside our block elements
    formatted = formatted.replace(/\n\n/g, '<br><br>');
    formatted = formatted.replace(/([^\>])\n([^\<])/g, '$1<br>$2');

    return formatted;
}

// Function to copy text to clipboard
function copyToClipboard(elementId, btnElement) {
    const textElement = document.getElementById(elementId);
    if (!textElement) return;
    
    // Retrieve pure text without HTML tags for copying
    const textToCopy = textElement.innerText;
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        // Visual feedback
        const icon = btnElement.querySelector('i');
        const span = btnElement.querySelector('span');
        const originalClass = icon.className;
        const originalText = span ? span.textContent : '';
        
        icon.className = 'fas fa-check';
        if (span) span.textContent = 'Copied!';
        btnElement.style.color = '#10b981'; // Success green
        
        setTimeout(() => {
            icon.className = originalClass;
            if (span) span.textContent = originalText;
            btnElement.style.color = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show/hide loading indicator
function showLoading(show) {
    loadingIndicator.style.display = show ? 'flex' : 'none';

    if (show) {
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }
}

// Clear ALL conversation history
async function clearHistory() {
    if (confirm('Apakah Anda yakin ingin menghapus SEMUA riwayat percakapan? Tindakan ini tidak dapat dibatalkan!')) {
        try {
            const response = await fetch('/api/clear-history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });

            if (response.ok) {
                // Create new session after clearing
                sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

                // Clear messages
                messagesContainer.innerHTML = `
                <div class="message assistant">
                    <div class="message-icon">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-body">
                        <div class="message-content">
                            Halo! 👋 Saya adalah AI asisten wisata Pantai Sulamadaha.
                            <br><br>
                            Apa yang ingin Anda rencanakan hari ini?
                            
                            <div class="suggestion-chips">
                                <button class="chip" onclick="sendMessage('Apa daya tarik utama Pantai Sulamadaha?')">
                                    <i class="fas fa-star"></i> Daya Tarik Utama
                                </button>
                                <button class="chip" onclick="sendMessage('Bagaimana cara menuju ke sana dari pelabuhan?')">
                                    <i class="fas fa-map-marked-alt"></i> Rute & Lokasi
                                </button>
                                <button class="chip" onclick="sendMessage('Apa aktivitas menarik yang bisa dilakukan di sana?')">
                                    <i class="fas fa-swimmer"></i> Aktivitas Menarik
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                `;
                // Reload history list and wait
                await loadChatHistory();
                alert('Semua riwayat percakapan telah dihapus.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Gagal menghapus riwayat.');
        }
    }
}

// Delete specific history item
async function deleteHistoryItem(sessionIdToDelete) {
    if (confirm('Apakah Anda yakin ingin menghapus history ini?')) {
        try {
            const response = await fetch('/api/delete-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionIdToDelete
                })
            });

            if (response.ok) {
                // Reload all history list and wait
                await loadChatHistory();

                // If deleted session is current session, start new chat
                if (sessionIdToDelete === sessionId) {
                    startNewChat();
                }
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Gagal menghapus history.');
        }
    }
}

// Edit user message
function editMessage(button) {
    const messageDiv = button.closest('.message');
    const contentDiv = messageDiv.querySelector('.message-content');
    const currentText = contentDiv.textContent;
    const actionsDiv = messageDiv.querySelector('.message-actions');

    // Replace content with editable input
    const editContainer = document.createElement('div');
    editContainer.className = 'message-edit-container';
    editContainer.innerHTML = `
        <textarea class="message-edit-input" rows="3">${escapeHtml(currentText)}</textarea>
        <div class="message-edit-actions">
            <button class="message-save-btn" title="Simpan">Simpan</button>
            <button class="message-cancel-btn" title="Batal">Batal</button>
        </div>
    `;

    // Replace content and hide actions
    contentDiv.replaceWith(editContainer);
    actionsDiv.style.display = 'none';

    // Focus on textarea
    const textarea = editContainer.querySelector('.message-edit-input');
    textarea.focus();

    // Save button handler
    const saveBtn = editContainer.querySelector('.message-save-btn');
    saveBtn.onclick = async function () {
        const newText = textarea.value.trim();

        if (newText && newText !== currentText) {
            // Disable buttons during processing
            saveBtn.disabled = true;
            editContainer.querySelector('.message-cancel-btn').disabled = true;

            // Replace textarea with new content
            const newContentDiv = document.createElement('div');
            newContentDiv.className = 'message-content';
            newContentDiv.textContent = newText;
            editContainer.replaceWith(newContentDiv);
            actionsDiv.style.display = '';

            // Find and remove old bot response
            let nextMessage = messageDiv.nextElementSibling;
            if (nextMessage && nextMessage.classList.contains('assistant')) {
                nextMessage.remove();
            }

            // Show loading indicator
            showLoading(true);

            try {
                // Send edited message to get new response
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: newText,
                        session_id: sessionId
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    // Add bot response right after the edited message
                    const botResponseDiv = document.createElement('div');
                    botResponseDiv.className = 'message assistant';
                    const formattedText = formatResponse(data.response);
                    botResponseDiv.innerHTML = `
                        <div class="message-icon">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="message-body">
                            <div class="message-content">${formattedText}</div>
                        </div>
                    `;
                    messageDiv.parentNode.insertBefore(botResponseDiv, messageDiv.nextSibling);

                    // Refresh sidebar history
                    await loadChatHistory();
                } else {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'message assistant';
                    errorDiv.innerHTML = `
                        <div class="message-icon">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="message-body">
                            <div class="message-content">❌ ${data.error || 'Terjadi kesalahan saat memproses pesan'}</div>
                        </div>
                    `;
                    messageDiv.parentNode.insertBefore(errorDiv, messageDiv.nextSibling);
                }
            } catch (error) {
                console.error('Error:', error);
                const errorDiv = document.createElement('div');
                errorDiv.className = 'message assistant';
                errorDiv.innerHTML = `
                    <div class="message-icon">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-body">
                        <div class="message-content">❌ Gagal terhubung ke server. Pastikan Flask sedang berjalan.</div>
                    </div>
                `;
                messageDiv.parentNode.insertBefore(errorDiv, messageDiv.nextSibling);
            } finally {
                showLoading(false);
            }
        } else {
            // Cancel if no change
            cancelEdit();
        }
    };

    // Cancel button handler
    const cancelBtn = editContainer.querySelector('.message-cancel-btn');
    cancelBtn.onclick = cancelEdit;

    function cancelEdit() {
        // Restore original content and actions
        editContainer.replaceWith(contentDiv);
        actionsDiv.style.display = '';
    }
}

// Delete user message
function deleteMessage(button) {
    if (confirm('Hapus pesan ini?')) {
        const messageDiv = button.closest('.message');
        const nextMessage = messageDiv.nextElementSibling;

        // If next message is bot response, delete it too
        if (nextMessage && nextMessage.classList.contains('assistant')) {
            nextMessage.remove();
        }

        messageDiv.remove();
    }
}

// Start new chat conversation
async function startNewChat() {
    // Create new session ID
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    // Clear messages container
    messagesContainer.innerHTML = `
        <div class="message assistant">
            <div class="message-icon">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-body">
                <div class="message-content">
                    Halo! 👋 Saya adalah AI asisten wisata Pantai Sulamadaha.
                    <br><br>
                    Apa yang ingin Anda rencanakan hari ini?
                    
                    <div class="suggestion-chips">
                        <button class="chip" onclick="sendMessage('Apa daya tarik utama Pantai Sulamadaha?')">
                            <i class="fas fa-star"></i> Daya Tarik Utama
                        </button>
                        <button class="chip" onclick="sendMessage('Bagaimana cara menuju ke sana dari pusat kota?')">
                            <i class="fas fa-map-marked-alt"></i> Rute & Lokasi
                        </button>
                        <button class="chip" onclick="sendMessage('Apa aktivitas menarik yang bisa dilakukan di sana?')">
                            <i class="fas fa-swimmer"></i> Aktivitas Menarik
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Clear input
    messageInput.value = '';
    messageInput.focus();

    // Update sidebar history
    await loadChatHistory();
}

// Get or create session ID (fetch from server to get latest session)
async function getOrCreateSessionId() {
    try {
        const response = await fetch('/api/latest-session');
        const data = await response.json();

        if (data.session_id) {
            // Use existing latest session
            return data.session_id;
        } else {
            // Create new session (no previous sessions)
            const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            return newSessionId;
        }
    } catch (error) {
        console.error('Error getting session:', error);
        // Fallback: create new session
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

// Load and display a history item (show full previous conversation)
function loadAndDisplayHistoryItem(message) {
    // Remove welcome message if exists
    const welcomeMessage = messagesContainer.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    // Find the index of the clicked user message in full history
    const historyList = document.getElementById('historyList');
    const currentMessages = historyList.querySelectorAll('.history-item');
    let messageIndex = -1;

    for (let i = 0; i < currentMessages.length; i++) {
        if (currentMessages[i].textContent.includes(message.substring(0, 30))) {
            messageIndex = i;
            break;
        }
    }

    // Fetch full history and display from that point onwards
    fetch(`/api/history?session_id=${sessionId}`)
        .then(res => res.json())
        .then(data => {
            const history = data.history;

            // Find user message index in full history
            let startIndex = -1;
            for (let i = 0; i < history.length; i++) {
                if (history[i].role === 'user' && history[i].content === message) {
                    startIndex = i;
                    break;
                }
            }

            // Clear current messages
            messagesContainer.innerHTML = '';

            // Display from that message onwards (user + bot response)
            if (startIndex !== -1) {
                // Show user message
                addMessage(history[startIndex].content, 'user');

                // Show bot response if exists (next message should be assistant)
                if (startIndex + 1 < history.length && history[startIndex + 1].role === 'assistant') {
                    addMessage(history[startIndex + 1].content, 'assistant');
                }

                // Show rest of conversation
                for (let i = startIndex + 2; i < history.length; i++) {
                    addMessage(history[i].content, history[i].role);
                }
            }

            // Scroll to top
            setTimeout(() => {
                messagesContainer.scrollTop = 0;
            }, 100);
        })
        .catch(error => console.error('Error loading history:', error));
}

// Load all chat sessions in sidebar
async function loadChatHistory() {
    try {
        // Fetch all sessions for this user
        const sessionsResponse = await fetch('/api/sessions');
        const sessionsData = await sessionsResponse.json();
        const historyList = document.getElementById('historyList');

        if (!historyList) return;

        if (!sessionsData.sessions || sessionsData.sessions.length === 0) {
            historyList.innerHTML = '<div class="history-empty">Belum ada riwayat chat</div>';
            return;
        }

        historyList.innerHTML = '';

        // For each session, fetch history and display
        for (const sid of sessionsData.sessions) {
            try {
                const historyResponse = await fetch(`/api/history?session_id=${sid}`);
                const historyData = await historyResponse.json();

                if (historyData.history && historyData.history.length > 0) {
                    // Get first message
                    const firstMessage = historyData.history[0];

                    // Create history item
                    const historyItem = document.createElement('div');
                    historyItem.className = 'history-item' + (sid === sessionId ? ' active' : '');

                    // Content wrapper
                    const contentWrapper = document.createElement('div');
                    contentWrapper.className = 'history-item-content';
                    contentWrapper.textContent = firstMessage.content.substring(0, 50) + (firstMessage.content.length > 50 ? '...' : '');
                    contentWrapper.title = `${historyData.history.length} messages`;
                    contentWrapper.onclick = () => loadSessionConversation(sid);

                    // Delete button
                    const deleteBtn = document.createElement('button');
                    deleteBtn.className = 'history-item-delete';
                    deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
                    deleteBtn.title = 'Hapus history ini';
                    deleteBtn.onclick = (e) => {
                        e.stopPropagation();
                        deleteHistoryItem(sid);
                    };

                    historyItem.appendChild(contentWrapper);
                    historyItem.appendChild(deleteBtn);
                    historyList.appendChild(historyItem);
                }
            } catch (error) {
                console.error(`Error loading session ${sid}:`, error);
            }
        }
    } catch (error) {
        console.error('Error loading sessions:', error);
    }
}

// Load specific session conversation
async function loadSessionConversation(selectedSessionId) {
    try {
        const response = await fetch(`/api/history?session_id=${selectedSessionId}`);
        const data = await response.json();

        // Clear welcome message
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        // Display all messages from this session
        if (data.history && data.history.length > 0) {
            messagesContainer.innerHTML = '';
            data.history.forEach(msg => {
                addMessage(msg.content, msg.role);
            });
        }

        // Update sessionId to this session
        sessionId = selectedSessionId;

        // Scroll to top
        setTimeout(() => {
            messagesContainer.scrollTop = 0;
        }, 100);
    } catch (error) {
        console.error('Error loading conversation:', error);
    }
}

// Focus on input when page loads and initialize session
window.addEventListener('load', async () => {
    // Create NEW session on page load (fresh start)
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    // Display welcome message (same as index.html)
    messagesContainer.innerHTML = `
        <div class="message assistant">
            <div class="message-icon">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                Halo! 👋 Saya adalah AI asisten khusus untuk wisata Pantai Sulamadaha di Ternate..
                <br><br>
                Apa yang ingin Anda rencanakan hari ini?
                
                <div class="suggestion-chips">
                    <button class="chip" onclick="sendMessage('Apa daya tarik utama Pantai Sulamadaha?')">
                        <i class="fas fa-star"></i> Daya Tarik Utama
                    </button>
                    <button class="chip" onclick="sendMessage('Bagaimana cara menuju ke sana dari pusat kota?')">
                        <i class="fas fa-map-marked-alt"></i> Rute & Lokasi
                    </button>
                    <button class="chip" onclick="sendMessage('Apa aktivitas menarik yang bisa dilakukan di sana?')">
                        <i class="fas fa-swimmer"></i> Aktivitas Menarik
                    </button>
                </div>
            </div>
        </div>
    `;

    // Load all history in sidebar (for user to choose old sessions)
    await loadChatHistory();

    messageInput.focus();
});

// Load chat history and display all messages in current session
async function loadChatHistoryAndDisplay() {
    try {
        if (!sessionId) return;

        const response = await fetch(`/api/history?session_id=${sessionId}`);
        const data = await response.json();

        // Clear welcome message
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        // Display all messages in current session
        if (data.history && data.history.length > 0) {
            messagesContainer.innerHTML = '';
            data.history.forEach(msg => {
                addMessage(msg.content, msg.role);
            });
        }

        // Also load history list in sidebar
        loadChatHistory();
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

// Auto-grow textarea height if needed (optional enhancement)
messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 100) + 'px';
});
