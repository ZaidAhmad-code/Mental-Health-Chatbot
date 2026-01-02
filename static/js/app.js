/* ============================================
   MindSpace - Main JavaScript
   ============================================ */

// ==================== GLOBAL STATE ====================
let currentUser = null;
let currentChatSessionId = null;
let chatSessions = [];

// ==================== THEME MANAGEMENT ====================
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

// Initialize theme attribute immediately (before DOM loads for no flash)
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);

// ==================== AUTH MANAGEMENT ====================
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/profile');
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            console.log('User loaded:', currentUser); // Debug log
            console.log('Avatar config:', currentUser.avatar_config); // Debug log
            showAuthenticatedUI();
        } else {
            showGuestUI();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showGuestUI();
    }
}

function showGuestUI() {
    const authGuest = document.getElementById('auth-guest');
    const authUser = document.getElementById('auth-user');
    
    if (authGuest) authGuest.style.display = 'flex';
    if (authUser) authUser.style.display = 'none';
}

function showAuthenticatedUI() {
    const authGuest = document.getElementById('auth-guest');
    const authUser = document.getElementById('auth-user');
    
    if (authGuest) authGuest.style.display = 'none';
    if (authUser) authUser.style.display = 'block';
    
    // Update user info displays
    const displayName = currentUser?.display_name || currentUser?.username || 'User';
    const email = currentUser?.email || '';
    
    const nameDisplay = document.getElementById('user-name-display');
    const dropdownName = document.getElementById('dropdown-name');
    const dropdownEmail = document.getElementById('dropdown-email');
    
    if (nameDisplay) nameDisplay.textContent = displayName;
    if (dropdownName) dropdownName.textContent = displayName;
    if (dropdownEmail) dropdownEmail.textContent = email;
    
    // Update avatar in header if exists
    const headerAvatar = document.querySelector('.user-avatar-small');
    if (headerAvatar && currentUser?.avatar_config) {
        try {
            console.log('Updating header avatar with config:', currentUser.avatar_config); // Debug
            const config = JSON.parse(currentUser.avatar_config);
            headerAvatar.style.backgroundColor = config.color || '#2D5A3D';
            headerAvatar.textContent = config.emoji || '👤';
            console.log('Header avatar updated:', config); // Debug
        } catch (e) {
            console.log('Error parsing avatar config:', e); // Debug
            console.log('Using default header avatar');
        }
    } else {
        console.log('No header avatar element or config:', { 
            hasElement: !!headerAvatar, 
            hasConfig: !!currentUser?.avatar_config 
        }); // Debug
    }
}

async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        currentUser = null;
        showToast('Logged out successfully. Redirecting...', 'success');
        // Redirect to login page after a short delay
        setTimeout(() => {
            window.location.href = '/login';
        }, 1000);
    } catch (error) {
        showToast('Logout failed', 'error');
    }
}

// User Dropdown Toggle
function setupUserDropdown() {
    const profileBtn = document.getElementById('user-profile-btn');
    const dropdown = document.getElementById('user-dropdown');
    
    if (profileBtn && dropdown) {
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            profileBtn.classList.toggle('active');
            dropdown.classList.toggle('visible');
        });
        
        document.addEventListener('click', () => {
            profileBtn?.classList.remove('active');
            dropdown?.classList.remove('visible');
        });
    }
}

// ==================== CHAT MANAGEMENT ====================
async function loadChatSessions() {
    try {
        const response = await fetch('/api/chats');
        if (response.ok) {
            const data = await response.json();
            chatSessions = data.sessions || [];
            renderChatList();
            
            if (chatSessions.length > 0) {
                await loadChatSession(chatSessions[0].id);
            }
        }
    } catch (error) {
        console.error('Failed to load chat sessions:', error);
    }
}

