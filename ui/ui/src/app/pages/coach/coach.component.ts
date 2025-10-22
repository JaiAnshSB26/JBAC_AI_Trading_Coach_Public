import { Component, ViewChild, ElementRef, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FormsModule } from '@angular/forms';

interface Message {
  sender: 'ai' | 'user';
  text: string;
  timestamp: Date;
  confidence?: number;
}

interface Analysis {
  title: string;
  description: string;
  icon: string;
  color: string;
  confidence: number;
}

interface Insight {
  title: string;
  description: string;
  time: string;
  type: 'success' | 'warning' | 'info';
}

interface Metric {
  label: string;
  value: string;
  change: number;
  color: string;
}

@Component({
  selector: 'app-coach',
  standalone: true,
  imports: [
    CommonModule, 
    MatCardModule, 
    MatIconModule, 
    MatButtonModule, 
    MatFormFieldModule,
    MatInputModule,
    MatChipsModule,
    MatTooltipModule,
    FormsModule
  ],
  templateUrl: './coach.component.html',
  styleUrl: './coach.component.scss'
})
export class CoachComponent implements OnInit {
  @ViewChild('chatContainer') chatContainer!: ElementRef;
  @ViewChild('messageInput') messageInput!: ElementRef;

  messages: Message[] = [
    { 
      sender: 'ai', 
      text: 'Hello! I\'m your AI Trading Coach. I\'ve analyzed your recent performance and I\'m ready to help you improve your trading strategies. What would you like to discuss today?', 
      timestamp: new Date(Date.now() - 300000),
      confidence: 95
    },
    { 
      sender: 'user', 
      text: 'Can you analyze my last 5 trades and give me feedback?', 
      timestamp: new Date(Date.now() - 240000)
    },
    { 
      sender: 'ai', 
      text: 'I\'ve analyzed your last 5 trades. Your risk management has improved significantly - you\'re maintaining proper stop-losses in 4 out of 5 trades. However, I noticed you\'re entering positions slightly early. Consider waiting for stronger confirmation signals.', 
      timestamp: new Date(Date.now() - 180000),
      confidence: 88
    }
  ];

  userMessage = '';
  isTyping = false;
  Math = Math;

  quickSuggestions = [
    'Analyze my portfolio',
    'Market outlook today',
    'Risk management tips',
    'Best entry strategies'
  ];

  liveAnalysis: Analysis[] = [
    {
      title: 'Market Sentiment',
      description: 'Currently bullish with strong momentum in tech sector',
      icon: 'trending_up',
      color: '#00e676',
      confidence: 82
    },
    {
      title: 'Risk Level',
      description: 'Moderate risk detected in current positions',
      icon: 'warning',
      color: '#ffc107',
      confidence: 76
    },
    {
      title: 'Opportunity Score',
      description: 'High probability setups available in crypto',
      icon: 'stars',
      color: '#2196f3',
      confidence: 91
    }
  ];

  recentInsights: Insight[] = [
    {
      title: 'Entry Timing Improved',
      description: 'Your average entry timing has improved by 15% this week',
      time: '2 hours ago',
      type: 'success'
    },
    {
      title: 'Portfolio Diversification',
      description: 'Consider reducing exposure to tech sector (currently 65%)',
      time: '4 hours ago',
      type: 'warning'
    },
    {
      title: 'AI Strategy Update',
      description: 'New momentum indicators added to your strategy',
      time: '1 day ago',
      type: 'info'
    }
  ];

  performanceMetrics: Metric[] = [
    {
      label: 'Win Rate',
      value: '72%',
      change: 8,
      color: '#00e676'
    },
    {
      label: 'Avg. Return',
      value: '4.2%',
      change: 12,
      color: '#00e676'
    },
    {
      label: 'Risk Score',
      value: '3.8/10',
      change: -15,
      color: '#00e676'
    },
    {
      label: 'Consistency',
      value: '89%',
      change: 5,
      color: '#00e676'
    }
  ];

  ngOnInit() {
    // Auto-scroll to bottom on init
    setTimeout(() => this.scrollToBottom(), 100);
  }

