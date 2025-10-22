import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService } from '../../services/api.service';
import { MarketCacheService } from '../../services/market-cache.service';
import { AddSymbolDialogComponent } from './add-symbol-dialog.component';

interface MarketCard {
  symbol: string;
  name: string;
  price: string;
  change: string;
  color: string;
  icon: string;
  chartGradient: string;
}

@Component({
  selector: 'app-market',
  standalone: true,
  imports: [
    CommonModule, 
    MatCardModule, 
    MatIconModule, 
    MatButtonModule, 
    MatProgressSpinnerModule,
    MatDialogModule,
    MatSnackBarModule
  ],
  templateUrl: './market.component.html',
  styleUrl: './market.component.scss'
})
export class MarketComponent implements OnInit, OnDestroy {
  marketHighlights: MarketCard[] = [];
  activePortfolioId: string | null = null;
  activePortfolioName: string = '';
  
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

  selectedAsset = '';
  loading = false;
  loadingPortfolio = true;
  lastUpdate: Date | null = null;

  // Symbol mappings for API calls (display name -> API symbol)
  private symbolMap = new Map<string, string>();

  private refreshTimer: any;

  constructor(
    private apiService: ApiService,
    private marketCache: MarketCacheService,
    private router: Router,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit() {
    console.log('=== MarketComponent ngOnInit ===');
    
    // Always load from portfolio for authenticated users
    if (this.apiService.isAuthenticated()) {
      this.loadSymbolsFromActivePortfolio();
    } else {
      this.showLoginPrompt();
    }
    
    // Refresh data every 30 seconds (only fetches if needed)
    this.refreshTimer = setInterval(() => {
      if (this.marketHighlights.length > 0) {
        this.loadMarketData(false); // Don't force, use cache if valid
      }
    }, 30000);
  }

  ngOnDestroy() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
  }

  /**
   * Load tracked symbols from user's active portfolio
   */
  private loadSymbolsFromActivePortfolio() {
    console.log('Loading symbols from active portfolio...');
    this.loadingPortfolio = true;
    
    const userStr = localStorage.getItem('current_user');
    if (!userStr) {
      console.warn('No user data found');
      this.showLoginPrompt();
      this.loadingPortfolio = false;
      return;
    }

    const user = JSON.parse(userStr);
    this.activePortfolioId = user.default_portfolio_id;
    
    if (!this.activePortfolioId) {
      console.log('No default portfolio, prompting user to create one');
      this.showCreatePortfolioPrompt();
      this.loadingPortfolio = false;
      return;
    }

    // Fetch portfolio details
    this.apiService.getPortfolioDetail(this.activePortfolioId).subscribe({
      next: (response) => {
        const portfolio = response.portfolio;
        this.activePortfolioName = portfolio.portfolio_name;
        
        console.log(`Portfolio: ${portfolio.portfolio_name}`);
        console.log(`Tracked symbols:`, portfolio.tracked_symbols);
        
        if (!portfolio.tracked_symbols || portfolio.tracked_symbols.length === 0) {
          console.log('No tracked symbols in portfolio');
          this.showEmptyPortfolioState();
          this.loadingPortfolio = false;
          return;
        }

        // Build market cards from tracked symbols
        this.marketHighlights = [];
        this.symbolMap.clear();

        portfolio.tracked_symbols.forEach((apiSymbol: string) => {
          const displayName = this.getDisplayNameForSymbol(apiSymbol);
          const icon = this.getIconForSymbol(apiSymbol);
          const baseColor = this.getColorForSymbol(apiSymbol);
          
          this.marketHighlights.push({
            symbol: displayName,
            name: this.getFullNameForSymbol(apiSymbol),
            price: '...',
            change: '...', 
            color: baseColor,
            icon: icon,
            chartGradient: `linear-gradient(135deg, ${baseColor}20, ${baseColor}05)`
          });

          this.symbolMap.set(displayName, apiSymbol);
        });

        console.log(`Loaded ${this.marketHighlights.length} symbols from portfolio`);
        this.loadingPortfolio = false;
        
        // Load market data with caching
        this.loadMarketData(false);
      },
      error: (err) => {
        console.error('Failed to load portfolio:', err);
        this.snackBar.open('Failed to load portfolio symbols', 'Close', { duration: 3000 });
        this.loadingPortfolio = false;
      }
    });
  }

