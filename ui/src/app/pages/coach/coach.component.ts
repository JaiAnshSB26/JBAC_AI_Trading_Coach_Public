import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ApiService } from '../../services/api.service';

interface Message {
  sender: 'user' | 'ai' | 'guide';
  text: string;
  timestamp: Date;
  recommendation?: string;
}

@Component({
  selector: 'app-coach',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatTooltipModule
  ],
  templateUrl: './coach.component.html',
  styleUrl: './coach.component.scss'
})
export class CoachComponent implements OnInit, AfterViewChecked {
  @ViewChild('tradeAnalysisChat') tradeAnalysisChat!: ElementRef;
  @ViewChild('guideChat') guideChat!: ElementRef;

  // Trade Analysis Panel
  tradeMessages: Message[] = [];
  tradeInput = '';
  tradeAnalyzing = false;
  analyzingStatus = '';
  tradeMessagesDisplayCount = 10; // Show only last 10 messages initially
  
  // General Guide Panel
  guideMessages: Message[] = [];
  guideInput = '';
  guideTyping = false;
  guideMessagesDisplayCount = 10; // Show only last 10 messages initially

  private shouldScrollTrade = false;
  private shouldScrollGuide = false;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    // Clean up any old localStorage chat data (migration from previous version)
    this.cleanupOldStorage();
    
    // Load chat history from sessionStorage (cleared when browser closes)
    this.loadChatHistory();
  }

  ngAfterViewChecked() {
    if (this.shouldScrollTrade) {
      this.scrollToBottom(this.tradeAnalysisChat);
      this.shouldScrollTrade = false;
    }
    if (this.shouldScrollGuide) {
      this.scrollToBottom(this.guideChat);
      this.shouldScrollGuide = false;
    }
  }

  // Trade Analysis Methods
  onTradeKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendTradeAnalysis();
    }
  }

  sendTradeAnalysis(event?: Event) {
    if (event) {
      event.preventDefault();
    }

    if (!this.tradeInput.trim() || this.tradeAnalyzing) {
      return;
    }

    // Add user message
    const userMessage: Message = {
      sender: 'user',
      text: this.tradeInput,
      timestamp: new Date()
    };
    this.tradeMessages.push(userMessage);
    this.shouldScrollTrade = true;

    const userInput = this.tradeInput;
    this.tradeInput = '';
    this.tradeAnalyzing = true;

    // Analyzing with agentic workflow (Planner → Critic → Synthesizer)
    this.analyzingStatus = 'AI analyzing trade idea...';
    
    this.apiService.getTradeAnalysis({ idea: userInput }).subscribe({
      next: (response) => {
        // Add AI's synthesized response
        this.tradeMessages.push({
          sender: 'ai',
          text: response.response,
          timestamp: new Date(),
          recommendation: response.recommendation
        });
        this.shouldScrollTrade = true;

        this.tradeAnalyzing = false;
        this.analyzingStatus = '';
        this.saveChatHistory();
      },
      error: (error) => {
        console.error('Trade analysis error:', error);
        this.tradeMessages.push({
          sender: 'ai',
          text: 'Sorry, I encountered an error analyzing your trade idea. Please try again.',
          timestamp: new Date()
        });
        this.tradeAnalyzing = false;
        this.analyzingStatus = '';
        this.shouldScrollTrade = true;
      }
    });
  }

  useExamplePrompt(prompt: string) {
    this.tradeInput = prompt;
  }

  // General Guide Methods
  sendGuideQuestion() {
    if (!this.guideInput.trim() || this.guideTyping) {
      return;
    }

    // Add user message
    const userMessage: Message = {
      sender: 'user',
      text: this.guideInput,
      timestamp: new Date()
    };
    this.guideMessages.push(userMessage);
    this.shouldScrollGuide = true;

    const userQuestion = this.guideInput;
    this.guideInput = '';
    this.guideTyping = true;

    // Call educational coach endpoint
    this.apiService.coachUser({ 
      user_query: userQuestion,
      user_level: 'beginner',
      focus_area: 'general' 
    }).subscribe({
      next: (response) => {
        this.guideMessages.push({
          sender: 'guide',
          text: this.formatResponse(response.lesson || response.message || 'I can help you learn about trading concepts. What would you like to know?'),
          timestamp: new Date()
        });
        this.guideTyping = false;
        this.shouldScrollGuide = true;
        this.saveChatHistory();
      },
      error: (error) => {
        console.error('Guide error:', error);
        this.guideMessages.push({
          sender: 'guide',
          text: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date()
        });
        this.guideTyping = false;
        this.shouldScrollGuide = true;
      }
    });
  }

  useGuidePrompt(prompt: string) {
    this.guideInput = prompt;
  }

  clearGuideChat() {
    this.guideMessages = [];
    this.saveChatHistory();
  }

  // Load More Methods
  get displayedTradeMessages(): Message[] {
    const start = Math.max(0, this.tradeMessages.length - this.tradeMessagesDisplayCount);
    return this.tradeMessages.slice(start);
  }

  get displayedGuideMessages(): Message[] {
    const start = Math.max(0, this.guideMessages.length - this.guideMessagesDisplayCount);
    return this.guideMessages.slice(start);
  }

  get hasMoreTradeMessages(): boolean {
    return this.tradeMessages.length > this.tradeMessagesDisplayCount;
  }

  get hasMoreGuideMessages(): boolean {
    return this.guideMessages.length > this.guideMessagesDisplayCount;
  }

  loadMoreTradeMessages() {
    this.tradeMessagesDisplayCount += 10;
  }

  loadMoreGuideMessages() {
    this.guideMessagesDisplayCount += 10;
  }

  // Utility Methods
  private formatResponse(text: string): string {
    // Convert markdown-style formatting to HTML
    let formatted = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold
      .replace(/\*(.*?)\*/g, '<em>$1</em>')               // Italic
      .replace(/\n/g, '<br>')                              // Line breaks
      .replace(/- (.*?)(<br>|$)/g, '• $1$2');            // Bullet points
    
    return formatted;
  }

  private scrollToBottom(elementRef: ElementRef) {
    if (elementRef && elementRef.nativeElement) {
      try {
        elementRef.nativeElement.scrollTop = elementRef.nativeElement.scrollHeight;
      } catch (err) {
        console.error('Scroll error:', err);
      }
    }
  }

  private saveChatHistory() {
    try {
      // Use sessionStorage instead of localStorage - data is cleared when browser closes
      sessionStorage.setItem('tradeMessages', JSON.stringify(this.tradeMessages));
      sessionStorage.setItem('guideMessages', JSON.stringify(this.guideMessages));
    } catch (e) {
      console.error('Failed to save chat history:', e);
    }
  }

  private loadChatHistory() {
    try {
      // Load from sessionStorage - only persists during current browser session
      const tradeMsgs = sessionStorage.getItem('tradeMessages');
      const guideMsgs = sessionStorage.getItem('guideMessages');
      
      if (tradeMsgs) {
        this.tradeMessages = JSON.parse(tradeMsgs);
      }
      if (guideMsgs) {
        this.guideMessages = JSON.parse(guideMsgs);
      }
    } catch (e) {
      console.error('Failed to load chat history:', e);
    }
  }

  private cleanupOldStorage() {
    // Remove any old localStorage chat data from previous implementation
    try {
      localStorage.removeItem('tradeMessages');
      localStorage.removeItem('guideMessages');
    } catch (e) {
      console.error('Failed to cleanup old storage:', e);
    }
  }
}
