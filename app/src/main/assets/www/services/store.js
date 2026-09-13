// ==========================================================================
// JARVIS Local Reactive State & Persistence Store
// Handles data models, mock engines, and localStorage synchronization
// ==========================================================================

const STORAGE_KEY = 'JARVIS_STATE_V1';

const DEFAULT_STATE = {
  activeScreen: 'core',
  navigationHistory: ['core'],
  assistantState: 'READY', // 'READY' | 'LISTENING' | 'THINKING' | 'SPEAKING' | 'OFFLINE'
  connectionStatus: 'ONLINE', // 'ONLINE' | 'STANDBY' | 'DEMO'
  
  // Telemetry & Vitals
  telemetry: {
    battery: 96,
    isCharging: true,
    computeLoad: '3.8 TFLOPS',
    neuralLatency: '4.2 ms',
    memoryUsage: '64.2%',
    coreTemp: '312 K',
    arcOutput: '3.8 GJ/s',
    uptime: '14d 08h 22m'
  },

  // Settings & Preferences
  settings: {
    hapticFeedback: true,
    soundEffects: true,
    visualGlowIntensity: 85,
    reducedMotion: false,
    ttsVoice: 'British Male (JARVIS Synthetic)',
    autoBriefing: true,
    demoModeNotice: true
  },

  // Chat History
  chatMessages: [
    {
      id: 'msg-1',
      sender: 'user',
      text: 'Good morning JARVIS. Systems check and today\'s schedule.',
      timestamp: '09:14 AM'
    },
    {
      id: 'msg-2',
      sender: 'jarvis',
      text: 'Good morning, sir. All core subroutines are functioning within nominal parameters. Quantum neural links are locked at 4.2ms latency. You have 3 priority tasks scheduled today, and global markets show positive momentum.',
      timestamp: '09:14 AM',
      citations: ['SYSTEM.TELEMETRY', 'TASK_ENGINE_V1'],
      uncertainty: 'Verified with 99.4% confidence'
    }
  ],

  // Tasks Data
  tasks: [
    {
      id: 'task-1',
      title: 'Analyze Q3 Semiconductor Market Trends',
      description: 'Synthesize earnings reports from top 5 fab manufacturers with focus on AI accelerator demand.',
      category: 'research',
      priority: 'high',
      status: 'active',
      progress: 65,
      dueDate: 'Today, 05:00 PM',
      createdAt: '2026-09-08'
    },
    {
      id: 'task-2',
      title: 'Review Python Backend Architecture',
      description: 'Audit FastAPI endpoints and Pydantic schema validation for WebSocket tool streaming.',
      category: 'code',
      priority: 'medium',
      status: 'active',
      progress: 40,
      dueDate: 'Tomorrow, 12:00 PM',
      createdAt: '2026-09-09'
    },
    {
      id: 'task-3',
      title: 'Smart Office Ambient Climate Sync',
      description: 'Maintain temperature between 21°C and 23°C during working hours.',
      category: 'devices',
      priority: 'low',
      status: 'completed',
      progress: 100,
      dueDate: 'Today, 08:00 AM',
      createdAt: '2026-09-07'
    },
    {
      id: 'task-4',
      title: 'Scheduled Portfolio Rebalance Simulation',
      description: 'Run backtest on 60/40 tech-etf allocation with strict 2% trailing stop limits.',
      category: 'markets',
      priority: 'high',
      status: 'scheduled',
      progress: 0,
      dueDate: 'Friday, 09:30 AM',
      createdAt: '2026-09-09'
    }
  ],

  // Research & Searches
  recentSearches: [
    'Next-gen photonic computing architectures',
    'Global copper supply chain disruptions',
    'FastAPI WebSockets high-concurrency benchmarks'
  ],
  savedResearch: [
    {
      id: 'res-1',
      title: 'Quantum Advantage in Cryptographic Primitives',
      domain: 'nature.com/articles/phys-2026',
      date: 'Sept 04, 2026',
      summary: 'Experimental demonstration of 1,200-qubit coherence times exceeding error-correction thresholds.',
      category: 'Physics'
    },
    {
      id: 'res-2',
      title: 'Autonomous Multi-Agent Policy Alignment',
      domain: 'arxiv.org/abs/2608.11029',
      date: 'Aug 29, 2026',
      summary: 'Centralized risk-scoring protocols preventing catastrophic tool execution in embodied AI.',
      category: 'AI Safety'
    }
  ],

  // News Intelligence
  newsItems: [
    {
      id: 'news-1',
      headline: 'Next-Gen Silicon Photonics Breakthrough Unveiled in Zurich Lab',
      source: 'Tech Global Wire',
      timestamp: '22m ago',
      category: 'Technology',
      region: 'Europe',
      isBreaking: true,
      read: false,
      saved: true
    },
    {
      id: 'news-2',
      headline: 'Federal Reserve Signals Steady Interest Rates Amid Controlled Core Inflation',
      source: 'Financial Standard',
      timestamp: '1h ago',
      category: 'Economy',
      region: 'North America',
      isBreaking: false,
      read: false,
      saved: false
    },
    {
      id: 'news-3',
      headline: 'Renewable Storage Grid Capacity Surpasses 45% Milestone in APAC Region',
      source: 'Clean Energy Monitor',
      timestamp: '3h ago',
      category: 'Energy',
      region: 'Asia-Pacific',
      isBreaking: false,
      read: true,
      saved: false
    }
  ],

  // Financial Markets Data (All labelled as Simulated / Demo Data)
  markets: [
    {
      symbol: 'S&P 500',
      name: 'Standard & Poor\'s 500',
      price: '5,842.10',
      change: '+34.20',
      changePct: '+0.59%',
      isPositive: true,
      volume: '3.4B',
      isWatchlist: true,
      sparkline: [40, 45, 42, 55, 60, 58, 64, 72, 70, 78, 85]
    },
    {
      symbol: 'NASDAQ',
      name: 'Nasdaq Composite',
      price: '18,410.50',
      change: '+142.80',
      changePct: '+0.78%',
      isPositive: true,
      volume: '4.8B',
      isWatchlist: true,
      sparkline: [50, 48, 55, 62, 60, 75, 72, 80, 88, 84, 95]
    },
    {
      symbol: 'NVDA',
      name: 'NVIDIA Corporation',
      price: '138.45',
      change: '+3.15',
      changePct: '+2.33%',
      isPositive: true,
      volume: '62.1M',
      isWatchlist: true,
      sparkline: [30, 32, 40, 42, 50, 62, 68, 75, 82, 90, 100]
    },
    {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      price: '232.10',
      change: '-0.85',
      changePct: '-0.36%',
      isPositive: false,
      volume: '41.2M',
      isWatchlist: true,
      sparkline: [70, 68, 65, 62, 60, 58, 55, 59, 54, 52, 48]
    },
    {
      symbol: 'BTC/USD',
      name: 'Bitcoin Core Index',
      price: '68,420.00',
      change: '+1,820.00',
      changePct: '+2.73%',
      isPositive: true,
      volume: '28.4B',
      isWatchlist: false,
      sparkline: [60, 65, 62, 70, 75, 72, 80, 85, 82, 90, 94]
    }
  ],

  // Smart Connected Devices
  devices: [
    {
      id: 'dev-1',
      name: 'Lab Primary HUD Lighting',
      type: 'light',
      room: 'Main Laboratory',
      isOnline: true,
      state: true,
      value: 85,
      unit: '%'
    },
    {
      id: 'dev-2',
      name: 'Atmospheric Air Circulation',
      type: 'thermostat',
      room: 'Main Laboratory',
      isOnline: true,
      state: true,
      value: 22.5,
      unit: '°C'
    },
    {
      id: 'dev-3',
      name: 'Acoustic Sound Matrix',
      type: 'speaker',
      room: 'Living Suite',
      isOnline: true,
      state: false,
      value: 45,
      unit: 'VOL'
    },
    {
      id: 'dev-4',
      name: 'Perimeter Optical Sensor Array',
      type: 'camera',
      room: 'Exterior Perimeter',
      isOnline: true,
      state: true,
      value: 100,
      unit: 'SEC'
    }
  ],

  // Files Workspace
  files: [
    {
      id: 'file-1',
      name: 'aegis_system_architecture.md',
      type: 'markdown',
      size: '14.2 KB',
      modifiedAt: 'Today, 04:12 AM',
      content: '# AEGIS System Architecture\n\n6-Plane Autonomous Agent System with verified R0-R4 safety gates and multi-model routing.'
    },
    {
      id: 'file-2',
      name: 'server_gateway.py',
      type: 'python',
      size: '28.6 KB',
      modifiedAt: 'Yesterday, 11:30 PM',
      content: 'from fastapi import FastAPI, WebSocket\n\napp = FastAPI(title="JARVIS AI Gateway")\n\n@app.get("/health")\nasync def health():\n    return {"status": "nominal"}'
    },
    {
      id: 'file-3',
      name: 'portfolio_risk_model.json',
      type: 'json',
      size: '5.8 KB',
      modifiedAt: 'Sept 08, 2026',
      content: '{\n  "max_portfolio_exposure": 0.25,\n  "max_daily_loss_pct": 2.0,\n  "hard_stop_active": true\n}'
    }
  ],

  // Coding Projects & Tasks
  codeProjects: [
    {
      id: 'proj-1',
      name: 'JARVIS-Android-Engine',
      language: 'Kotlin / Python',
      branch: 'main',
      status: 'Healthy',
      tasks: [
        {
          id: 'ctask-1',
          title: 'Implement WebSocket Streaming Handler',
          description: 'Enable real-time token streaming and audio buffer synchronization.',
          status: 'ready_for_test',
          diff: '+ async def stream_tokens(ws: WebSocket):\n+     async for chunk in model.generate_stream():\n+         await ws.send_text(chunk.text)',
          testResults: '3 passed, 0 failed [124ms]'
        },
        {
          id: 'ctask-2',
          title: 'Add Strict Pydantic Tool Validations',
          description: 'Guarantee type safety and schema verification before execution.',
          status: 'applied',
          diff: '+ class ToolRequest(BaseModel):\n+     tool_name: str\n+     parameters: Dict[str, Any]',
          testResults: '7 passed, 0 failed [88ms]'
        }
      ]
    }
  ],

  // Personal Memory & Preferences Store
  memories: [
    {
      id: 'mem-1',
      category: 'Identity',
      key: 'User Designation',
      value: 'Tony Stark (Administrator)',
      updatedAt: '2026-09-01'
    },
    {
      id: 'mem-2',
      category: 'Communication',
      key: 'Tone & Persona',
      value: 'Calm, intelligent, respectful, British assistant style. Direct answers by default.',
      updatedAt: '2026-09-02'
    },
    {
      id: 'mem-3',
      category: 'Research',
      key: 'Primary Focus',
      value: 'Quantum computing, photonic chips, autonomous agent safety, energy storage.',
      updatedAt: '2026-09-05'
    },
    {
      id: 'mem-4',
      category: 'Trading Limits',
      key: 'Max Loss Limit',
      value: '2.0% daily maximum loss; paper trading only until explicitly cleared.',
      updatedAt: '2026-09-06'
    }
  ],

  // Integrations & Provider Connections
  integrations: [
    {
      id: 'int-1',
      name: 'Google Gemini Pro / Flash AI',
      category: 'Model Gateway',
      status: 'Connected (Demo)',
      icon: 'psychology'
    },
    {
      id: 'int-2',
      name: 'Web & News Search Provider',
      category: 'Research Engine',
      status: 'Demo Mode',
      icon: 'travel_explore'
    },
    {
      id: 'int-3',
      name: 'Market Data Provider',
      category: 'Financial Telemetry',
      status: 'Simulated Feed',
      icon: 'monitoring'
    },
    {
      id: 'int-4',
      name: 'Broker API Gateway',
      category: 'Trading Connection',
      status: 'Disabled (Read-Only Mode)',
      icon: 'account_balance'
    },
    {
      id: 'int-5',
      name: 'Smart Home Hub',
      category: 'IoT & Automation',
      status: 'Local Bridge Active',
      icon: 'home'
    }
  ]
};

