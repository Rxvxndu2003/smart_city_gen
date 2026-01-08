/**
 * WebSocket-based 3D generation with live updates
 */

export interface GenerationUpdate {
  type: 'connected' | 'progress' | 'mesh_update' | 'error' | 'completed';
  message?: string;
  progress?: number;
  stage?: string;
  mesh?: any;
  error?: string;
}

export interface GenerationCallbacks {
  onProgress: (message: string, progress: number) => void;
  onComplete: (modelUrl: string) => void;
  onError: (error: string) => void;
  onConnect?: () => void;
}

export class GenerationWebSocket {
  private ws: WebSocket | null = null;
  private projectId: number;
  private apiBaseUrl: string;
  private token: string;
  private callbacks: GenerationCallbacks;
  private fallbackPolling: number | null = null;

  constructor(
    projectId: number,
    apiBaseUrl: string,
    token: string,
    callbacks: GenerationCallbacks
  ) {
    this.projectId = projectId;
    this.apiBaseUrl = apiBaseUrl;
    this.token = token;
    this.callbacks = callbacks;
  }

  async start() {
    try {
      // Try WebSocket connection
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = new URL(this.apiBaseUrl).host;
      const wsUrl = `${wsProtocol}//${wsHost}/ws/generation/${this.projectId}`;
      
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.callbacks.onConnect?.();
        this.callbacks.onProgress('🔗 Connected - Starting generation...', 5);
        
        // Trigger generation
        this.startGeneration();
      };

      this.ws.onmessage = (event) => {
        try {
          const data: GenerationUpdate = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (err) {
          console.error('WebSocket message error:', err);
        }
      };

      this.ws.onerror = () => {
        console.error('WebSocket error - falling back to polling');
        this.callbacks.onProgress('⚠️ Connection issue - using fallback...', 10);
        this.close();
        this.startFallbackPolling();
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
      };

    } catch (err) {
      console.error('WebSocket initialization error:', err);
      this.startFallbackPolling();
    }
  }

  private async startGeneration() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/generation/${this.projectId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to start generation: ${response.status}`);
      }
    } catch (err: any) {
      console.error('Generation start error:', err);
      this.callbacks.onError(err.message);
      this.close();
    }
  }

  private handleMessage(data: GenerationUpdate) {
    switch (data.type) {
      case 'connected':
        console.log('WebSocket established:', data.message);
        break;
        
      case 'progress':
        if (data.message && data.progress !== undefined) {
          this.callbacks.onProgress(data.message, data.progress);
        }
        break;
        
      case 'mesh_update':
        console.log('Mesh update:', data.stage, data.progress + '%');
        // Can be used for live 3D preview in future
        break;
        
      case 'completed':
        this.fetchFinalStatus();
        break;
        
      case 'error':
        this.callbacks.onError(data.error || 'Unknown error');
        this.close();
        break;
    }

    // Auto-complete at 100%
    if (data.progress === 100 || data.stage === 'completed') {
      setTimeout(() => this.fetchFinalStatus(), 1000);
    }
  }

  private async fetchFinalStatus() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/generation/${this.projectId}/status`, {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.model_url) {
          this.callbacks.onComplete(data.model_url);
        } else {
          this.callbacks.onError('Model URL not found');
        }
      }
    } catch (err: any) {
      this.callbacks.onError(err.message);
    } finally {
      this.close();
    }
  }

  private startFallbackPolling() {
    let pollCount = 0;
    
    this.fallbackPolling = window.setInterval(async () => {
      pollCount++;
      
      try {
        const response = await fetch(`${this.apiBaseUrl}/generation/${this.projectId}/status`, {
          headers: { 'Authorization': `Bearer ${this.token}` }
        });

        if (!response.ok) {
          this.callbacks.onError('Failed to check status');
          this.close();
          return;
        }

        const data = await response.json();

        if (data.status === 'queued') {
          this.callbacks.onProgress('⏳ Queued for processing...', 10);
        } else if (data.status === 'processing') {
          const progress = Math.min(90, 20 + pollCount * 10);
          this.callbacks.onProgress(`🔨 Processing 3D model... (${pollCount * 3}s)`, progress);
        } else if (data.status === 'completed') {
          if (data.model_url) {
            this.callbacks.onProgress('✅ 3D model generated successfully!', 100);
            this.callbacks.onComplete(data.model_url);
          }
          this.close();
        } else if (data.status === 'failed') {
          this.callbacks.onError(data.error || 'Generation failed');
          this.close();
        }
      } catch (err: any) {
        console.error('Polling error:', err);
      }
    }, 3000);

    // Timeout after 5 minutes
    setTimeout(() => {
      this.callbacks.onError('Generation timeout');
      this.close();
    }, 300000);
  }

  close() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    if (this.fallbackPolling) {
      clearInterval(this.fallbackPolling);
      this.fallbackPolling = null;
    }
  }
}
