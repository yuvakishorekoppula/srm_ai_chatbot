document.addEventListener('DOMContentLoaded', () => {
    const chatWrapper = document.getElementById('chat-wrapper');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const themeToggle = document.getElementById('theme-toggle');
    const newChatBtn = document.getElementById('new-chat-btn');
    const historyList = document.getElementById('chat-history-list');
    const typingIndicator = document.getElementById('typing-indicator');
    const suggestionBtns = document.querySelectorAll('.suggestion-btn');

    let currentConversationId = null;

    // --- Core Functions ---

    function formatResponse(text) {
        if (!text) return "";

        // 1. Sanitize/Clean bold markers (convert markdown bold to HTML)
        let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // 2. Handle Markdown Links [text](url) first to prevent double-wrapping
        const mdLinkRegex = /\[(.*?)\]\((https?:\/\/.*?)\)/g;
        formatted = formatted.replace(mdLinkRegex, (match, linkText, url) => {
            return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="chat-link"><i class="fas fa-external-link-alt"></i> ${linkText}</a>`;
        });

        // 3. Convert remaining raw URLs to Clickable Links
        const urlRegex = /(?<!href="|">)(https?:\/\/[^\s<]+)/g;
        formatted = formatted.replace(urlRegex, (url) => {
            const cleanUrl = url.replace(/[.,;]$/, '');
            return `<a href="${cleanUrl}" target="_blank" rel="noopener noreferrer" class="chat-link"><i class="fas fa-external-link-alt"></i> ${cleanUrl}</a>`;
        });

        // 4. Handle Line Breaks and Spacing (Split by double newline for paragraphs)
        formatted = formatted.split('\n\n').map(para => {
            if (para.trim()) {
                return `<p style="margin-bottom: 12px;">${para.trim().replace(/\n/g, '<br>')}</p>`;
            }
            return '';
        }).join('');

        // 5. Bold Keywords for better visibility (if not already bolded)
        const keywords = ['Admissions', 'Departments', 'Facilities', 'SRM', 'Attendance', 'Rules', 'Timetable', 'Hostel'];
        keywords.forEach(word => {
            const reg = new RegExp(`\\b(${word})\\b`, 'gi');
            // Check if word is already inside a tag
            formatted = formatted.replace(reg, (match) => `<strong>${match}</strong>`);
        });

        return formatted;
    }

    function appendMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message animate-fade-in`;
        
        const avatar = document.createElement('div');
        avatar.className = `avatar ${role}-avatar`;
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (role === 'bot') {
            contentDiv.innerHTML = formatResponse(content);
        } else {
            contentDiv.textContent = content;
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        chatWrapper.appendChild(messageDiv);
        
        // Scroll to bottom smoothly
        const chatContainer = document.getElementById('chat-container');
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: 'smooth'
        });
    }

    async function loadConversations() {
        try {
            const response = await fetch('/conversations');
            const data = await response.json();
            
            historyList.innerHTML = '';
            data.forEach(conv => {
                const item = document.createElement('div');
                item.className = 'history-item';
                item.textContent = conv.title;
                item.onclick = () => loadMessages(conv.id);
                historyList.appendChild(item);
            });
        } catch (error) {
            console.error('Error loading history:', error);
        }
    }

    async function loadMessages(convId) {
        currentConversationId = convId;
        chatWrapper.innerHTML = ''; // Clear current view
        
        try {
            const response = await fetch(`/conversation/${convId}`);
            const data = await response.json();
            
            data.forEach(msg => {
                appendMessage(msg.role, msg.content);
            });
        } catch (error) {
            console.error('Error loading messages:', error);
        }
    }

    async function handleSendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Display user message immediately
        appendMessage('user', message);
        userInput.value = '';

        // Show typing indicator
        typingIndicator.style.display = 'block';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message,
                    conversation_id: currentConversationId 
                })
            });

            const data = await response.json();
            
            if (data.error) {
                alert("Session expired. Please login again.");
                window.location.href = '/login';
                return;
            }

            typingIndicator.style.display = 'none';
            appendMessage('bot', data.response);

            // If it was a new conversation, update history and set ID
            if (!currentConversationId) {
                currentConversationId = data.conversation_id;
                loadConversations();
            }

        } catch (error) {
            console.error('Error:', error);
            typingIndicator.style.display = 'none';
            appendMessage('bot', "Sorry, I'm having trouble connecting to SRM servers.");
        }
    }

    // --- Event Listeners ---

    sendBtn.addEventListener('click', handleSendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSendMessage();
    });

    newChatBtn.addEventListener('click', () => {
        currentConversationId = null;
        chatWrapper.innerHTML = `
            <div class="message bot-message">
                <div class="avatar bot-avatar">SRM</div>
                <div class="message-content">
                    New session started. How can I assist you, SRM student?
                </div>
            </div>
        `;
    });

    themeToggle.addEventListener('click', () => {
        const body = document.body;
        const icon = themeToggle.querySelector('i');
        
        if (body.hasAttribute('data-theme')) {
            body.removeAttribute('data-theme');
            icon.className = 'fas fa-moon';
        } else {
            body.setAttribute('data-theme', 'dark');
            icon.className = 'fas fa-sun';
        }
    });

    suggestionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            userInput.value = btn.textContent;
            handleSendMessage();
        });
    });

    // Initial Load
    loadConversations();
});