  sendMessage() {
    if (!this.userMessage.trim() || this.isTyping) return;

    // Add user message
    this.messages.push({
      sender: 'user',
      text: this.userMessage.trim(),
      timestamp: new Date()
    });

    const userQuery = this.userMessage.trim();
    this.userMessage = '';
    this.isTyping = true;

    // Scroll to bottom
    setTimeout(() => this.scrollToBottom(), 100);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = this.generateAIResponse(userQuery);
      this.messages.push({
        sender: 'ai',
        text: aiResponse.text,
        timestamp: new Date(),
        confidence: aiResponse.confidence
      });
      this.isTyping = false;
      setTimeout(() => this.scrollToBottom(), 100);
    }, 1500 + Math.random() * 1000);
  }

  generateAIResponse(query: string): { text: string; confidence: number } {
    const responses = [
      {
        keywords: ['analyze', 'portfolio', 'performance'],
        text: 'Based on your portfolio analysis, you have a well-diversified mix with 60% stocks, 25% crypto, and 15% bonds. Your recent performance shows a 12% gain this month. I recommend reducing your crypto exposure slightly as it\'s currently overweight.',
        confidence: 92
      },
      {
        keywords: ['market', 'outlook', 'today', 'trend'],
        text: 'Today\'s market outlook is cautiously optimistic. The S&P 500 is showing bullish momentum, but watch for resistance at 4,400. Crypto markets are volatile - BTC is testing the 67k resistance level. Consider taking partial profits if you\'re long.',
        confidence: 85
      },
      {
        keywords: ['risk', 'management', 'stop', 'loss'],
        text: 'Excellent question! For optimal risk management, I recommend: 1) Never risk more than 2% per trade, 2) Use trailing stops for winning positions, 3) Diversify across sectors, 4) Set position sizes based on volatility. Your current risk score is improving!',
        confidence: 96
      },
      {
        keywords: ['entry', 'strategy', 'signals', 'timing'],
        text: 'For better entry timing, wait for confluence of signals: 1) Price above 20 EMA, 2) RSI between 40-60, 3) Volume confirmation, 4) Support/resistance levels. Your recent entries have been 85% accurate using this approach.',
        confidence: 89
      }
    ];

    const matchedResponse = responses.find(response => 
      response.keywords.some(keyword => 
        query.toLowerCase().includes(keyword.toLowerCase())
      )
    );

    if (matchedResponse) {
      return matchedResponse;
    }

    // Default responses
    const defaultResponses = [
      {
        text: 'That\'s an interesting question. Based on your trading history and current market conditions, I\'d recommend focusing on your risk management strategy. Your recent trades show good discipline, but there\'s always room for improvement.',
        confidence: 78
      },
      {
        text: 'I understand your concern. Let me analyze this in the context of your trading goals. Your performance metrics indicate you\'re on the right track, but consider diversifying your strategies for better risk-adjusted returns.',
        confidence: 82
      },
      {
        text: 'Great observation! This aligns with what I\'ve noticed in your trading patterns. I suggest we focus on backtesting this approach with historical data to validate the strategy before implementing it with real capital.',
        confidence: 87
      }
    ];

    return defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
  }

  selectSuggestion(suggestion: string) {
    this.userMessage = suggestion;
    this.sendMessage();
  }

  handleEnterKey(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  scrollToBottom() {
    if (this.chatContainer) {
      const element = this.chatContainer.nativeElement;
      element.scrollTop = element.scrollHeight;
    }
  }

  getConfidenceIcon(confidence: number | undefined): string {
    if (!confidence) return 'help_outline';
    if (confidence >= 90) return 'sentiment_very_satisfied';
    if (confidence >= 70) return 'sentiment_satisfied';
    if (confidence >= 50) return 'sentiment_neutral';
    return 'sentiment_dissatisfied';
  }

  clearChat() {
    this.messages = [
      { 
        sender: 'ai', 
        text: 'Chat cleared! How can I help you with your trading today?', 
        timestamp: new Date(),
        confidence: 95
      }
    ];
  }

  exportChat() {
    const chatData = this.messages.map(msg => ({
      sender: msg.sender,
      text: msg.text,
      timestamp: msg.timestamp.toISOString()
    }));
    
    const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trading-coach-chat-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  generateReport() {
    alert('Generating detailed performance report...');
  }

  analyzePortfolio() {
    alert('Starting portfolio analysis...');
  }

  getMarketInsights() {
    alert('Fetching latest market insights...');
  }

  scheduleSession() {
    alert('Opening session scheduler...');
  }
}

