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
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService } from '../../services/api.service';

interface Trade {
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  orderType: 'market' | 'limit' | 'stop';
}

interface TradeHistory {
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  time: string;
  total: number;
  status: string;
}

interface Position {
  symbol: string;
  quantity: number;
  avg_price: number;
  avgCost: number;  // Alias for template compatibility
  current_price: number;
  currentPrice: number;  // Alias for template compatibility
  value: number;
  currentValue: number;  // Alias for template compatibility
  pnl: number;
  pnl_percent: number;
  percentChange: number;  // Alias for template compatibility
}

interface SymbolSuggestion {
  symbol: string;
  name: string;
}

interface CurrentPrice {
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
    MatButtonToggleModule,
    MatSnackBarModule
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
  portfolioValue = 0;
  totalPnL = 0;
  dailyPnL = 0;
  availableBalance = 0;
  estimatedTotal = 0;

  // Symbol search
  symbolSuggestions: SymbolSuggestion[] = [];
  currentPrice: CurrentPrice | null = null;
  isLoadingPrice = false;

  // Trade history and positions
  tradesHistory: TradeHistory[] = [];
  openPositions: Position[] = [];
  
  // Filters and settings
  historyFilter = 'all';
  analyticsTimeRange = '1M';

  // Analytics
  winRate = 0;
  totalReturn = 0;
  totalReturnAmount = 0;
  avgTradeSize = 0;
  totalTrades = 0;
  sharpeRatio = 0;