class Store {
  constructor() {
    this.state = this.loadState();
    this.subscribers = new Set();
  }

  loadState() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (e) {
      console.warn('Failed to load persisted state from localStorage:', e);
    }
    return JSON.parse(JSON.stringify(DEFAULT_STATE));
  }

  saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.state));
    } catch (e) {
      console.warn('Failed to save state to localStorage:', e);
    }
  }

  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  notify(changedKeys = []) {
    this.saveState();
    this.subscribers.forEach(cb => cb(this.state, changedKeys));
  }

  // Navigation
  navigate(screenId) {
    if (this.state.activeScreen === screenId) return;
    this.state.navigationHistory.push(screenId);
    this.state.activeScreen = screenId;
    this.notify(['activeScreen']);
  }

  goBack() {
    if (this.state.navigationHistory.length > 1) {
      this.state.navigationHistory.pop();
      this.state.activeScreen = this.state.navigationHistory[this.state.navigationHistory.length - 1];
      this.notify(['activeScreen']);
      return true;
    }
    return false;
  }

  setAssistantState(state) {
    this.state.assistantState = state;
    this.notify(['assistantState']);
  }

  // Chat Actions
  addMessage(sender, text, citations = null, uncertainty = null) {
    const newMsg = {
      id: 'msg-' + Date.now(),
      sender,
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      citations,
      uncertainty
    };
    this.state.chatMessages.push(newMsg);
    this.notify(['chatMessages']);
    return newMsg;
  }

  clearChat() {
    this.state.chatMessages = [];
    this.notify(['chatMessages']);
  }

  // Task Actions
  addTask(title, description, priority = 'medium', category = 'general', dueDate = 'Tomorrow') {
    const newTask = {
      id: 'task-' + Date.now(),
      title,
      description,
      priority,
      category,
      status: 'active',
      progress: 0,
      dueDate,
      createdAt: new Date().toISOString().split('T')[0]
    };
    this.state.tasks.unshift(newTask);
    this.notify(['tasks']);
    return newTask;
  }

  toggleTaskStatus(taskId) {
    const task = this.state.tasks.find(t => t.id === taskId);
    if (task) {
      if (task.status === 'completed') {
        task.status = 'active';
        task.progress = 50;
      } else {
        task.status = 'completed';
        task.progress = 100;
      }
      this.notify(['tasks']);
    }
  }

  deleteTask(taskId) {
    this.state.tasks = this.state.tasks.filter(t => t.id !== taskId);
    this.notify(['tasks']);
  }

  // Markets Watchlist
  toggleWatchlist(symbol) {
    const item = this.state.markets.find(m => m.symbol === symbol);
    if (item) {
      item.isWatchlist = !item.isWatchlist;
      this.notify(['markets']);
    }
  }

  // Device Controls
  toggleDevice(deviceId) {
    const dev = this.state.devices.find(d => d.id === deviceId);
    if (dev) {
      dev.state = !dev.state;
      this.notify(['devices']);
    }
  }

  setDeviceValue(deviceId, val) {
    const dev = this.state.devices.find(d => d.id === deviceId);
    if (dev) {
      dev.value = Number(val);
      this.notify(['devices']);
    }
  }

  // Files Workspace
  addFile(name, type, content = '') {
    const newFile = {
      id: 'file-' + Date.now(),
      name,
      type,
      size: `${(content.length / 1024 + 0.5).toFixed(1)} KB`,
      modifiedAt: 'Just now',
      content
    };
    this.state.files.unshift(newFile);
    this.notify(['files']);
    return newFile;
  }

  deleteFile(fileId) {
    this.state.files = this.state.files.filter(f => f.id !== fileId);
    this.notify(['files']);
  }

  // Memory Actions
  addMemory(category, key, value) {
    const newMem = {
      id: 'mem-' + Date.now(),
      category,
      key,
      value,
      updatedAt: new Date().toISOString().split('T')[0]
    };
    this.state.memories.unshift(newMem);
    this.notify(['memories']);
    return newMem;
  }

  deleteMemory(memId) {
    this.state.memories = this.state.memories.filter(m => m.id !== memId);
    this.notify(['memories']);
  }

  clearAllMemory() {
    this.state.memories = [];
    this.notify(['memories']);
  }

  // Research Actions
  saveResearch(title, domain, date, summary, category) {
    const item = {
      id: 'res-' + Date.now(),
      title,
      domain,
      date,
      summary,
      category
    };
    this.state.savedResearch.unshift(item);
    this.notify(['savedResearch']);
  }

  // News Actions
  toggleNewsSaved(newsId) {
    const item = this.state.newsItems.find(n => n.id === newsId);
    if (item) {
      item.saved = !item.saved;
      this.notify(['newsItems']);
    }
  }

  markNewsRead(newsId) {
    const item = this.state.newsItems.find(n => n.id === newsId);
    if (item) {
      item.read = true;
      this.notify(['newsItems']);
    }
  }

  // Settings
  updateSetting(key, value) {
    this.state.settings[key] = value;
    this.notify(['settings']);
  }

  resetAllData() {
    localStorage.removeItem(STORAGE_KEY);
    this.state = JSON.parse(JSON.stringify(DEFAULT_STATE));
    this.notify(['all']);
  }
}

export const store = new Store();
