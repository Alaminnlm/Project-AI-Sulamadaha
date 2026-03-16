// Transient history array for this session only
        let transientHistory = [];

        const chatMessages = document.getElementById('chatMessages');
        const userInput = document.getElementById('userInput');
        const chatForm = document.getElementById('chatForm');
        const sendBtn = document.getElementById('sendBtn');
        const typingIndicator = document.getElementById('typingIndicator');

        function sendPrompt(text) {
            userInput.value = text;
            userInput.focus();
            // Automatically submit
            document.getElementById('sendBtn').click();
        }

        function scrollToBottom() {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // Format raw text to simple HTML (bolding, line breaks)
        function formatText(text) {
            // Escape HTML
            const div = document.createElement('div');
            div.textContent = text;
            let formatted = div.innerHTML;

            // Simple markdown parsing
            formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            formatted = formatted.replace(/\n/g, '<br>');
            formatted = formatted.replace(/^\d+\.\s/gm, '<br>✓ ');

            return formatted;
        }

        function addMessage(text, isUser = false) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${isUser ? 'user' : 'bot'}`;

            const avatarHtml = isUser
                ? `<div class="msg-avatar"><i class="fas fa-user"></i></div>`
                : `<div class="msg-avatar"><i class="fas fa-robot"></i></div>`;

            const formattedText = isUser ? text : formatText(text);
            const msgId = 'msg-' + Date.now() + Math.random().toString(36).substr(2, 5);

            let bodyHtml = '';
            if (isUser) {
                bodyHtml = `
                    <div class="msg-body">
                        <div class="msg-bubble">${formattedText}</div>
                    </div>
                `;
            } else {
                bodyHtml = `
                    <div class="msg-body">
                        <div class="msg-bubble" id="${msgId}">${formattedText}</div>
                        <div class="msg-actions">
                            <button class="copy-btn" title="Salin teks" onclick="copyToClipboard('${msgId}', this)">
                                <i class="far fa-copy"></i>
                                <span>Copy response</span>
                            </button>
                        </div>
                    </div>
                `;
            }

            msgDiv.innerHTML = `
                ${avatarHtml}
                ${bodyHtml}
            `;

            chatMessages.appendChild(msgDiv);
            scrollToBottom();
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

        async function handleSubmit(e) {
            e.preventDefault();
            const text = userInput.value.trim();
            if (!text) return;

            // UI Update: User message
            userInput.value = '';
            userInput.disabled = true;
            sendBtn.disabled = true;
            addMessage(text, true);

            // Add to transient history
            transientHistory.push({
                role: "user",
                parts: [{ "text": text }]
            });

            // Show typing indicator
            typingIndicator.classList.add('active');
            chatMessages.appendChild(typingIndicator); // move to bottom
            scrollToBottom();

            try {
                // Send to generalized /api/chat endpoint which now accepts transient_history
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: text,
                        transient_history: transientHistory.slice(0, -1) // send everything except last msg
                    })
                });

                const data = await response.json();

                // Hide typing
                typingIndicator.classList.remove('active');

                if (response.ok) {
                    addMessage(data.response, false);
                    transientHistory.push({
                        role: "model",
                        parts: [{ "text": data.response }]
                    });
                } else {
                    addMessage("❌ " + (data.error || "Maaf, terjadi kesalahan saat menghubungi server."), false);
                }
            } catch (err) {
                console.error(err);
                typingIndicator.classList.remove('active');
                addMessage("❌ Gagal terhubung ke server.", false);
            } finally {
                userInput.disabled = false;
                sendBtn.disabled = false;
                userInput.focus();
            }
        }