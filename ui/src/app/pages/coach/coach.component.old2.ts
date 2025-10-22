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
import { ApiService } from '../../services/api.service';

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

  messages: Message[] = [];
  userMessage = '';
  isTyping = false;
  Math = Math;

  // Default user ID - in production this would come from auth
  private userId = 'demo_user';
  private userGoal = 'Learn trading strategies and improve performance';
  private riskLevel = 'medium';
  private symbols = ['AAPL', 'MSFT', 'TSLA', 'GOOGL'];

  quickSuggestions = [
    'Analyze my portfolio',
    'Market outlook today',
    'Risk management tips',
    'Best entry strategies'
  ];

  liveAnalysis: Analysis[] = [];
  recentInsights: Insight[] = [];
  performanceMetrics: Metric[] = [];

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadInitialData();
  }

  loadInitialData() {
    // Add welcome message
    this.messages.push({
      sender: 'ai',
      text: 'Hello! I\'m your AI Trading Coach powered by real LLM agents. I can help you analyze your portfolio, critique trades, and create learning plans. What would you like to discuss today?',
      timestamp: new Date(),
      confidence: 95
    });

    // Load portfolio metrics
    this.loadPortfolioMetrics();
    
    // Auto-scroll to bottom
    setTimeout(() => this.scrollToBottom(), 100);
  }

  loadPortfolioMetrics() {
    this.apiService.getPortfolio(this.userId).subscribe({
      next: (data) => {
        this.updateMetrics(data);
        this.generateInsights(data);
        this.updateLiveAnalysis(data);
      },
      error: (error) => {
        console.log('Portfolio not found or error:', error);
        this.setDefaultMetrics();
      }
    });
  }

  updateMetrics(portfolioData: any) {
    const metrics = portfolioData.metrics || {};
    
    const winRate = metrics.win_rate || 0;
    const totalPnl = metrics.total_pnl || 0;
    const avgReturn = totalPnl > 0 ? (totalPnl / metrics.total_value * 100) : 0;
    
    // Calculate risk score (lower is better)
    const positionsCount = portfolioData.positions?.length || 0;
    const riskScore = positionsCount > 0 ? Math.min(10, 10 - (winRate / 10)) : 5;
    
    this.performanceMetrics = [
      {
        label: 'Win Rate',
        value: `${winRate.toFixed(0)}%`,
        change: winRate > 60 ? 5 : -5,
        color: winRate > 60 ? '#00e676' : '#ff5252'
      },
      {
        label: 'Total P&L',
        value: `$${totalPnl.toFixed(2)}`,
        change: totalPnl > 0 ? 10 : -10,
        color: totalPnl > 0 ? '#00e676' : '#ff5252'
      },
      {
        label: 'Risk Score',
        value: `${riskScore.toFixed(1)}/10`,
        change: riskScore < 5 ? 15 : -10,
        color: riskScore < 5 ? '#00e676' : '#ffc107'
      },
      {
        label: 'Active Positions',
        value: positionsCount.toString(),
        change: 0,
        color: '#2196f3'
      }
    ];
  }

  generateInsights(portfolioData: any) {
    const metrics = portfolioData.metrics || {};
    const insights: Insight[] = [];

    if (metrics.win_rate > 60) {
      insights.push({
        title: 'Strong Performance',
        description: `Your win rate of ${metrics.win_rate.toFixed(1)}% is above average`,
        time: 'just now',
        type: 'success'
      });
    }

    if (portfolioData.positions && portfolioData.positions.length > 5) {
      insights.push({
        title: 'Portfolio Diversification',
        description: 'Consider consolidating positions to reduce complexity',
        time: '1 hour ago',
        type: 'warning'
      });
    }

    if (metrics.total_trades === 0) {
      insights.push({
        title: 'Ready to Start',
        description: 'Execute your first paper trade to begin learning',
        time: 'just now',
        type: 'info'
      });
    }

    this.recentInsights = insights.length > 0 ? insights : [{
      title: 'AI Learning',
      description: 'Your AI coach is analyzing your trading patterns',
      time: 'ongoing',
      type: 'info'
    }];
  }

  updateLiveAnalysis(portfolioData: any) {
    const metrics = portfolioData.metrics || {};
    
    // Market sentiment (simplified for now)
    this.liveAnalysis = [
      {
        title: 'Portfolio Health',
        description: metrics.win_rate > 60 ? 'Strong performance across positions' : 'Focus on risk management',
        icon: 'trending_up',
        color: metrics.win_rate > 60 ? '#00e676' : '#ffc107',
        confidence: Math.min(95, 50 + (metrics.win_rate || 0) / 2)
      },
      {
        title: 'Risk Assessment',
        description: portfolioData.positions?.length > 5 ? 'High position count' : 'Moderate risk level',
        icon: 'warning',
        color: '#ffc107',
        confidence: 76
      },
      {
        title: 'Learning Progress',
        description: `${metrics.total_trades || 0} trades executed`,
        icon: 'school',
        color: '#2196f3',
        confidence: Math.min(90, (metrics.total_trades || 0) * 5)
      }
    ];
  }

  setDefaultMetrics() {
    this.performanceMetrics = [
      { label: 'Win Rate', value: 'N/A', change: 0, color: '#00e676' },
      { label: 'Total P&L', value: '$0.00', change: 0, color: '#00e676' },
      { label: 'Risk Score', value: 'N/A', change: 0, color: '#ffc107' },
      { label: 'Active Positions', value: '0', change: 0, color: '#2196f3' }
    ];
    
    this.recentInsights = [{
      title: 'Get Started',
      description: 'Initialize your portfolio to start trading',
      time: 'now',
      type: 'info'
    }];
    
    this.liveAnalysis = [{
      title: 'Ready to Learn',
      description: 'AI coach is ready to help you get started',
      icon: 'psychology',
      color: '#2196f3',
      confidence: 95
    }];
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

    // Call the AI coach API
    this.apiService.sendCoachMessage(this.userId, this.userGoal, userQuery, this.riskLevel, this.symbols).subscribe({
      next: (response) => {
        this.messages.push({
          sender: 'ai',
          text: response.answer || 'I apologize, but I couldn\'t generate a response. Please try again.',
          timestamp: new Date(),
          confidence: 85
        });
        this.isTyping = false;
        setTimeout(() => this.scrollToBottom(), 100);
      },
      error: (error) => {
        console.error('Coach API error:', error);
        this.messages.push({
          sender: 'ai',
          text: 'I\'m having trouble connecting to the AI service right now. Please check that the backend is running.',
          timestamp: new Date(),
          confidence: 50
        });
        this.isTyping = false;
        setTimeout(() => this.scrollToBottom(), 100);
      }
    });
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
    this.userMessage = 'Generate a detailed performance report for my trading activity';
    this.sendMessage();
  }

  analyzePortfolio() {
    this.userMessage = 'Analyze my current portfolio and provide recommendations';
    this.sendMessage();
  }

  getMarketInsights() {
    this.userMessage = 'What are the current market conditions and opportunities?';
    this.sendMessage();
  }

  scheduleSession() {
    this.userMessage = 'I want to schedule a learning session. What topics should we cover?';
    this.sendMessage();
  }
}
