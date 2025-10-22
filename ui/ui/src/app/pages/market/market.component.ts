import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';

@Component({
  selector: 'app-market',
  standalone: true,
  imports: [
    CommonModule, 
    MatCardModule, 
    MatIconModule, 
    MatButtonModule, 
    MatProgressSpinnerModule,
    MatChipsModule
  ],
  templateUrl: './market.component.html',
  styleUrl: './market.component.scss'
})
export class MarketComponent {
  marketHighlights = [
    { 
      symbol: 'BTC/USD', 
      name: 'Bitcoin',
      price: '67,245.32',
      change: '+2.4%', 
      color: '#F7931A', 
      icon: 'currency_bitcoin',
      chartGradient: 'linear-gradient(135deg, #F7931A20, #F7931A05)'
    },
    { 
      symbol: 'AAPL', 
      name: 'Apple Inc.',
      price: '178.92',
      change: '-1.2%', 
      color: '#FF5252', 
      icon: 'phone_iphone',
      chartGradient: 'linear-gradient(135deg, #FF525220, #FF525205)'
    },
    { 
      symbol: 'TSLA', 
      name: 'Tesla Inc.',
      price: '251.88',
      change: '+4.8%', 
      color: '#00E676', 
      icon: 'electric_car',
      chartGradient: 'linear-gradient(135deg, #00E67620, #00E67605)'
    },
    { 
      symbol: 'ETH/USD', 
      name: 'Ethereum',
      price: '2,647.15',
      change: '+1.9%', 
      color: '#627EEA', 
      icon: 'diamond',
      chartGradient: 'linear-gradient(135deg, #627EEA20, #627EEA05)'
    },
    { 
      symbol: 'NVDA', 
      name: 'NVIDIA Corp.',
      price: '884.36',
      change: '+6.2%', 
      color: '#76B900', 
      icon: 'memory',
      chartGradient: 'linear-gradient(135deg, #76B90020, #76B90005)'
    },
    { 
      symbol: 'GOOGL', 
      name: 'Alphabet Inc.',
      price: '168.24',
      change: '+0.8%', 
      color: '#4285F4', 
      icon: 'search',
      chartGradient: 'linear-gradient(135deg, #4285F420, #4285F405)'
    }
  ];

  aiInsights = [
    {
      title: 'Bullish Momentum Detected',
      description: 'AI sentiment analysis shows strong bullish momentum in tech and crypto sectors with 89% confidence.',
      icon: 'trending_up',
      color: '#00E676',
      confidence: 89
    },
    {
      title: 'Volatility Alert',
      description: 'Expected volatility decrease in the next 24-48 hours based on historical patterns and market indicators.',
      icon: 'warning',
      color: '#FFC107',
      confidence: 76
    },
    {
      title: 'Institutional Activity',
      description: 'High institutional buying detected for BTC and TSLA with significant volume spikes in the last 4 hours.',
      icon: 'business',
      color: '#2196F3',
      confidence: 94
    },
    {
      title: 'Profit Booking Zone',
      description: 'AAPL showing overbought signals. AI recommends considering partial profit booking at current levels.',
      icon: 'savings',
      color: '#FF9800',
      confidence: 82
    }
  ];

  selectedAsset = 'BTC/USD';
  loading = false;

  refreshData() {
    this.loading = true;
    
    // Simulate API call
    setTimeout(() => {
      // Update prices with small random changes
      this.marketHighlights = this.marketHighlights.map(item => {
        const randomChange = (Math.random() - 0.5) * 2; // -1% to +1%
        const newPrice = parseFloat(item.price.replace(',', '')) * (1 + randomChange / 100);
        const changePercent = randomChange > 0 ? `+${randomChange.toFixed(1)}%` : `${randomChange.toFixed(1)}%`;
        const newColor = randomChange > 0 ? '#00E676' : '#FF5252';
        
        return {
          ...item,
          price: newPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
          change: changePercent,
          color: newColor
        };
      });
      
      this.loading = false;
    }, 2000);
  }
}