  // Available symbols for trading
  popularSymbols = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'BTC-USD', 'ETH-USD'];
  showCustomInput = false;

  // Portfolio and user IDs
  private userId = 'demo_user';
  private activePortfolioId: string | null = null;
  private priceUpdateInterval: any;

  constructor(
    private apiService: ApiService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit() {
    // Get current user and active portfolio
    const userStr = localStorage.getItem('current_user');
    if (userStr) {
      const user = JSON.parse(userStr);
      this.userId = user.user_id;
      this.activePortfolioId = user.default_portfolio_id;
    }

    if (!this.activePortfolioId) {
      this.snackBar.open('Please create a portfolio first from the dashboard', 'Close', { duration: 5000 });
      return;
    }

    this.loadPortfolioData();
    
    // Update prices every 30 seconds
    this.priceUpdateInterval = setInterval(() => {
      if (this.trade.symbol) {
        this.updateCurrentPrice(this.trade.symbol);
      }
    }, 30000);
  }

  ngOnDestroy() {
    if (this.priceUpdateInterval) {
      clearInterval(this.priceUpdateInterval);
    }
  }

  loadPortfolioData() {
    if (!this.activePortfolioId) return;

    // Load portfolio details from DynamoDB
    this.apiService.getPortfolioDetail(this.activePortfolioId).subscribe({
      next: (data) => {
        const portfolio = data.portfolio;
        
        // Update portfolio display with DynamoDB data
        this.availableBalance = portfolio.current_balance || 0;
        this.portfolioValue = portfolio.total_value || 0;
        this.estimatedTotal = this.portfolioValue;
        
        // Update positions
        this.openPositions = (portfolio.positions || []).map((pos: any) => ({
          symbol: pos.symbol,
          quantity: pos.quantity,
          avg_price: pos.avg_cost,
          avgCost: pos.avg_cost,
          current_price: pos.current_price || pos.avg_cost,
          currentPrice: pos.current_price || pos.avg_cost,
          value: pos.current_value || (pos.quantity * pos.avg_cost),
          currentValue: pos.current_value || (pos.quantity * pos.avg_cost),
          pnl: pos.unrealized_pnl || 0,
          pnl_percent: pos.pnl_percent || 0,
          percentChange: pos.pnl_percent || 0
        }));
        
        // Load trade history
        this.loadTradeHistory();
      },
      error: (error) => {
        console.error('Failed to load portfolio:', error);
        this.snackBar.open('Failed to load portfolio data', 'Close', { duration: 5000 });
      }
    });
  }

  loadTradeHistory() {
    if (!this.activePortfolioId) return;

    this.apiService.getPortfolioTrades(this.activePortfolioId, undefined, 50).subscribe({
      next: (data) => {
        this.tradesHistory = (data.trades || []).map((trade: any) => ({
          symbol: trade.symbol,
          side: trade.side,
          quantity: trade.quantity,
          price: trade.price,
          time: new Date(trade.timestamp).toLocaleString(),
          total: trade.total_amount,
          status: trade.status
        }));
        
        // Calculate analytics
        this.calculateAnalytics();
      },
      error: (error) => {
        console.error('Failed to load trade history:', error);
      }
    });
  }

  calculateAnalytics() {
    this.totalTrades = this.tradesHistory.length;
    
    if (this.totalTrades === 0) return;
    
    // Calculate total return from current positions
    this.totalReturnAmount = this.openPositions.reduce((sum, pos) => sum + pos.pnl, 0);
    this.totalReturn = this.availableBalance > 0 ? (this.totalReturnAmount / this.availableBalance) * 100 : 0;
    
    // Calculate average trade size
    this.avgTradeSize = this.tradesHistory.reduce((sum, trade) => sum + trade.total, 0) / this.totalTrades;
    
    // Calculate win rate (simplified)
    const profitableTrades = this.openPositions.filter(pos => pos.pnl > 0).length;
    this.winRate = this.openPositions.length > 0 ? (profitableTrades / this.openPositions.length) * 100 : 0;
  }

  updatePortfolioDisplay(portfolioData: any) {
    const metrics = portfolioData.metrics || {};
    const state = portfolioData.state || {};
    
    this.availableBalance = state.cash || 0;
    this.portfolioValue = metrics.total_value || 0;
    this.totalPnL = metrics.total_pnl || 0;
    
    // Map positions from API format
    this.openPositions = (portfolioData.positions || []).map((pos: any) => ({
      symbol: pos.symbol,
      quantity: pos.quantity,
      avg_price: pos.avg_price,
      avgCost: pos.avg_price,  // Alias for template
      current_price: pos.current_price,
      currentPrice: pos.current_price,  // Alias for template
      value: pos.value,
      currentValue: pos.value,  // Alias for template
      pnl: pos.pnl,
      pnl_percent: pos.pnl_percent,
      percentChange: pos.pnl_percent  // Alias for template
    }));
    
    // Map trade history from API format
    this.tradesHistory = (state.history || []).map((trade: any) => ({
      symbol: trade.symbol,
      side: trade.side,
      quantity: trade.quantity,
      price: trade.price,
      time: trade.time,
      total: trade.quantity * trade.price,  // Calculate total
      status: 'filled'  // All historical trades are filled
    }));
    
    // Calculate analytics
    this.totalTrades = metrics.total_trades || 0;
    this.winRate = metrics.win_rate || 0;
    this.totalReturn = this.portfolioValue > 0 ? (this.totalPnL / this.portfolioValue * 100) : 0;
    this.totalReturnAmount = this.totalPnL;
    this.avgTradeSize = this.totalTrades > 0 ? (this.portfolioValue / this.totalTrades) : 0;
    
    // Calculate daily P&L (simplified - difference from last trade)
    if (this.tradesHistory.length > 0) {
      // For demo purposes, show a percentage of total P&L
      this.dailyPnL = this.totalPnL * 0.1;
    }
  }

  // Quick symbol selection
  selectQuickSymbol(symbol: string) {
    this.trade.symbol = symbol;
    this.updateCurrentPrice(symbol);
  }

  // Adjust quantity with +/- buttons
  adjustQuantity(delta: number) {
    this.trade.quantity = Math.max(1, this.trade.quantity + delta);
    this.calculateTotal();
  }

  updateCurrentPrice(symbol: string) {
    this.isLoadingPrice = true;
    this.apiService.getMarketData(symbol, '1d', '1h').subscribe({
      next: (data) => {
        if (data.latest && data.latest.close) {
          const currentPrice = data.latest.close;
          const previousPrice = data.sample && data.sample.length > 1 
            ? data.sample[data.sample.length - 2].close 
            : currentPrice;
          
          const change = currentPrice - previousPrice;
          const changePercent = (change / previousPrice) * 100;
          
          this.currentPrice = {
            price: currentPrice,
            change: change,
            changePercent: changePercent,
            lastUpdate: new Date()
          };
          
          if (this.trade.orderType === 'market') {
            this.trade.price = this.currentPrice.price;
          }
          this.calculateTotal();
        }
        this.isLoadingPrice = false;
      },
      error: (error) => {
        console.error('Failed to fetch price:', error);
        this.snackBar.open(`Failed to fetch price for ${symbol}`, 'Close', { duration: 3000 });
        this.isLoadingPrice = false;
      }
    });
  }

  // Trading functions
  calculateTotal() {
    if (this.trade.orderType === 'market' && this.currentPrice && this.currentPrice.price > 0) {
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
    if (!this.canExecuteTrade()) {
      this.snackBar.open('Invalid trade parameters or insufficient balance', 'Close', { duration: 3000 });
      return;
    }

    if (!this.activePortfolioId) {
      this.snackBar.open('Please select a portfolio first', 'Close', { duration: 3000 });
      return;
    }

    this.apiService.executeTradeInPortfolio(
      this.activePortfolioId, 
      this.trade.symbol, 
      this.trade.side, 
      this.trade.quantity, 
      this.trade.orderType
    ).subscribe({
      next: (response) => {
        const trade = response.trade;
        this.snackBar.open(
          `✓ ${this.trade.side.toUpperCase()} ${this.trade.quantity} ${this.trade.symbol} at $${trade.price.toFixed(2)}`, 
          'Close', 
          { duration: 5000 }
        );
        
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
        
        // Reload portfolio data
        this.loadPortfolioData();
      },
      error: (error) => {
        console.error('Trade execution failed:', error);
        this.snackBar.open(
          `Failed to execute trade: ${error.error?.detail || 'Unknown error'}`, 
          'Close', 
          { duration: 5000 }
        );
      }
    });
  }

  // Filter functions
  get filteredTradesHistory(): TradeHistory[] {
    // For now, return all trades
    // Could add date filtering based on historyFilter
    return this.tradesHistory;
  }

  // Quick action functions
  closeAllPositions() {
    if (this.openPositions.length === 0) {
      this.snackBar.open('No open positions to close', 'Close', { duration: 3000 });
      return;
    }

    let closedCount = 0;
    const closePromises = this.openPositions.map(position => {
      return new Promise((resolve) => {
        this.apiService.executeTrade(this.userId, position.symbol, 'sell', position.quantity).subscribe({
          next: () => {
            closedCount++;
            resolve(true);
          },
          error: (error) => {
            console.error(`Failed to close ${position.symbol}:`, error);
            resolve(false);
          }
        });
      });
    });

    Promise.all(closePromises).then(() => {
      this.snackBar.open(
        `Closed ${closedCount} of ${this.openPositions.length} positions`, 
        'Close', 
        { duration: 5000 }
      );
      this.loadPortfolioData();
    });
  }

  setStopLoss() {
    this.snackBar.open('Stop loss feature coming soon!', 'Close', { duration: 3000 });
  }

  viewAnalytics() {
    this.snackBar.open('Detailed analytics view coming soon!', 'Close', { duration: 3000 });
  }

  exportTrades() {
    const csvContent = this.generateCSV();
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trade_history_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    this.snackBar.open('Trade history exported', 'Close', { duration: 3000 });
  }

  private generateCSV(): string {
    const headers = ['Time', 'Symbol', 'Side', 'Quantity', 'Price'];
    const rows = this.tradesHistory.map(trade => [
      trade.time,
      trade.symbol,
      trade.side,
      trade.quantity.toString(),
      trade.price.toString()
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }
}
