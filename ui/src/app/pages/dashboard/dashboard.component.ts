import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { PortfolioSelectorComponent } from '../../components/portfolio-selector/portfolio-selector.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, MatCardModule, MatIconModule, MatButtonModule, MatChipsModule, PortfolioSelectorComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  currentTime: string = '';
  
  features = [
    {
      icon: 'visibility',
      title: 'Market Watch',
      description: 'Track real-time prices across multiple exchanges',
      color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      route: '/market'
    },
    {
      icon: 'psychology',
      title: 'AI Coach',
      description: 'Get personalized trading insights and analysis',
      color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      route: '/coach'
    },
    {
      icon: 'account_balance',
      title: 'Paper Trading',
      description: 'Practice trading with virtual funds',
      color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      route: '/trades'
    }
  ];

  ngOnInit() {
    this.updateTime();
    setInterval(() => this.updateTime(), 1000);
  }

  updateTime() {
    const now = new Date();
    this.currentTime = now.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  }
}