  /**
   * Load market data with session caching
   */
  private loadMarketData(forceRefresh: boolean = false) {
    if (this.marketHighlights.length === 0) {
      return;
    }

    console.log(`Loading market data (force: ${forceRefresh})...`);
    this.loading = true;
    
    const symbolsToFetch: string[] = [];
    const cachedData = new Map<string, any>();

    // Check cache for each symbol
    this.marketHighlights.forEach(item => {
      const apiSymbol = this.symbolMap.get(item.symbol);
      if (!apiSymbol) return;

      if (!forceRefresh) {
        const cached = this.marketCache.get(apiSymbol);
        if (cached) {
          cachedData.set(apiSymbol, cached);
          console.log(`Using cached data for ${apiSymbol}`);
          return;
        }
      }

      symbolsToFetch.push(apiSymbol);
    });

    // If all data is cached, just update UI
    if (symbolsToFetch.length === 0) {
      console.log('All symbols cached, updating UI only');
      this.updateMarketCards(cachedData);
      this.loading = false;
      this.lastUpdate = new Date();
      return;
    }

    // Fetch missing symbols
    console.log(`Fetching ${symbolsToFetch.length} symbols from API:`, symbolsToFetch);
    
    this.apiService.getMultipleSymbols(symbolsToFetch, forceRefresh).subscribe({
      next: (dataMap) => {
        console.log(`Received data for ${dataMap.size} symbols`);
        
        // Cache the fetched data
        dataMap.forEach((data, symbol) => {
          this.marketCache.set(symbol, data);
        });

        // Merge with cached data
        cachedData.forEach((data, symbol) => {
          if (!dataMap.has(symbol)) {
            dataMap.set(symbol, data);
          }
        });

        this.updateMarketCards(dataMap);
        this.lastUpdate = new Date();
        this.loading = false;
      },
      error: (error) => {
        console.error('Failed to load market data:', error);
        this.snackBar.open('Failed to load market data', 'Retry', { duration: 3000 })
          .onAction().subscribe(() => this.loadMarketData(true));
        this.loading = false;
      }
    });
  }