function renderChatList() {
    const chatList = document.getElementById('chat-list');
    if (!chatList) return;
    
    if (chatSessions.length === 0) {
        chatList.innerHTML = `
            <div class="chat-list-empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <p>No conversations yet</p>
                <p style="font-size: 11px; margin-top: 4px;">Start chatting to begin</p>
            </div>`;
        return;
    }
    
    chatList.innerHTML = chatSessions.map(session => `
        <div class="chat-item ${session.id === currentChatSessionId ? 'active' : ''}" 
             onclick="loadChatSession(${session.id})">
            <div class="chat-item-content">
                <div class="chat-item-title">${escapeHtml(session.title || 'New Chat')}</div>
                <div class="chat-item-date">${formatRelativeTime(session.updated_at)}</div>
            </div>
            <button class="chat-item-delete" onclick="event.stopPropagation(); deleteChatSession(${session.id})">
                🗑️
            </button>
        </div>
    `).join('');
}

async function loadChatSession(sessionId) {
    console.log('Loading chat session:', sessionId);
    try {
        currentChatSessionId = sessionId;
        renderChatList();
        
        console.log('Fetching chat session from backend:', sessionId);
        
        // First load the session into memory on the backend
        await fetch(`/api/chats/${sessionId}/load`, { method: 'POST' });
        
        // Then get the session details and messages
        const response = await fetch(`/api/chats/${sessionId}`);
        console.log('Response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('Chat data received:', data);
            const session = data.session || chatSessions.find(s => s.id === sessionId);
            
            updateChatTitle(session?.title || 'Chat');
            renderMessages(data.messages || []);
        } else {
            console.error('Failed to load chat:', response.status);
            showToast('Failed to load chat', 'error');
        }
    } catch (error) {
        console.error('Failed to load chat session:', error);
        showToast('Error loading chat: ' + error.message, 'error');
    }
}

async function reloadCurrentChatMessages() {
    if (!currentChatSessionId) return;
    
    try {
        const response = await fetch(`/api/chats/${currentChatSessionId}`);
        if (response.ok) {
            const data = await response.json();
            // Only reload messages, don't change the title or UI state
            const messages = data.messages || [];
            if (messages.length > 0) {
                renderMessages(messages);
            }
        }
    } catch (error) {
        console.error('Failed to reload messages:', error);
    }
}

function renderMessages(messages) {
    const chatLog = document.getElementById('chat-log');
    if (!chatLog) return;
    
    if (messages.length === 0) {
        chatLog.innerHTML = `
            <div class="welcome-message">
                <h2 class="welcome-title">Welcome to Serene</h2>
                <p class="welcome-subtitle">Your AI-powered mental health companion. Share your thoughts in a safe, supportive space.</p>
                <div class="quick-actions">
                    <button class="quick-btn" onclick="quickQuery('I\\'m feeling anxious')">😰 Feeling Anxious</button>
                    <button class="quick-btn" onclick="quickQuery('I need coping strategies')">🧘 Coping Strategies</button>
                    <button class="quick-btn" onclick="quickQuery('How can I improve my mood?')">😊 Mood Help</button>
                </div>
            </div>`;
        return;
    }
    
    // Handle both formats: {message, response} from DB and {role, content} from streaming
    let html = '';
    messages.forEach(msg => {
        if (msg.message !== undefined && msg.response !== undefined) {
            // Database format: {message, response}
            html += `
                <div class="chat-message user-message">
                    <div class="message-wrapper">
                        <div class="avatar user-avatar">👤</div>
                        <div class="message-content">${escapeHtml(msg.message)}</div>
                    </div>
                </div>
                <div class="chat-message bot-message">
                    <div class="message-wrapper">
                        <div class="avatar bot-avatar"><img src="/static/images/serene.png" alt="Serene" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;"></div>
                        <div class="message-content">${formatBotResponse(msg.response)}</div>
                    </div>
                </div>
            `;
        } else {
            // Streaming format: {role, content}
            const isUser = msg.role === 'user';
            const avatarContent = isUser ? '👤' : '<img src="/static/images/serene.png" alt="Serene" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">';
            html += `
                <div class="chat-message ${isUser ? 'user-message' : 'bot-message'}">
                    <div class="message-wrapper">
                        <div class="avatar ${isUser ? 'user-avatar' : 'bot-avatar'}">${avatarContent}</div>
                        <div class="message-content">${isUser ? escapeHtml(msg.content) : formatBotResponse(msg.content)}</div>
                    </div>
                </div>
            `;
        }
    });
    
    chatLog.innerHTML = html;
    scrollToBottom();
}

