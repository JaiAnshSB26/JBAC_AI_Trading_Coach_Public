import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
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
  
  // User state - simplified without pictures
  isLoggedIn = false;
  userName = 'John Trader';
  userEmail = 'john@tradingcoach.ai';
  
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

  ngOnInit() {
    // Start with logged out state for simplicity
    this.isLoggedIn = false;
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
    console.log('Opening login...');
    // Simulate login process
    this.isLoggedIn = true;
    this.userName = 'John Trader';
    this.userEmail = 'john@tradingcoach.ai';
    alert('Successfully logged in as John Trader!');
  }

  register() {
    console.log('Opening registration...');
    alert('Registration: Create your new AI Trading Coach account');
  }

  viewProfile() {
    console.log('Navigating to profile...');
    alert('Profile: View and edit your trading profile');
  }

  viewPortfolio() {
    console.log('Navigating to portfolio...');
    alert('Portfolio: View your current positions and performance');
  }

  viewSettings() {
    console.log('Navigating to user settings...');
    alert('User Settings: Manage account preferences and security');
  }

  logout() {
    console.log('Logging out...');
    this.isLoggedIn = false;
    this.userName = '';
    this.userEmail = '';
    alert('Successfully logged out!');
  }
}


