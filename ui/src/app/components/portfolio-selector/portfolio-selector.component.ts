import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-portfolio-selector',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './portfolio-selector.component.html',
  styleUrls: ['./portfolio-selector.component.scss']
})
export class PortfolioSelectorComponent implements OnInit {
  portfolios: any[] = [];
  activePortfolio: any = null;
  loading = false;
  showCreateForm = false;
  
  // Create portfolio form
  newPortfolioName = '';
  newPortfolioAmount = 10000;
  newPortfolioSymbols = 'AAPL,TSLA,NVDA';
  
  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadPortfolios();
  }

  loadPortfolios(): void {
    this.loading = true;
    this.apiService.getPortfolios().subscribe({
      next: (response) => {
        this.portfolios = response.portfolios || [];
        
        // Find active portfolio (or use first one)
        const user = JSON.parse(localStorage.getItem('current_user') || '{}');
        if (user.default_portfolio_id) {
          this.activePortfolio = this.portfolios.find(p => p.portfolio_id === user.default_portfolio_id);
        }
        if (!this.activePortfolio && this.portfolios.length > 0) {
          this.activePortfolio = this.portfolios[0];
        }
        
        this.loading = false;
      },
      error: (error) => {
        console.error('Failed to load portfolios:', error);
        this.loading = false;
      }
    });
  }

  selectPortfolio(portfolio: any): void {
    this.apiService.activatePortfolio(portfolio.portfolio_id).subscribe({
      next: () => {
        this.activePortfolio = portfolio;
        
        // Update user in localStorage
        const user = JSON.parse(localStorage.getItem('current_user') || '{}');
        user.default_portfolio_id = portfolio.portfolio_id;
        localStorage.setItem('current_user', JSON.stringify(user));
        
        // Emit event or reload page
        window.location.reload();
      },
      error: (error) => {
        console.error('Failed to activate portfolio:', error);
      }
    });
  }

  createPortfolio(): void {
    if (!this.newPortfolioName.trim()) {
      alert('Please enter a portfolio name');
      return;
    }

    const symbols = this.newPortfolioSymbols
      .split(',')
      .map(s => s.trim().toUpperCase())
      .filter(s => s.length > 0);

    this.apiService.createPortfolio(this.newPortfolioName, this.newPortfolioAmount, symbols).subscribe({
      next: (response) => {
        console.log('Portfolio created:', response);
        this.showCreateForm = false;
        this.newPortfolioName = '';
        this.newPortfolioAmount = 10000;
        this.newPortfolioSymbols = 'AAPL,TSLA,NVDA';
        this.loadPortfolios();
      },
      error: (error) => {
        console.error('Failed to create portfolio:', error);
        alert('Failed to create portfolio: ' + error.message);
      }
    });
  }

  deletePortfolio(portfolio: any, event: Event): void {
    event.stopPropagation();
    
    if (!confirm(`Are you sure you want to delete "${portfolio.portfolio_name}"?`)) {
      return;
    }

    this.apiService.deletePortfolio(portfolio.portfolio_id).subscribe({
      next: () => {
        console.log('Portfolio deleted');
        this.loadPortfolios();
      },
      error: (error) => {
        console.error('Failed to delete portfolio:', error);
        alert('Failed to delete portfolio: ' + error.message);
      }
    });
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  }

  cancelCreate(): void {
    this.showCreateForm = false;
    this.newPortfolioName = '';
    this.newPortfolioAmount = 10000;
    this.newPortfolioSymbols = 'AAPL,TSLA,NVDA';
  }
}