async function createNewChat() {
    try {
        const response = await fetch('/api/chats', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'New Chat' })
        });
        
        if (response.ok) {
            const data = await response.json();
            currentChatSessionId = data.id;
            await loadChatSessions();
            
            const chatLog = document.getElementById('chat-log');
            if (chatLog) {
                chatLog.innerHTML = `
                    <div class="welcome-message">
                        <h2 class="welcome-title">Welcome to Serene</h2>
                        <p class="welcome-subtitle">Your AI-powered mental health companion. Share your thoughts in a safe, supportive space.</p>
                        <div class="quick-actions">
                            <button class="quick-btn" onclick="quickQuery('I\\'m feeling anxious')">😰 Feeling Anxious</button>
                            <button class="quick-btn" onclick="quickQuery('I need coping strategies')">🧘 Coping Strategies</button>
                            <button class="quick-btn" onclick="quickQuery('How can I improve my mood?')">😊 Mood Help</button>
                        </div>
                    </div>`;
            }
            updateChatTitle('New Chat');
        }
    } catch (error) {
        console.error('Failed to create chat:', error);
        showToast('Failed to create new chat', 'error');
    }
}

async function deleteChatSession(sessionId) {
    if (!confirm('Delete this conversation?')) return;
    
    try {
        const response = await fetch(`/api/chats/${sessionId}`, { method: 'DELETE' });
        if (response.ok) {
            await loadChatSessions();
            showToast('Chat deleted', 'success');
        }
    } catch (error) {
        showToast('Failed to delete chat', 'error');
    }
}

function updateChatTitle(title) {
    const titleEl = document.getElementById('current-chat-title');
    if (titleEl) titleEl.textContent = title;
}

function editChatTitle() {
    const newTitle = prompt('Enter new chat title:');
    if (newTitle && currentChatSessionId) {
        fetch(`/api/chats/${currentChatSessionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        }).then(() => {
            updateChatTitle(newTitle);
            loadChatSessions();
        });
    }
}

// ==================== MESSAGE SENDING ====================
function sendMessage() {
    const input = document.getElementById('user-input');
    const userQuery = input.value.trim();
    if (!userQuery) return;
    
    // Auto-create chat session if none exists
    if (!currentChatSessionId) {
        createNewChatAndSend(userQuery);
        return;
    }
    
    // Remove welcome message
    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    
    // Add user message to UI
    addMessageToUI(userQuery, true);
    
    // Clear input
    input.value = '';
    input.style.height = 'auto';
    
    // Send to API with streaming
    streamChatResponse(userQuery);
}

async function createNewChatAndSend(userQuery) {
    try {
        const response = await fetch('/api/chats', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: userQuery.substring(0, 50) })
        });
        
        if (response.ok) {
            const data = await response.json();
            currentChatSessionId = data.id;
            await loadChatSessions();
            sendMessage();
        }
    } catch (error) {
        showToast('Failed to start chat', 'error');
    }
}

function addMessageToUI(content, isUser) {
    const chatLog = document.getElementById('chat-log');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isUser ? 'user-message' : 'bot-message'}`;
    const avatarContent = isUser ? '👤' : '<img src="/static/images/serene.png" alt="Serene" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">';
    messageDiv.innerHTML = `
        <div class="message-wrapper">
            <div class="avatar ${isUser ? 'user-avatar' : 'bot-avatar'}">${avatarContent}</div>
            <div class="message-content">${isUser ? escapeHtml(content) : formatBotResponse(content)}</div>
        </div>
    `;
    chatLog.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
}

async function streamChatResponse(query) {
    const chatLog = document.getElementById('chat-log');
    const sendBtn = document.getElementById('send-button');
    
    // Create streaming message container
    const streamingId = 'streaming-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.id = streamingId;
    messageDiv.className = 'chat-message bot-message';
    messageDiv.innerHTML = `
        <div class="message-wrapper">
            <div class="avatar bot-avatar"><img src="/static/images/serene.png" alt="Serene" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;"></div>
            <div class="message-content">
                <span class="streaming-text"></span>
                <span class="streaming-cursor">▋</span>
            </div>
        </div>
    `;
    chatLog.appendChild(messageDiv);
    scrollToBottom();
    
    // Disable send button
    sendBtn.disabled = true;
    sendBtn.textContent = '...';
    
    let fullResponse = '';
    
    try {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                chat_session_id: currentChatSessionId
            })
        });
        
        if (!response.ok) throw new Error('Stream failed');
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        const streamingText = messageDiv.querySelector('.streaming-text');
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'token') {
                            fullResponse += data.content;
                            streamingText.innerHTML = formatBotResponse(fullResponse);
                            scrollToBottom();
                        } else if (data.type === 'done') {
                            // Handle completion
                            if (data.crisis_detected) {
                                messageDiv.classList.add('crisis-alert');
                            }
                        }
                    } catch (e) {
                        // Skip malformed JSON
                    }
                }
            }
        }
        
        // Remove cursor
        const cursor = messageDiv.querySelector('.streaming-cursor');
        if (cursor) cursor.remove();
        
        // Auto-update title if first message
        autoUpdateChatTitle(query);
        
        // Reload messages from backend to ensure they're saved properly
        await reloadCurrentChatMessages();
        
    } catch (error) {
        console.error('Streaming error:', error);
        // Fallback to regular API
        fallbackChatRequest(query, streamingId);
    }
    
    // Re-enable send button
    sendBtn.disabled = false;
    sendBtn.textContent = 'Send';
}

