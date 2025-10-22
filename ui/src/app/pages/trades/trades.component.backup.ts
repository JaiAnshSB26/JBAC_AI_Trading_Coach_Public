import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { FormsModule } from '@angular/forms';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatButtonToggleModule } from '@angular/material/button-toggle';

interface Trade {
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  orderType: 'market' | 'limit' | 'stop';
}

interface TradeHistory {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  total: number;
  time: Date;
  status: 'filled' | 'pending' | 'cancelled';
  orderType: string;
}

interface Position {
  symbol: string;
  quantity: number;
  avgCost: number;
  currentPrice: number;
  currentValue: number;
  pnl: number;
  percentChange: number;
}

interface SymbolSuggestion {
  symbol: string;
  name: string;
  price: number;
}

interface CurrentPrice {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  lastUpdate: Date;
}

@Component({
  selector: 'app-trades',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatInputModule,
    MatButtonModule,
    FormsModule,
    MatSelectModule,
    MatIconModule,
    MatChipsModule,
    MatButtonToggleModule
  ],
  templateUrl: './trades.component.html',
  styleUrl: './trades.component.scss'
})
export class TradesComponent implements OnInit {
  // Trading form data
  trade: Trade = { 
    symbol: '', 
    side: 'buy', 
    quantity: 1, 
    price: 0,
    orderType: 'market'
  };

  // Portfolio data
  portfolioValue = 100000;
  totalPnL = 2450.75;
  dailyPnL = 385.20;
  availableBalance = 50000;
  estimatedTotal = 0;

  // Symbol search
  symbolSuggestions: SymbolSuggestion[] = [];
  currentPrice: CurrentPrice | null = null;

  // Trade history and positions
  tradesHistory: TradeHistory[] = [];
  openPositions: Position[] = [];
  
  // Filters and settings
  historyFilter = 'all';
  analyticsTimeRange = '1M';

  // Analytics
  winRate = 68.5;
  totalReturn = 12.8;
  totalReturnAmount = 12800;
  avgTradeSize = 2450;
  totalTrades = 45;
  sharpeRatio = 1.85;

