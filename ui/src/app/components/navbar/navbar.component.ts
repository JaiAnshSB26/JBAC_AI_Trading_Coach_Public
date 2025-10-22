import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatBadgeModule } from '@angular/material/badge';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

interface Notification {
  id: number;
  title: string;
  time: string;
  icon: string;
  color: string;
  read: boolean;
}

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatInputModule,
    MatFormFieldModule,
    MatBadgeModule,
    MatTooltipModule,
    MatDividerModule,
    FormsModule
  ],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.scss'
})
export class NavbarComponent implements OnInit {
  // Mobile menu state
  isMobileMenuOpen = false;
  
  // Search functionality
  searchQuery = '';
  
  // User state
  isLoggedIn = false;
  currentUser: any = null;
  userName = '';
  userEmail = '';
  
  // Notifications
  notifications: Notification[] = [
    {
      id: 1,
      title: 'BTC hit $67,000 resistance level',
      time: '2 minutes ago',
      icon: 'trending_up',
      color: '#00e676',
      read: false
    },
    {
      id: 2,
      title: 'AI recommends taking profit on TSLA',
      time: '15 minutes ago',
      icon: 'smart_toy',
      color: '#2196f3',
      read: false
    },
    {
      id: 3,
      title: 'Portfolio gained 2.4% today',
      time: '1 hour ago',
      icon: 'account_balance_wallet',
      color: '#00e676',
      read: true
    }
  ];

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    // Check if user is logged in and load user info
    this.loadUserInfo();
    
    // Listen for storage changes (e.g., login/logout in another tab)
    window.addEventListener('storage', (event) => {
      if (event.key === 'token' || event.key === 'current_user') {
        this.loadUserInfo();
      }
    });
  }

  private loadUserInfo() {
    this.isLoggedIn = this.apiService.isAuthenticated();
    
    if (this.isLoggedIn) {
      // Load user from localStorage
      const userStr = localStorage.getItem('current_user');
      if (userStr) {
        try {
          this.currentUser = JSON.parse(userStr);
          this.userName = this.currentUser.display_name || this.currentUser.email?.split('@')[0] || 'Trader';
          this.userEmail = this.currentUser.email || '';
        } catch (e) {
          console.error('Failed to parse user data:', e);
          this.isLoggedIn = false;
        }
      } else {
        // If token exists but user data doesn't, fetch it
        this.apiService.getCurrentUser().subscribe({
          next: (user) => {
            this.currentUser = user;
            this.userName = user.display_name || user.email?.split('@')[0] || 'Trader';
            this.userEmail = user.email || '';
            localStorage.setItem('current_user', JSON.stringify(user));
          },
          error: (err) => {
            console.error('Failed to fetch user data:', err);
            this.isLoggedIn = false;
          }
        });
      }
    } else {
      // Clear user data if not authenticated
      this.currentUser = null;
      this.userName = '';
      this.userEmail = '';
    }
  }

  get notificationCount(): number {
    return this.notifications.filter(n => !n.read).length;
  }

  // Mobile menu functions
  toggleMobileMenu() {
    this.isMobileMenuOpen = !this.isMobileMenuOpen;
  }

  closeMobileMenu() {
    this.isMobileMenuOpen = false;
  }

  // Search functionality
  onSearch() {
    if (this.searchQuery.trim()) {
      console.log('Searching for:', this.searchQuery);
      // Implement search logic here
      alert(`Searching for: ${this.searchQuery}`);
    }
  }

  // Settings menu functions
  openThemeSettings() {
    console.log('Opening theme settings...');
    alert('Theme Settings: Choose between Dark/Light themes');
  }

  openNotificationSettings() {
    console.log('Opening notification settings...');
    alert('Notification Settings: Manage your trading alerts');
  }

  openTradingSettings() {
    console.log('Opening trading settings...');
    alert('Trading Settings: Configure risk management and trading preferences');
  }

  openPreferences() {
    console.log('Opening preferences...');
    alert('General Preferences: Language, timezone, and display settings');
  }

  // Notification functions
  markAllAsRead() {
    this.notifications.forEach(notification => {
      notification.read = true;
    });
    console.log('All notifications marked as read');
  }

  // User menu functions
  login() {
    this.router.navigate(['/login']);
  }

  register() {
    this.router.navigate(['/login']);
  }

  viewProfile() {
    console.log('Navigating to profile...');
    alert('Profile: View and edit your trading profile');
  }

  viewPortfolio() {
    console.log('Navigating to portfolio...');
    this.router.navigate(['/dashboard']);
  }

  viewSettings() {
    console.log('Navigating to user settings...');
    alert('User Settings: Manage account preferences and security');
  }

  logout() {
    console.log('Logging out...');
    this.apiService.logout();
    this.isLoggedIn = false;
    this.currentUser = null;
    this.userName = '';
    this.userEmail = '';
    this.router.navigate(['/login']);
  }
}