async function fallbackChatRequest(query, streamingId) {
    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `query=${encodeURIComponent(query)}&chat_session_id=${currentChatSessionId}`
        });
        
        const data = await response.json();
        const messageDiv = document.getElementById(streamingId);
        
        if (messageDiv) {
            const content = messageDiv.querySelector('.message-content');
            content.innerHTML = formatBotResponse(data.response);
            
            if (data.crisis_detected) {
                messageDiv.classList.add('crisis-alert');
            }
        }
        
        // Reload messages from backend
        await reloadCurrentChatMessages();
    } catch (error) {
        showToast('Failed to get response', 'error');
    }
}

async function autoUpdateChatTitle(firstMessage) {
    const currentTitle = document.getElementById('current-chat-title')?.textContent;
    
    if (currentTitle === 'New Chat' && currentChatSessionId) {
        const newTitle = firstMessage.substring(0, 40) + (firstMessage.length > 40 ? '...' : '');
        
        try {
            await fetch(`/api/chats/${currentChatSessionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: newTitle })
            });
            
            updateChatTitle(newTitle);
            loadChatSessions();
        } catch (error) {
            console.error('Failed to update title:', error);
        }
    }
}

function quickQuery(query) {
    const input = document.getElementById('user-input');
    if (input) {
        input.value = query;
        sendMessage();
    }
}

// ==================== MODAL MANAGEMENT ====================
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('visible');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('visible');
        document.body.style.overflow = '';
        
        // Clean up breathing exercise if closing that modal
        if (modalId === 'breathing-modal' && breathingInterval) {
            clearInterval(breathingInterval);
            breathingInterval = null;
            const circle = document.getElementById('breathing-circle');
            if (circle) {
                circle.style.transform = 'scale(1)';
                circle.textContent = '';
            }
        }
    }
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay') || e.target.classList.contains('modal')) {
        // Only close if clicking the overlay, not the content
        if (e.target === e.currentTarget) {
            e.target.style.display = 'none';
            e.target.classList.remove('visible');
            document.body.style.overflow = '';
        }
    }
});

// ==================== UTILITY FUNCTIONS ====================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatBotResponse(text) {
    if (!text) return '';
    text = text.replace(/\n/g, '<br>');
    text = text.replace(/(<br>){2,}/g, '</p><p>');
    return `<p>${text}</p>`;
}

function formatRelativeTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
}

function scrollToBottom() {
    const chatLog = document.getElementById('chat-log');
    if (chatLog) {
        chatLog.scrollTop = chatLog.scrollHeight;
    }
}

function showToast(message, type = 'info') {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(t => t.remove());
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('visible'), 10);
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Auto-resize textarea
function setupTextareaAutoResize() {
    const textarea = document.getElementById('user-input');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 150) + 'px';
        });
        
        // Send on Enter (without Shift)
        textarea.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

// Emergency Panel
function setupEmergencyPanel() {
    const emergencyBtn = document.querySelector('.emergency-btn');
    const emergencyCard = document.querySelector('.emergency-card');
    
    if (emergencyBtn && emergencyCard) {
        emergencyBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            emergencyCard.classList.toggle('visible');
        });
        
        document.addEventListener('click', (e) => {
            if (!emergencyCard.contains(e.target) && !emergencyBtn.contains(e.target)) {
                emergencyCard.classList.remove('visible');
            }
        });
    }
}

// ==================== DASHBOARD FUNCTIONS ====================
async function openDashboard() {
    openModal('dashboard-modal');
    await loadDashboardData();
}

async function loadDashboardData() {
    console.log('Loading dashboard data...');
    
    try {
        const response = await fetch('/api/dashboard/stats');
        
        if (response.ok) {
            const data = await response.json();
            
            // Update stats
            const totalChatsEl = document.getElementById('total-chats');
            const totalMessagesEl = document.getElementById('total-messages');
            const streakDaysEl = document.getElementById('streak-days');
            
            if (totalChatsEl) totalChatsEl.textContent = data.total_chats || 0;
            if (totalMessagesEl) totalMessagesEl.textContent = data.total_messages || 0;
            if (streakDaysEl) streakDaysEl.textContent = data.streak_days || 0;
            
            // Update recent activity
            const recentActivityEl = document.getElementById('recent-activity');
            if (recentActivityEl && data.recent_activity) {
                if (data.recent_activity.length === 0) {
                    recentActivityEl.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">No recent activity yet. Start a conversation! 💬</p>';
                } else {
                    recentActivityEl.innerHTML = data.recent_activity.map(activity => `
                        <div style="padding: 12px; background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: var(--radius-md); display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>${activity.title || 'Chat Session'}</strong>
                                <p style="color: var(--text-secondary); margin: 4px 0 0 0; font-size: 14px;">${activity.description || ''}</p>
                            </div>
                            <span style="color: var(--text-secondary); font-size: 12px;">${activity.time || ''}</span>
                        </div>
                    `).join('');
                }
            }
        } else {
            console.error('Failed to load dashboard data');
            // Show placeholder data
            const recentActivityEl = document.getElementById('recent-activity');
            if (recentActivityEl) {
                recentActivityEl.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">Start chatting to see your activity here! 💬</p>';
            }
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        // Show fallback message
        const recentActivityEl = document.getElementById('recent-activity');
        if (recentActivityEl) {
            recentActivityEl.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">Dashboard data will appear here once you start chatting! 🌊</p>';
        }
    }
}

// ==================== WELLNESS FUNCTIONS ====================
async function openWellnessModal() {
    openModal('wellness-modal');
    // Load wellness data
    await loadWellnessData();
}

function closeWellnessModal() {
    closeModal('wellness-modal');
}

async function loadWellnessData() {
    try {
        const [breathingRes, meditationRes, statsRes] = await Promise.all([
            fetch('/api/wellness/breathing'),
            fetch('/api/wellness/meditation'),
            fetch('/api/wellness/stats')
        ]);
        
        if (breathingRes.ok) {
            const data = await breathingRes.json();
            renderBreathingExercises(data.exercises || []);
        }
        
        if (meditationRes.ok) {
            const data = await meditationRes.json();
            renderMeditationSessions(data.sessions || []);
        }
        
        if (statsRes.ok) {
            const stats = await statsRes.json();
            updateWellnessStats(stats);
        }
    } catch (error) {
        console.error('Failed to load wellness data:', error);
    }
}

function updateWellnessStats(stats) {
    const streakEl = document.getElementById('wellness-streak');
    const minutesEl = document.getElementById('wellness-minutes');
    const sessionsEl = document.getElementById('wellness-sessions');
    
    if (streakEl) streakEl.textContent = stats.streak?.current || 0;
    if (minutesEl) minutesEl.textContent = stats.totals?.minutes || 0;
    if (sessionsEl) sessionsEl.textContent = stats.totals?.sessions || 0;
}

function renderBreathingExercises(exercises) {
    const grid = document.getElementById('breathing-exercises-grid');
    if (!grid) return;
    
    if (exercises.length === 0) {
        grid.innerHTML = '<p class="placeholder-text">No exercises available</p>';
        return;
    }
    
    grid.innerHTML = exercises.map(ex => `
        <div class="exercise-card" onclick="selectExercise('breathing', '${ex.id}')">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span style="font-size: 32px;">${ex.icon || '🌬️'}</span>
                <div>
                    <h4 style="margin: 0;">${ex.name}</h4>
                    <span style="font-size: 12px; color: var(--text-muted);">${ex.difficulty || 'Beginner'}</span>
                </div>
            </div>
            <p style="font-size: 13px; color: var(--text-secondary);">${ex.description}</p>
        </div>
    `).join('');
}

function renderMeditationSessions(sessions) {
    const grid = document.getElementById('meditation-exercises-grid');
    if (!grid) return;
    
    if (sessions.length === 0) {
        grid.innerHTML = '<p class="placeholder-text">No sessions available</p>';
        return;
    }
    
    grid.innerHTML = sessions.map(s => `
        <div class="exercise-card" onclick="selectExercise('meditation', '${s.id}')">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span style="font-size: 32px;">${s.icon || '🧘'}</span>
                <div>
                    <h4 style="margin: 0;">${s.name}</h4>
                    <span style="font-size: 12px; color: var(--text-muted);">${s.difficulty || 'Beginner'}</span>
                </div>
            </div>
            <p style="font-size: 13px; color: var(--text-secondary);">${s.description}</p>
        </div>
    `).join('');
}

function showWellnessTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.wellness-tab').forEach(tab => tab.classList.remove('active'));
    event?.target?.classList.add('active');
    
    // Show correct content
    const breathingTab = document.getElementById('breathing-tab');
    const meditationTab = document.getElementById('meditation-tab');
    
    if (breathingTab) breathingTab.style.display = tabName === 'breathing' ? 'block' : 'none';
    if (meditationTab) meditationTab.style.display = tabName === 'meditation' ? 'block' : 'none';
}

function selectExercise(type, exerciseId) {
    showToast(`Selected ${type} exercise: ${exerciseId}`, 'info');
    // Implement exercise selection logic
}

function startBreathingExercise() {
    openModal('breathing-modal');
}

let breathingInterval = null;
function startBreathingCycle() {
    const circle = document.getElementById('breathing-circle');
    const text = document.getElementById('breathing-text');
    
    if (breathingInterval) {
        clearInterval(breathingInterval);
        breathingInterval = null;
    }
    
    let step = 0;
    const steps = [
        { text: 'Breathe In', duration: 4, scale: 1.5 },
        { text: 'Hold', duration: 4, scale: 1.5 },
        { text: 'Breathe Out', duration: 4, scale: 1 },
        { text: 'Hold', duration: 4, scale: 1 }
    ];
    
    function runStep() {
        const currentStep = steps[step % 4];
        text.textContent = currentStep.text;
        circle.style.transform = `scale(${currentStep.scale})`;
        circle.textContent = currentStep.duration;
        
        let countdown = currentStep.duration;
        const countInterval = setInterval(() => {
            countdown--;
            circle.textContent = countdown;
            if (countdown === 0) clearInterval(countInterval);
        }, 1000);
        
        step++;
    }
    
    runStep();
    breathingInterval = setInterval(runStep, 4000);
    
    showToast('Breathing exercise started. Relax and follow along.', 'success');
}

function openJournal() {
    openModal('journal-modal');
    document.getElementById('journal-text').value = '';
    document.getElementById('journal-text').focus();
}

function saveJournalEntry() {
    const entry = document.getElementById('journal-text').value.trim();
    if (entry) {
        // In a real app, this would save to the backend
        showToast('✨ Journal entry saved! Keep writing to track your thoughts.', 'success');
        closeModal('journal-modal');
    } else {
        showToast('Please write something before saving.', 'info');
    }
}

function showSleepTips() {
    openModal('sleep-modal');
}

function startGratitude() {
    openModal('gratitude-modal');
    document.getElementById('gratitude-1').value = '';
    document.getElementById('gratitude-2').value = '';
    document.getElementById('gratitude-3').value = '';
    document.getElementById('gratitude-1').focus();
}

function saveGratitude() {
    const g1 = document.getElementById('gratitude-1').value.trim();
    const g2 = document.getElementById('gratitude-2').value.trim();
    const g3 = document.getElementById('gratitude-3').value.trim();
    
    if (g1 && g2 && g3) {
        // In a real app, this would save to the backend
        showToast('✨ Gratitude list saved! Practicing gratitude boosts mood and wellbeing.', 'success');
        closeModal('gratitude-modal');
    } else {
        showToast('Please fill in all three gratitude items.', 'info');
    }
}

// ==================== SIDEBAR FUNCTIONS ====================
function toggleSidebar() {
    const sidebar = document.getElementById('chat-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('hidden');
    }
}

// ==================== PROFILE FUNCTIONS ====================
function openProfile() {
    if (currentUser) {
        const displayNameInput = document.getElementById('profile-display-name');
        const emailInput = document.getElementById('profile-email');
        const usernameInput = document.getElementById('profile-username');
        const bioInput = document.getElementById('profile-bio');
        const profileAvatar = document.getElementById('profile-avatar');
        
        if (displayNameInput) displayNameInput.value = currentUser.display_name || '';
        if (emailInput) emailInput.value = currentUser.email || '';
        if (usernameInput) usernameInput.value = currentUser.username || '';
        if (bioInput) bioInput.value = currentUser.bio || '';
        
        // Load avatar config if exists
        if (profileAvatar) {
            if (currentUser.avatar_config) {
                try {
                    const config = JSON.parse(currentUser.avatar_config);
                    profileAvatar.style.backgroundColor = config.color || '#2D5A3D';
                    profileAvatar.textContent = config.emoji || '👤';
                } catch (e) {
                    console.log('Using default avatar');
                    profileAvatar.style.backgroundColor = '#2D5A3D';
                    profileAvatar.textContent = '👤';
                }
            } else {
                // Set default avatar
                profileAvatar.style.backgroundColor = '#2D5A3D';
                profileAvatar.textContent = '👤';
            }
        }
    }
    openModal('profile-modal');
}

function openSettings() {
    openModal('settings-modal');
}

function saveSettings() {
    showToast('Settings saved', 'success');
    closeModal('settings-modal');
}

function changePassword() {
    showToast('Password change functionality', 'info');
}

function deleteAccount() {
    if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
        showToast('Account deletion functionality coming soon', 'info');
    }
}

// Avatar customizer state
let currentAvatarConfig = {
    emoji: '👤',
    color: '#2D5A3D'
};

function openAvatarCustomizer() {
    // Load current avatar if exists
    if (currentUser && currentUser.avatar_config) {
        try {
            currentAvatarConfig = JSON.parse(currentUser.avatar_config);
        } catch (e) {
            console.log('Using default avatar config');
            currentAvatarConfig = {
                emoji: '👤',
                color: '#2D5A3D'
            };
        }
    } else {
        // Reset to default if no config
        currentAvatarConfig = {
            emoji: '👤',
            color: '#2D5A3D'
        };
    }
    
    // Update preview
    updateAvatarPreview();
    openModal('avatar-customizer-modal');
}

function selectAvatarStyle(emoji) {
    currentAvatarConfig.emoji = emoji;
    updateAvatarPreview();
    
    // Visual feedback
    document.querySelectorAll('.avatar-option').forEach(btn => {
        btn.style.borderColor = 'var(--border-color)';
        btn.style.transform = 'scale(1)';
    });
    event.target.style.borderColor = 'var(--accent)';
    event.target.style.transform = 'scale(1.1)';
}

function selectAvatarColor(color) {
    currentAvatarConfig.color = color;
    updateAvatarPreview();
}

function updateAvatarPreview() {
    const preview = document.getElementById('avatar-preview');
    if (preview) {
        preview.style.backgroundColor = currentAvatarConfig.color;
        preview.textContent = currentAvatarConfig.emoji;
    }
}

async function saveCustomAvatar() {
    try {
        // Save to backend
        const response = await fetch('/api/auth/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                avatar_config: JSON.stringify(currentAvatarConfig)
            })
        });

        const result = await response.json();
        
        if (result.success) {
            // Update profile avatar display
            const profileAvatar = document.getElementById('profile-avatar');
            if (profileAvatar) {
                profileAvatar.style.backgroundColor = currentAvatarConfig.color;
                profileAvatar.textContent = currentAvatarConfig.emoji;
            }
            
            // Update header avatar if exists
            const headerAvatar = document.querySelector('.user-avatar-small');
            if (headerAvatar) {
                headerAvatar.style.backgroundColor = currentAvatarConfig.color;
                headerAvatar.textContent = currentAvatarConfig.emoji;
            }
            
            // Update current user
            if (currentUser) {
                currentUser.avatar_config = JSON.stringify(currentAvatarConfig);
            }
            
            showToast('Avatar updated successfully! ✨', 'success');
            closeModal('avatar-customizer-modal');
        } else {
            showToast(result.message || 'Failed to update avatar', 'error');
        }
    } catch (error) {
        console.error('Error saving avatar:', error);
        showToast('Failed to save avatar', 'error');
    }
}

async function saveProfile() {
    const displayName = document.getElementById('profile-display-name')?.value;
    const email = document.getElementById('profile-email')?.value;
    const bio = document.getElementById('profile-bio')?.value;
    
    if (!displayName || !email) {
        showToast('Please fill in all required fields', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                display_name: displayName,
                email: email,
                bio: bio
            })
        });
        
        if (response.ok) {
            showToast('Profile updated successfully! ✨', 'success');
            closeModal('profile-modal');
            // Refresh user data
            await checkAuthStatus();
        } else {
            const error = await response.json();
            showToast(error.message || 'Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('Error saving profile:', error);
        showToast('Failed to update profile', 'error');
    }
}

async function saveMood(mood) {
    console.log('Saving mood:', mood);
    
    try {
        const response = await fetch('/api/dashboard/mood', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mood: mood })
        });
        
        if (response.ok) {
            const moodEmojis = {
                'great': '😄',
                'good': '🙂',
                'okay': '😐',
                'bad': '😔',
                'terrible': '😢'
            };
            showToast(`Mood saved: ${moodEmojis[mood] || ''}`, 'success');
            // Reload dashboard data
            await loadDashboardData();
        } else {
            showToast('Failed to save mood', 'error');
        }
    } catch (error) {
        console.error('Error saving mood:', error);
        showToast('Your mood has been noted', 'success'); // Fallback for offline
    }
}

async function clearAllChats() {
    if (!confirm('Are you sure you want to delete ALL your chat history? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/chats/clear', {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('All chats cleared successfully', 'success');
            // Reload chat sessions
            await loadChatSessions();
            // Clear current chat
            currentSessionId = null;
            const chatLog = document.getElementById('chat-log');
            if (chatLog) chatLog.innerHTML = '';
        } else {
            showToast('Failed to clear chats', 'error');
        }
    } catch (error) {
        console.error('Error clearing chats:', error);
        showToast('Failed to clear chats', 'error');
    }
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme icon
    const currentTheme = document.documentElement.getAttribute('data-theme');
    updateThemeIcon(currentTheme);
    
    // Check auth status
    checkAuthStatus();
    
    // Setup UI components
    setupUserDropdown();
    setupTextareaAutoResize();
    setupEmergencyPanel();
    
    // Load chat sessions
    loadChatSessions();
    
    // Setup send button
    const sendBtn = document.getElementById('send-button');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    // Focus input
    const input = document.getElementById('user-input');
    if (input) input.focus();
});
