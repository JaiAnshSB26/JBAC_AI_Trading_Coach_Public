import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, of, forkJoin } from 'rxjs';
import { catchError, map, retry, tap, shareReplay } from 'rxjs/operators';

/**
 * API Service for JBAC AI Trading Coach
 * Handles all communication with the FastAPI backend
 */
@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl: string;
  private marketDataCache = new Map<string, { data: any, timestamp: number }>();
  private pendingRequests = new Map<string, Observable<any>>();
  private cacheTimeout = 120000; // 2 minutes cache (increased to reduce API calls)
  private authToken: string | null = null;

  constructor(private http: HttpClient) {
    // Get API URL from environment or default to localhost
    this.apiUrl = this.getApiUrl();
    // Load auth token from localStorage
    this.authToken = localStorage.getItem('auth_token');
    
    // Log cache info on initialization
    console.log('✅ API Service initialized with 2-minute market data cache');
  }

  private getApiUrl(): string {
    // Check if we're in production or development
    const hostname = window.location.hostname;
    
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      // Development: FastAPI backend on port 8000
      return 'http://localhost:8000/api';
    } else {
      // Production: API Gateway or same host
      return '/api';
    }
  }

  /**
   * Authentication Methods
   */

  // Register new user with email/password
  register(email: string, password: string, displayName?: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/register`, {
      email,
      password,
      display_name: displayName
    }).pipe(
      tap((response: any) => {
        if (response.token) {
          this.setAuthToken(response.token);
        }
      }),
      catchError(this.handleError)
    );
  }

  // Login with email/password
  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/login`, {
      email,
      password
    }).pipe(
      tap((response: any) => {
        if (response.token) {
          this.setAuthToken(response.token);
        }
      }),
      catchError(this.handleError)
    );
  }

  // Google OAuth authentication
  googleAuth(idToken: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/google`, {
      id_token: idToken
    }).pipe(
      tap((response: any) => {
        if (response.token) {
          this.setAuthToken(response.token);
        }
      }),
      catchError(this.handleError)
    );
  }

  // Alias for googleAuth (for compatibility)
  googleLogin(idToken: string): Observable<any> {
    return this.googleAuth(idToken);
  }

  // Get current authenticated user
  getCurrentUser(): Observable<any> {
    return this.http.get(`${this.apiUrl}/auth/me`, {
      headers: this.getAuthHeaders()
    }).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  // Logout
  logout(): void {
    this.authToken = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('current_user');
  }

  // Set auth token
  setAuthToken(token: string): void {
    this.authToken = token;
    localStorage.setItem('auth_token', token);
  }

  // Get auth token
  getAuthToken(): string | null {
    return this.authToken;
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return this.authToken !== null;
  }

  // Get auth headers
  private getAuthHeaders(): any {
    if (this.authToken) {
      return { 'Authorization': `Bearer ${this.authToken}` };
    }
    return {};
  }

  /**
   * Health check endpoint
   */
  healthCheck(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  /**
   * Market Data Endpoints
   */
  
  // Get market data for a symbol (OHLCV + indicators)
  getMarketData(symbol: string, period: string = '1mo', interval: string = '1d'): Observable<any> {
    const cacheKey = `${symbol}_${period}_${interval}`;
    
    // Check cache first
    const cached = this.marketDataCache.get(cacheKey);
    if (cached && (Date.now() - cached.timestamp) < this.cacheTimeout) {
      const ageSeconds = Math.floor((Date.now() - cached.timestamp) / 1000);
      console.log(`✅ Cache hit for ${symbol} (age: ${ageSeconds}s, expires in: ${Math.floor((this.cacheTimeout - (Date.now() - cached.timestamp)) / 1000)}s)`);
      return of(cached.data);
    }
    
    // Check if request is already pending
    const pending = this.pendingRequests.get(cacheKey);
    if (pending) {
      console.log(`Reusing pending request for ${symbol}`);
      return pending;
    }
    
    // Make new request
    console.log(`🔄 Fetching fresh data for ${symbol} (cache miss or expired)`);
    const request = this.http.get(`${this.apiUrl}/market/${symbol}`, {
      params: { period, interval }
    }).pipe(
      retry(2),
      tap(data => {
        // Store in cache
        this.marketDataCache.set(cacheKey, { data, timestamp: Date.now() });
        // Remove from pending
        this.pendingRequests.delete(cacheKey);
      }),
      catchError(error => {
        // Remove from pending on error
        this.pendingRequests.delete(cacheKey);
        return this.handleError(error);
      }),
      shareReplay(1)
    );
    
    // Store pending request
    this.pendingRequests.set(cacheKey, request);
    return request;
  }

  // Get current price for a symbol
  getCurrentPrice(symbol: string): Observable<number> {
    return this.getMarketData(symbol, '1d', '1h').pipe(
      map(data => {
        if (data.candles && data.candles.length > 0) {
          const lastCandle = data.candles[data.candles.length - 1];
          return lastCandle.close;
        }
        return 0;
      }),
      catchError(() => of(0))
    );
  }

  /**
   * Portfolio Management Endpoints (DynamoDB)
   */

  // Get all portfolios for current user
  getPortfolios(): Observable<any> {
    return this.http.get(`${this.apiUrl}/portfolios`, {
      headers: this.getAuthHeaders()
    }).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  // Create new portfolio
  createPortfolio(portfolioName: string, initialValue: number = 10000, trackedSymbols?: string[]): Observable<any> {
    return this.http.post(`${this.apiUrl}/portfolios`, {
      portfolio_name: portfolioName,
      initial_value: initialValue,
      tracked_symbols: trackedSymbols || []
    }, {
      headers: this.getAuthHeaders()
    }).pipe(
      catchError(this.handleError)
    );
  }

  // Get specific portfolio details
  getPortfolioDetail(portfolioId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/portfolios/${portfolioId}`, {
      headers: this.getAuthHeaders()
    }).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  // Delete portfolio
  deletePortfolio(portfolioId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/portfolios/${portfolioId}`, {
      headers: this.getAuthHeaders()
    }).pipe(
      catchError(this.handleError)
    );
  }

  // Activate portfolio (set as default)
  activatePortfolio(portfolioId: string): Observable<any> {
    return this.http.put(`${this.apiUrl}/portfolios/${portfolioId}/activate`, {}, {
      headers: this.getAuthHeaders()
    }).pipe(
      catchError(this.handleError)
    );
  }

  // Add tracked symbol to portfolio
  addTrackedSymbol(portfolioId: string, symbol: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/portfolios/${portfolioId}/symbols`, {
      symbol: symbol.toUpperCase()
    }, {
      headers: this.getAuthHeaders()
    }).pipe(
      catchError(this.handleError)
    );
  }

  // Remove tracked symbol from portfolio
  removeTrackedSymbol(portfolioId: string, symbol: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/portfolios/${portfolioId}/symbols/${symbol.toUpperCase()}`, {
      headers: this.getAuthHeaders()
    }).pipe(
      catchError(this.handleError)
    );
  }

  // Get tracked symbols for portfolio
  getTrackedSymbols(portfolioId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/portfolios/${portfolioId}/symbols`, {
      headers: this.getAuthHeaders()
    }).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  // Execute trade in specific portfolio
  executeTradeInPortfolio(portfolioId: string, symbol: string, side: 'buy' | 'sell', quantity: number, tradeType: string = 'market'): Observable<any> {
    return this.http.post(`${this.apiUrl}/portfolios/${portfolioId}/trades`, {
      symbol: symbol.toUpperCase(),
      side: side.toLowerCase(),
      quantity,
      trade_type: tradeType
    }, {
      headers: this.getAuthHeaders()
    }).pipe(
      catchError(this.handleError)
    );
  }

  // Get trade history for specific portfolio
  getPortfolioTrades(portfolioId: string, symbol?: string, limit: number = 50): Observable<any> {
    let params: any = { limit: limit.toString() };
    if (symbol) {
      params.symbol = symbol.toUpperCase();
    }

    return this.http.get(`${this.apiUrl}/portfolios/${portfolioId}/trades`, {
      headers: this.getAuthHeaders(),
      params
    }).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  /**
   * Legacy Portfolio Simulation Endpoints (Backward Compatibility)
   */

  // Initialize a new portfolio (legacy)
  initPortfolio(userId: string, startingCapital: number = 100000): Observable<any> {
    return this.http.post(`${this.apiUrl}/init`, {
      user_id: userId,
      cash: startingCapital
    }).pipe(
      catchError(this.handleError)
    );
  }

  // Get portfolio status (legacy)
  getPortfolio(userId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/portfolio/${userId}`).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  // Execute a trade (legacy)
  executeTrade(userId: string, symbol: string, side: 'buy' | 'sell', quantity: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/paper_trade`, {
      user_id: userId,
      symbol,
      side,
      quantity
    }).pipe(
      catchError(this.handleError)
    );
  }

  // Get trade history (legacy)
  getTradeHistory(userId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/portfolio/${userId}/history`).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  /**
   * AI Agent Endpoints
   */

  // Get learning plan from Planner agent
  getPlan(userId: string, experienceLevel: string = 'beginner'): Observable<any> {
    return this.http.post(`${this.apiUrl}/plan`, {
      user_id: userId,
      experience_level: experienceLevel
    }).pipe(
      catchError(this.handleError)
    );
  }

  // Get trade critique from Critic agent
  critiqueTrade(userId: string, symbol: string, side: string, rationale: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/critique`, {
      user_id: userId,
      symbol,
      side,
      rationale
    }).pipe(
      catchError(this.handleError)
    );
  }

  // Get coaching from Coach agent
  getCoaching(userId: string, topic: string, context?: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/coach`, {
      user_id: userId,
      topic,
      context
    }).pipe(
      catchError(this.handleError)
    );
  }

  // Send message to coach (supports chat interface)
  sendCoachMessage(userId: string, goal: string, message: string, riskLevel: string = 'medium', symbols: string[] = ['AAPL', 'MSFT', 'TSLA']): Observable<any> {
    return this.http.post(`${this.apiUrl}/coach`, {
      user_id: userId,
      goal: `${goal}. User asks: ${message}`,
      risk_level: riskLevel,
      symbols: symbols
    }).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * Analytics and Metrics
   */

  // Get portfolio performance metrics
  getPerformanceMetrics(userId: string): Observable<any> {
    return this.getPortfolio(userId).pipe(
      map(portfolio => {
        const totalValue = portfolio.cash + portfolio.holdings_value;
        const totalPnL = totalValue - portfolio.starting_capital;
        const returnPercent = (totalPnL / portfolio.starting_capital) * 100;

        return {
          portfolioValue: totalValue,
          cash: portfolio.cash,
          holdingsValue: portfolio.holdings_value,
          totalPnL,
          returnPercent,
          startingCapital: portfolio.starting_capital,
          positions: portfolio.positions || []
        };
      }),
      catchError(() => of({
        portfolioValue: 0,
        cash: 0,
        holdingsValue: 0,
        totalPnL: 0,
        returnPercent: 0,
        startingCapital: 100000,
        positions: []
      }))
    );
  }

  // Calculate win rate from trade history
  getWinRate(userId: string): Observable<number> {
    return this.getTradeHistory(userId).pipe(
      map(history => {
        if (!history || history.length === 0) return 0;
        
        const closedTrades = history.filter((trade: any) => trade.status === 'filled');
        if (closedTrades.length === 0) return 0;
        
        const wins = closedTrades.filter((trade: any) => trade.pnl > 0).length;
        return (wins / closedTrades.length) * 100;
      }),
      catchError(() => of(0))
    );
  }

  /**
   * Multi-symbol market data with intelligent deduplication
   */
  getMultipleSymbols(symbols: string[], forceRefresh: boolean = false): Observable<Map<string, any>> {
    console.log('getMultipleSymbols called with:', symbols, 'forceRefresh:', forceRefresh);
    
    // Deduplicate input symbols
    const uniqueSymbols = [...new Set(symbols)];
    console.log('Unique symbols to fetch:', uniqueSymbols);
    
    // Use forkJoin for parallel requests with proper rxjs handling
    const requests: { [key: string]: Observable<any> } = {};
    uniqueSymbols.forEach(symbol => {
      requests[symbol] = this.getMarketData(symbol, '1d', '1h').pipe(
        catchError(error => {
          console.error(`Failed to fetch ${symbol}:`, error);
          return of(null);
        })
      );
    });

    return new Observable(observer => {
      // Only make requests for symbols not in cache or expired
      const validRequests: { [key: string]: Observable<any> } = {};
      const cachedResults = new Map<string, any>();
      
      uniqueSymbols.forEach(symbol => {
        const cacheKey = `${symbol}_1d_1h`;
        const cached = this.marketDataCache.get(cacheKey);
        
        // If forceRefresh is true, bypass cache
        if (!forceRefresh && cached && (Date.now() - cached.timestamp) < this.cacheTimeout) {
          console.log(`Using cached data for ${symbol}`);
          cachedResults.set(symbol, cached.data);
        } else {
          console.log(`Will fetch fresh data for ${symbol}`);
          validRequests[symbol] = requests[symbol];
        }
      });
      
      // Fetch only non-cached symbols
      if (Object.keys(validRequests).length === 0) {
        console.log('All data from cache, returning immediately');
        observer.next(cachedResults);
        observer.complete();
        return;
      }
      
      forkJoin(validRequests).subscribe({
        next: (results: any) => {
          console.log('Fetched fresh data for symbols:', Object.keys(results));
          const dataMap = new Map(cachedResults);
          
          Object.entries(results).forEach(([symbol, data]) => {
            if (data) {
              dataMap.set(symbol, data);
            }
          });
          
          observer.next(dataMap);
          observer.complete();
        },
        error: (error: any) => {
          console.error('Error fetching multiple symbols:', error);
          // Return cached data even on error
          observer.next(cachedResults);
          observer.complete();
        }
      });
    });
  }

  /**
   * Coach & Agent Endpoints
   */
  
  // Trade Analysis - Coordinated Planner + Critic agents
  getTradeAnalysis(request: { idea: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/trade-analysis`, request).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  // Educational Coach - General Q&A
  coachUser(request: { user_query: string; user_level?: string; focus_area?: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/coach`, request).pipe(
      retry(1),
      catchError(this.handleError)
    );
  }

  /**
   * Error handling
   */
  private handleError(error: HttpErrorResponse) {
    let errorMessage = 'An error occurred';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
      
      if (error.error && error.error.detail) {
        errorMessage = error.error.detail;
      }
    }
    
    console.error('API Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
