// Main Application JavaScript
class VoiceAIApp {
    constructor() {
        this.sessionId = null;
        this.selectedAgent = 'orchestrator';
        this.autoSpeak = true;
        this.includeSources = true;
        this.voiceType = 'alloy';
        this.ttsSpeed = 1.0;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        this.init();
    }
    
    async init() {
        console.log('Initializing Voice AI App...');
        
        // Generate session ID
        this.sessionId = this.generateSessionId();
        document.getElementById('sessionId').textContent = this.sessionId.substring(0, 8) + '...';
        
        // Load system info
        await this.loadSystemInfo();
        
        // Initialize event listeners
        this.initEventListeners();
        
        // Update metrics periodically
        setInterval(() => this.updateMetrics(), 5000);
        
        console.log('App initialized successfully');
    }
    
    generateSessionId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    initEventListeners() {
        // Agent selection
        document.querySelectorAll('.agent-item').forEach(item => {
            item.addEventListener('click', (e) => {
                document.querySelectorAll('.agent-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                this.selectedAgent = item.dataset.agent;
                console.log('Selected agent:', this.selectedAgent);
            });
        });
        
        // Text input and send
        const textInput = document.getElementById('textInput');
        const sendBtn = document.getElementById('btnSend');
        
        textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Voice recording
        const voiceBtn = document.getElementById('btnVoice');
        voiceBtn.addEventListener('mousedown', () => this.startRecording());
        voiceBtn.addEventListener('mouseup', () => this.stopRecording());
        voiceBtn.addEventListener('mouseleave', () => {
            if (this.isRecording) this.stopRecording();
        });
        
        // Touch events for mobile
        voiceBtn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startRecording();
        });
        voiceBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopRecording();
        });
        
        // File upload
        const uploadBtn = document.getElementById('btnUpload');
        const fileInput = document.getElementById('fileUpload');
        
        uploadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        
        // Settings
        document.getElementById('chkAutoSpeak').addEventListener('change', (e) => {
            this.autoSpeak = e.target.checked;
        });
        
        document.getElementById('chkIncludeSources').addEventListener('change', (e) => {
            this.includeSources = e.target.checked;
        });
        
        document.getElementById('voiceSelect').addEventListener('change', (e) => {
            this.voiceType = e.target.value;
        });
        
        // Modals
        document.getElementById('btnSettings').addEventListener('click', () => {
            document.getElementById('settingsModal').classList.add('active');
        });
        
        document.getElementById('btnMetrics').addEventListener('click', () => {
            this.showMetricsModal();
        });
        
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.target.closest('.modal').classList.remove('active');
            });
        });
        
        // Settings controls
        const tempSlider = document.getElementById('temperature');
        tempSlider.addEventListener('input', (e) => {
            document.getElementById('tempValue').textContent = e.target.value;
        });
        
        const speedSlider = document.getElementById('ttsSpeed');
        speedSlider.addEventListener('input', (e) => {
            document.getElementById('speedValue').textContent = e.target.value;
            this.ttsSpeed = parseFloat(e.target.value);
        });
        
        // New session
        document.getElementById('btnNewSession').addEventListener('click', () => {
            this.startNewSession();
        });
    }
    
    async sendMessage(text = null) {
        const messageText = text || document.getElementById('textInput').value.trim();
        
        if (!messageText) return;
        
        // Clear input
        if (!text) {
            document.getElementById('textInput').value = '';
        }
        
        // Add user message to chat
        this.addMessage('user', messageText);
        
        // Show loading
        this.showLoading('Processing message...');
        
        try {
            // Send to backend
            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: messageText,
                    session_id: this.sessionId,
                    agent_override: this.selectedAgent === 'orchestrator' ? null : this.selectedAgent,
                    include_sources: this.includeSources
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to send message');
            }
            
            const data = await response.json();
            
            // Add assistant message
            this.addMessage('assistant', data.response, {
                agent: data.agent_used,
                sources: data.sources,
                metrics: data.metrics
            });
            
            // Auto-speak if enabled
            if (this.autoSpeak) {
                await this.speakText(data.response);
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('assistant', 'Sorry, I encountered an error processing your message. Please try again.');
        } finally {
            this.hideLoading();
        }
    }
    
    addMessage(type, content, metadata = {}) {
        const messagesContainer = document.getElementById('chatMessages');
        
        // Remove welcome message if exists
        const welcomeMsg = messagesContainer.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        bubbleDiv.textContent = content;
        
        contentDiv.appendChild(bubbleDiv);
        
        // Add metadata if assistant message
        if (type === 'assistant' && metadata.agent) {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'message-meta';
            metaDiv.innerHTML = `Agent: ${metadata.agent}`;
            
            if (metadata.metrics) {
                metaDiv.innerHTML += ` | Response time: ${metadata.metrics.total_time_ms.toFixed(0)}ms`;
            }
            
            contentDiv.appendChild(metaDiv);
        }
        
        // Add sources if available
        if (metadata.sources && metadata.sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            sourcesDiv.innerHTML = '<strong>Sources:</strong>';
            
            metadata.sources.forEach(source => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.innerHTML = `📄 ${source.metadata.filename || 'Document'} (Score: ${source.score.toFixed(2)})`;
                sourcesDiv.appendChild(sourceItem);
            });
            
            contentDiv.appendChild(sourcesDiv);
        }
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    async startRecording() {
        if (this.isRecording) return;
        
        console.log('Starting recording...');
        this.isRecording = true;
        this.audioChunks = [];
        
        const voiceBtn = document.getElementById('btnVoice');
        voiceBtn.classList.add('recording');
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                await this.processAudioRecording(audioBlob);
            };
            
            this.mediaRecorder.start();
        } catch (error) {
            console.error('Error starting recording:', error);
            this.isRecording = false;
            voiceBtn.classList.remove('recording');
            alert('Failed to access microphone. Please check permissions.');
        }
    }
    
    stopRecording() {
        if (!this.isRecording) return;
        
        console.log('Stopping recording...');
        this.isRecording = false;
        
        const voiceBtn = document.getElementById('btnVoice');
        voiceBtn.classList.remove('recording');
        
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }
    
    async processAudioRecording(audioBlob) {
        this.showLoading('Transcribing audio...');
        
        try {
            const formData = new FormData();
            formData.append('audio_file', audioBlob, 'recording.webm');
            
            const response = await fetch('/api/audio/transcribe', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Failed to transcribe audio');
            }
            
            const data = await response.json();
            
            // Set transcribed text in input
            document.getElementById('textInput').value = data.text;
            
            // Optionally auto-send
            if (data.text.trim()) {
                await this.sendMessage(data.text);
            }
            
        } catch (error) {
            console.error('Error processing audio:', error);
            alert('Failed to transcribe audio. Please try again.');
        } finally {
            this.hideLoading();
        }
    }
    
    async speakText(text) {
        try {
            const response = await fetch('/api/audio/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    voice: this.voiceType,
                    speed: this.ttsSpeed
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to generate speech');
            }
            
            const data = await response.json();
            
            // Play audio
            const audio = document.getElementById('audioPlayer');
            audio.src = `data:audio/mp3;base64,${data.audio}`;
            await audio.play();
            
        } catch (error) {
            console.error('Error generating speech:', error);
        }
    }
    
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const agentSelect = document.getElementById('uploadAgent');
        const selectedAgent = agentSelect.value;
        
        if (!selectedAgent) {
            alert('Please select an agent for the document');
            return;
        }
        
        this.showLoading('Uploading document...');
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('agent', selectedAgent);
        
        try {
            const response = await fetch('/api/rag/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Failed to upload document');
            }
            
            const data = await response.json();
            
            const statusDiv = document.getElementById('uploadStatus');
            statusDiv.className = 'upload-status success';
            statusDiv.textContent = `✓ Uploaded ${data.filename} (${data.chunks_created} chunks created)`;
            
            // Clear after 5 seconds
            setTimeout(() => {
                statusDiv.className = 'upload-status';
                statusDiv.textContent = '';
            }, 5000);
            
        } catch (error) {
            console.error('Error uploading file:', error);
            
            const statusDiv = document.getElementById('uploadStatus');
            statusDiv.className = 'upload-status error';
            statusDiv.textContent = '✗ Failed to upload document';
        } finally {
            this.hideLoading();
            event.target.value = '';
        }
    }
    
    async loadSystemInfo() {
        try {
            const response = await fetch('/api/system-info');
            const data = await response.json();
            console.log('System info:', data);
        } catch (error) {
            console.error('Error loading system info:', error);
        }
    }
    
    async updateMetrics() {
        try {
            // Update audio metrics
            const audioResponse = await fetch('/api/audio/metrics');
            const audioData = await audioResponse.json();
            
            if (audioData.stt.avg_duration_ms) {
                document.getElementById('avgSttTime').textContent = `${audioData.stt.avg_duration_ms.toFixed(0)}ms`;
            }
            
            if (audioData.tts.avg_duration_ms) {
                document.getElementById('avgTtsTime').textContent = `${audioData.tts.avg_duration_ms.toFixed(0)}ms`;
            }
            
            // Update chat metrics
            const chatResponse = await fetch('/api/chat/metrics');
            const chatData = await chatResponse.json();
            
            if (chatData.by_agent && Object.keys(chatData.by_agent).length > 0) {
                const avgTimes = Object.values(chatData.by_agent).map(a => a.avg_response_time_ms);
                const avgTime = avgTimes.reduce((a, b) => a + b, 0) / avgTimes.length;
                document.getElementById('avgResponseTime').textContent = `${avgTime.toFixed(0)}ms`;
            }
            
            // Update RAG metrics
            const ragResponse = await fetch('/api/rag/metrics');
            const ragData = await ragResponse.json();
            
            if (ragData.retrieval.avg_retrieval_time_ms) {
                document.getElementById('avgRetrievalTime').textContent = `${ragData.retrieval.avg_retrieval_time_ms.toFixed(0)}ms`;
            }
            
        } catch (error) {
            console.error('Error updating metrics:', error);
        }
    }
    
    async showMetricsModal() {
        this.showLoading('Loading metrics...');
        
        try {
            // Fetch all metrics
            const [audioMetrics, chatMetrics, ragMetrics] = await Promise.all([
                fetch('/api/audio/metrics').then(r => r.json()),
                fetch('/api/chat/metrics').then(r => r.json()),
                fetch('/api/rag/metrics').then(r => r.json())
            ]);
            
            const metricsContent = document.getElementById('metricsContent');
            metricsContent.innerHTML = `
                <div class="metrics-section">
                    <h3>Audio Processing</h3>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <h4>Speech-to-Text</h4>
                            <p>Processed: ${audioMetrics.stt.total_processed}</p>
                            <p>Avg Time: ${audioMetrics.stt.avg_duration_ms.toFixed(0)}ms</p>
                        </div>
                        <div class="metric-card">
                            <h4>Text-to-Speech</h4>
                            <p>Processed: ${audioMetrics.tts.total_processed}</p>
                            <p>Avg Time: ${audioMetrics.tts.avg_duration_ms.toFixed(0)}ms</p>
                        </div>
                    </div>
                </div>
                
                <div class="metrics-section">
                    <h3>Chat Performance</h3>
                    <div class="metrics-grid">
                        ${Object.entries(chatMetrics.by_agent || {}).map(([agent, data]) => `
                            <div class="metric-card">
                                <h4>${agent}</h4>
                                <p>Requests: ${data.count}</p>
                                <p>Avg Time: ${data.avg_response_time_ms.toFixed(0)}ms</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="metrics-section">
                    <h3>Document Retrieval</h3>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <h4>Queries</h4>
                            <p>Total: ${ragMetrics.retrieval.total_queries}</p>
                            <p>Avg Time: ${ragMetrics.retrieval.avg_retrieval_time_ms.toFixed(0)}ms</p>
                        </div>
                        <div class="metric-card">
                            <h4>Documents</h4>
                            <p>Processed: ${ragMetrics.document_processing.total_documents}</p>
                            <p>Total Chunks: ${ragMetrics.document_processing.total_chunks}</p>
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('metricsModal').classList.add('active');
            
        } catch (error) {
            console.error('Error loading metrics:', error);
            alert('Failed to load metrics');
        } finally {
            this.hideLoading();
        }
    }
    
    startNewSession() {
        if (confirm('Start a new session? This will clear the current conversation.')) {
            // Clear current session
            fetch('/api/chat/clear-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ session_id: this.sessionId })
            });
            
            // Generate new session ID
            this.sessionId = this.generateSessionId();
            document.getElementById('sessionId').textContent = this.sessionId.substring(0, 8) + '...';
            
            // Clear chat messages
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <i class="fas fa-robot fa-3x"></i>
                    <h2>Welcome to Voice-Enabled AI Agent</h2>
                    <p>Ask me anything! Use voice or text input.</p>
                    <p>I can help with Real Estate, Medical, AI/ML, Sales, and Education topics.</p>
                </div>
            `;
        }
    }
    
    showLoading(text = 'Loading...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        loadingText.textContent = text;
        overlay.style.display = 'flex';
    }
    
    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }
}

// Add styles for metrics modal
const style = document.createElement('style');
style.textContent = `
    .metrics-section {
        margin-bottom: 2rem;
    }
    
    .metrics-section h3 {
        margin-bottom: 1rem;
        color: var(--primary-color);
    }
    
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }
    
    .metric-card {
        background-color: var(--light-bg);
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid var(--border-color);
    }
    
    .metric-card h4 {
        margin-bottom: 0.5rem;
        color: var(--text-primary);
    }
    
    .metric-card p {
        margin-bottom: 0.25rem;
        font-size: 0.875rem;
        color: var(--text-secondary);
    }
`;
document.head.appendChild(style);

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VoiceAIApp();
});