  // Sample data
  private sampleSymbols: SymbolSuggestion[] = [
    { symbol: 'AAPL', name: 'Apple Inc.', price: 175.50 },
    { symbol: 'TSLA', name: 'Tesla Inc.', price: 245.80 },
    { symbol: 'MSFT', name: 'Microsoft Corp.', price: 380.25 },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 140.75 },
    { symbol: 'AMZN', name: 'Amazon.com Inc.', price: 145.90 },
    { symbol: 'NVDA', name: 'NVIDIA Corp.', price: 485.20 },
    { symbol: 'META', name: 'Meta Platforms Inc.', price: 325.15 },
    { symbol: 'BTC-USD', name: 'Bitcoin', price: 45250.00 },
    { symbol: 'ETH-USD', name: 'Ethereum', price: 2850.75 }
  ];

  ngOnInit() {
    this.loadSampleData();
    this.calculateTotal();
  }

  // Symbol search functionality
  onSymbolSearch(event: any) {
    const query = event.target.value.toUpperCase();
    if (query.length >= 1) {
      this.symbolSuggestions = this.sampleSymbols.filter(symbol => 
        symbol.symbol.includes(query) || symbol.name.toUpperCase().includes(query)
      ).slice(0, 5);
    } else {
      this.symbolSuggestions = [];
    }
  }

  selectSymbol(suggestion: SymbolSuggestion) {
    this.trade.symbol = suggestion.symbol;
    this.symbolSuggestions = [];
    this.updateCurrentPrice(suggestion);
  }

  updateCurrentPrice(suggestion: SymbolSuggestion) {
    // Simulate real-time price updates
    const changePercent = (Math.random() - 0.5) * 4; // -2% to +2%
    const change = suggestion.price * (changePercent / 100);
    
    this.currentPrice = {
      symbol: suggestion.symbol,
      price: suggestion.price + change,
      change: change,
      changePercent: changePercent,
      lastUpdate: new Date()
    };

    if (this.trade.orderType === 'market') {
      this.trade.price = this.currentPrice.price;
    }
    this.calculateTotal();
  }

  // Trading functions
  calculateTotal() {
    if (this.trade.orderType === 'market' && this.currentPrice) {
      this.estimatedTotal = this.trade.quantity * this.currentPrice.price;
    } else {
      this.estimatedTotal = this.trade.quantity * this.trade.price;
    }
  }

  canExecuteTrade(): boolean {
    return !!(
      this.trade.symbol && 
      this.trade.quantity > 0 && 
      (this.trade.orderType === 'market' || this.trade.price > 0) &&
      (this.trade.side === 'sell' || this.estimatedTotal <= this.availableBalance)
    );
  }

  executeTrade() {
    if (!this.canExecuteTrade()) return;

    const tradePrice = this.trade.orderType === 'market' && this.currentPrice 
      ? this.currentPrice.price 
      : this.trade.price;

    const total = this.trade.quantity * tradePrice;
    
    const newTrade: TradeHistory = {
      id: Date.now().toString(),
      symbol: this.trade.symbol,
      side: this.trade.side,
      quantity: this.trade.quantity,
      price: tradePrice,
      total: total,
      time: new Date(),
      status: this.trade.orderType === 'market' ? 'filled' : 'pending',
      orderType: this.trade.orderType
    };

    this.tradesHistory.unshift(newTrade);
    this.updatePositions(newTrade);
    this.updatePortfolioValue(newTrade);

    // Reset form
    this.trade = { 
      symbol: '', 
      side: 'buy', 
      quantity: 1, 
      price: 0,
      orderType: 'market'
    };
    this.currentPrice = null;
    this.estimatedTotal = 0;
  }

  updatePositions(trade: TradeHistory) {
    const existingPosition = this.openPositions.find(p => p.symbol === trade.symbol);
    
    if (existingPosition) {
      if (trade.side === 'buy') {
        const totalCost = (existingPosition.quantity * existingPosition.avgCost) + trade.total;
        const totalQuantity = existingPosition.quantity + trade.quantity;
        existingPosition.avgCost = totalCost / totalQuantity;
        existingPosition.quantity = totalQuantity;
      } else {
        existingPosition.quantity -= trade.quantity;
        if (existingPosition.quantity <= 0) {
          this.openPositions = this.openPositions.filter(p => p.symbol !== trade.symbol);
          return;
        }
      }
    } else if (trade.side === 'buy') {
      const newPosition: Position = {
        symbol: trade.symbol,
        quantity: trade.quantity,
        avgCost: trade.price,
        currentPrice: trade.price,
        currentValue: trade.total,
        pnl: 0,
        percentChange: 0
      };
      this.openPositions.push(newPosition);
    }

    // Update current values and P&L
    this.updatePositionValues();
  }

  updatePositionValues() {
    this.openPositions.forEach(position => {
      // Simulate price changes
      const priceChange = (Math.random() - 0.5) * 0.02; // -1% to +1%
      position.currentPrice = position.avgCost * (1 + priceChange);
      position.currentValue = position.quantity * position.currentPrice;
      position.pnl = position.currentValue - (position.quantity * position.avgCost);
      position.percentChange = ((position.currentPrice - position.avgCost) / position.avgCost) * 100;
    });
  }

  updatePortfolioValue(trade: TradeHistory) {
    if (trade.side === 'buy') {
      this.availableBalance -= trade.total;
    } else {
      this.availableBalance += trade.total;
    }
    
    this.portfolioValue = this.availableBalance + this.openPositions.reduce((sum, pos) => sum + pos.currentValue, 0);
  }

  // Filter functions
  get filteredTradesHistory(): TradeHistory[] {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

    switch (this.historyFilter) {
      case 'today':
        return this.tradesHistory.filter(trade => trade.time >= today);
      case 'week':
        return this.tradesHistory.filter(trade => trade.time >= weekAgo);
      case 'month':
        return this.tradesHistory.filter(trade => trade.time >= monthAgo);
      default:
        return this.tradesHistory;
    }
  }

  // Quick action functions
  closeAllPositions() {
    this.openPositions.forEach(position => {
      const closeOrder: TradeHistory = {
        id: Date.now().toString() + Math.random(),
        symbol: position.symbol,
        side: 'sell',
        quantity: position.quantity,
        price: position.currentPrice,
        total: position.currentValue,
        time: new Date(),
        status: 'filled',
        orderType: 'market'
      };
      this.tradesHistory.unshift(closeOrder);
      this.availableBalance += closeOrder.total;
    });
    this.openPositions = [];
    this.portfolioValue = this.availableBalance;
  }

  setStopLoss() {
    // Implementation for setting stop loss orders
    console.log('Setting stop loss orders...');
  }

  viewAnalytics() {
    // Implementation for detailed analytics view
    console.log('Opening analytics view...');
  }

  exportTrades() {
    const csvContent = this.generateCSV();
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'trade_history.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  }

  private generateCSV(): string {
    const headers = ['Time', 'Symbol', 'Side', 'Quantity', 'Price', 'Total', 'Status'];
    const rows = this.tradesHistory.map(trade => [
      trade.time.toISOString(),
      trade.symbol,
      trade.side,
      trade.quantity.toString(),
      trade.price.toString(),
      trade.total.toString(),
      trade.status
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }

  // Load sample data for demonstration
  private loadSampleData() {
    // Sample trades
    const sampleTrades: TradeHistory[] = [
      {
        id: '1',
        symbol: 'AAPL',
        side: 'buy',
        quantity: 10,
        price: 175.50,
        total: 1755.00,
        time: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        status: 'filled',
        orderType: 'market'
      },
      {
        id: '2',
        symbol: 'TSLA',
        side: 'buy',
        quantity: 5,
        price: 245.80,
        total: 1229.00,
        time: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4 hours ago
        status: 'filled',
        orderType: 'limit'
      }
    ];

    this.tradesHistory = sampleTrades;

    // Sample positions
    this.openPositions = [
      {
        symbol: 'AAPL',
        quantity: 10,
        avgCost: 175.50,
        currentPrice: 177.25,
        currentValue: 1772.50,
        pnl: 17.50,
        percentChange: 1.00
      },
      {
        symbol: 'TSLA',
        quantity: 5,
        avgCost: 245.80,
        currentPrice: 248.90,
        currentValue: 1244.50,
        pnl: 15.50,
        percentChange: 1.26
      }
    ];

    this.availableBalance = 96016.00; // 100k - trades
    this.portfolioValue = this.availableBalance + this.openPositions.reduce((sum, pos) => sum + pos.currentValue, 0);
  }
}