  /**
   * Update market cards with fetched data
   */
  private updateMarketCards(dataMap: Map<string, any>) {
    this.marketHighlights = this.marketHighlights.map(item => {
      const apiSymbol = this.symbolMap.get(item.symbol);
      if (!apiSymbol) return item;

      const marketData = dataMap.get(apiSymbol);
      if (!marketData || !marketData.latest) return item;

      const latest = marketData.latest;
      const sample = marketData.sample || [];
      
      // Calculate price change
      const previousCandle = sample.length > 1 ? sample[sample.length - 2] : latest;
      const currentPrice = latest.close;
      const previousPrice = previousCandle.close;
      const changePercent = ((currentPrice - previousPrice) / previousPrice) * 100;
      
      const color = changePercent >= 0 ? '#00E676' : '#FF5252';
      const changeText = changePercent >= 0 
        ? `+${changePercent.toFixed(2)}%` 
        : `${changePercent.toFixed(2)}%`;
      
      const formattedPrice = currentPrice.toLocaleString('en-US', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      });

      return {
        ...item,
        price: formattedPrice,
        change: changeText,
        color: color
      };
    });
  }

  /**
   * Manual refresh button handler
   */
  refreshData() {
    console.log('Manual refresh - invalidating cache');
    this.marketCache.clearAll();
    this.loadMarketData(true);
  }

  /**
   * Open add symbol dialog
   */
  openAddSymbolDialog() {
    if (!this.activePortfolioId) {
      this.snackBar.open('Please create a portfolio first', 'Go to Dashboard', { duration: 3000 })
        .onAction().subscribe(() => this.router.navigate(['/dashboard']));
      return;
    }

    const dialogRef = this.dialog.open(AddSymbolDialogComponent, {
      width: '500px',
      panelClass: 'add-symbol-dialog'
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result && result.symbol) {
        this.addSymbol(result.symbol);
      }
    });
  }

  /**
   * Add a new symbol to portfolio
   */
  private addSymbol(symbol: string) {
    // Check if already exists
    const apiSymbol = symbol.toUpperCase();
    const exists = Array.from(this.symbolMap.values()).some(s => 
      s.toUpperCase() === apiSymbol
    );

    if (exists) {
      this.snackBar.open('Symbol already tracked in portfolio', 'Close', { duration: 3000 });
      return;
    }

    // Validate symbol first
    this.loading = true;
    this.apiService.getMarketData(symbol).subscribe({
      next: () => {
        // Valid symbol, add to portfolio
        if (!this.activePortfolioId) {
          this.loading = false;
          return;
        }

        this.apiService.addTrackedSymbol(this.activePortfolioId, symbol).subscribe({
          next: () => {
            console.log(`Added ${symbol} to portfolio`);
            this.snackBar.open(`Added ${symbol} to ${this.activePortfolioName}`, 'Close', { duration: 3000 });
            
            // Reload symbols from portfolio
            this.loadSymbolsFromActivePortfolio();
          },
          error: (err) => {
            console.error('Failed to add symbol:', err);
            this.snackBar.open('Failed to add symbol to portfolio', 'Close', { duration: 3000 });
            this.loading = false;
          }
        });
      },
      error: () => {
        this.snackBar.open(`Invalid symbol: ${symbol}`, 'Close', { duration: 3000 });
        this.loading = false;
      }
    });
  }

  /**
   * Remove symbol from portfolio
   */
  removeSymbol(symbol: string) {
    if (!this.activePortfolioId) {
      return;
    }

    const apiSymbol = this.symbolMap.get(symbol);
    if (!apiSymbol) {
      return;
    }

    this.apiService.removeTrackedSymbol(this.activePortfolioId, apiSymbol).subscribe({
      next: () => {
        console.log(`Removed ${apiSymbol} from portfolio`);
        this.snackBar.open(`Removed ${symbol}`, 'Close', { duration: 2000 });
        
        // Clear cache for this symbol
        this.marketCache.clear(apiSymbol);
        
        // Reload symbols
        this.loadSymbolsFromActivePortfolio();
      },
      error: (err) => {
        console.error('Failed to remove symbol:', err);
        this.snackBar.open('Failed to remove symbol', 'Close', { duration: 3000 });
      }
    });
  }

  canRemoveSymbol(): boolean {
    return this.marketHighlights.length > 1;
  }

  /**
   * Helper methods for symbol display
   */
  private getDisplayNameForSymbol(apiSymbol: string): string {
    const upper = apiSymbol.toUpperCase();
    if (upper === 'BTC-USD') return 'BTC/USD';
    if (upper === 'ETH-USD') return 'ETH/USD';
    return apiSymbol;
  }

  private getFullNameForSymbol(apiSymbol: string): string {
    const upper = apiSymbol.toUpperCase();
    const nameMap: {[key: string]: string} = {
      'BTC-USD': 'Bitcoin',
      'ETH-USD': 'Ethereum',
      'AAPL': 'Apple Inc.',
      'TSLA': 'Tesla Inc.',
      'NVDA': 'NVIDIA Corp.',
      'GOOGL': 'Alphabet Inc.',
      'MSFT': 'Microsoft Corp.',
      'AMZN': 'Amazon.com Inc.',
      'META': 'Meta Platforms Inc.'
    };
    return nameMap[upper] || apiSymbol;
  }

  private getColorForSymbol(apiSymbol: string): string {
    const upper = apiSymbol.toUpperCase();
    if (upper.includes('BTC')) return '#F7931A';
    if (upper.includes('ETH')) return '#627EEA';
    return '#999';
  }

  private getIconForSymbol(symbol: string): string {
    const symbolUpper = symbol.toUpperCase();
    
    // Crypto icons
    if (symbolUpper.includes('BTC')) return 'currency_bitcoin';
    if (symbolUpper.includes('ETH')) return 'diamond';
    if (symbolUpper.includes('SOL')) return 'wb_sunny';
    if (symbolUpper.includes('ADA')) return 'account_balance_wallet';
    
    // Stock icons
    if (['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN'].includes(symbolUpper)) return 'computer';
    if (['TSLA', 'F', 'GM'].includes(symbolUpper)) return 'electric_car';
    if (['NVDA', 'AMD', 'INTC'].includes(symbolUpper)) return 'memory';
    if (['JPM', 'BAC', 'GS'].includes(symbolUpper)) return 'account_balance';
    
    return 'show_chart';
  }

  /**
   * Empty state handlers
   */
  private showLoginPrompt() {
    this.loadingPortfolio = false;
    this.snackBar.open('Please login to view market data', 'Login', { duration: 5000 })
      .onAction().subscribe(() => this.router.navigate(['/login']));
  }

  private showCreatePortfolioPrompt() {
    this.loadingPortfolio = false;
    this.snackBar.open('Create a portfolio to start tracking symbols', 'Go to Dashboard', { duration: 5000 })
      .onAction().subscribe(() => this.router.navigate(['/dashboard']));
  }

  private showEmptyPortfolioState() {
    this.loadingPortfolio = false;
    // Show empty state in template
  }
}

