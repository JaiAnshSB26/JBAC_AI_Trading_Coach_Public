import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, MatButtonModule, MatProgressBarModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent {
  stats = [
    { icon: 'psychology', label: 'AI Confidence', value: '87%', color: '#00D084' },
    { icon: 'trending_up', label: 'Win Rate', value: '72%', color: '#00BFA5' },
    { icon: 'bar_chart', label: 'Total Trades', value: '145', color: '#4FC3F7' },
    { icon: 'school', label: 'Learning Progress', value: '65%', color: '#FFD54F' },
  ];

  insights = [
    'Your average win rate has increased by 8% this week 📈',
    'AI model confidence suggests focusing on momentum strategies today ⚡',
    'You’ve been most accurate in predicting BTC trends — keep it up 💪'
  ];
}

