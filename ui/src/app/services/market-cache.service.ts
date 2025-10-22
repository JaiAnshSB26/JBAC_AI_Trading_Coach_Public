import { Injectable } from '@angular/core';

/**
 * Session-level market data cache service
 * Persists data across component navigation within the same browser session
 */
@Injectable({
  providedIn: 'root'
})
export class MarketCacheService {
  private cache = new Map<string, CachedMarketData>();
  private readonly CACHE_DURATION = 60000; // 1 minute

  constructor() {
    console.log('MarketCacheService initialized');
  }

  /**
   * Get cached market data for a symbol
   */
  get(symbol: string): any | null {
    const cached = this.cache.get(symbol.toUpperCase());
    
    if (!cached) {
      return null;
    }

    // Check if cache is still valid
    const now = Date.now();
    if (now - cached.timestamp > this.CACHE_DURATION) {
      console.log(`Cache expired for ${symbol}`);
      this.cache.delete(symbol.toUpperCase());
      return null;
    }

    console.log(`Cache hit for ${symbol}`);
    return cached.data;
  }

  /**
   * Set cached market data for a symbol
   */
  set(symbol: string, data: any): void {
    this.cache.set(symbol.toUpperCase(), {
      data,
      timestamp: Date.now()
    });
    console.log(`Cached data for ${symbol}`);
  }

  /**
   * Check if symbol data is cached and valid
   */
  has(symbol: string): boolean {
    return this.get(symbol) !== null;
  }

  /**
   * Clear cache for specific symbol
   */
  clear(symbol: string): void {
    this.cache.delete(symbol.toUpperCase());
    console.log(`Cleared cache for ${symbol}`);
  }

  /**
   * Clear all cached data
   */
  clearAll(): void {
    this.cache.clear();
    console.log('Cleared all market cache');
  }

  /**
   * Get all cached symbols
   */
  getCachedSymbols(): string[] {
    return Array.from(this.cache.keys());
  }

  /**
   * Force refresh - clears cache and allows new fetch
   */
  invalidate(symbol?: string): void {
    if (symbol) {
      this.clear(symbol);
    } else {
      this.clearAll();
    }
  }
}

interface CachedMarketData {
  data: any;
  timestamp: number;
}
