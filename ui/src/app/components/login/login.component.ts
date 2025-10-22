import { Component, OnInit, AfterViewInit, NgZone } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { environment } from '../../../environments/environment';

declare const google: any;

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit, AfterViewInit {
  email = '';
  password = '';
  errorMessage = '';
  isLoading = false;
  showPassword = false;

  // Google OAuth Client ID from environment config
  private googleClientId = environment.googleClientId;

  constructor(
    private authService: AuthService,
    private router: Router,
    private ngZone: NgZone
  ) {}

  ngOnInit(): void {
    // Check if already authenticated
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/dashboard']);
    }

    // Load Google Sign-In script
    this.loadGoogleSignIn();
  }

  ngAfterViewInit(): void {
    // Initialize Google Sign-In button after view loads
    setTimeout(() => this.initializeGoogleSignIn(), 500);
  }

  /**
   * Load Google Sign-In script
   */
  private loadGoogleSignIn(): void {
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
  }

  /**
   * Initialize Google Sign-In button
   */
  private initializeGoogleSignIn(): void {
    if (typeof google !== 'undefined' && google.accounts) {
      google.accounts.id.initialize({
        client_id: this.googleClientId,
        callback: (response: any) => this.handleGoogleCallback(response)
      });

      google.accounts.id.renderButton(
        document.getElementById('google-signin-button'),
        {
          theme: 'outline',
          size: 'large',
          width: '100%',
          text: 'signin_with'
        }
      );
    }
  }

  /**
   * Handle Google Sign-In callback
   */
  private handleGoogleCallback(response: any): void {
    this.ngZone.run(() => {
      this.isLoading = true;
      this.errorMessage = '';

      this.authService.googleLogin(response.credential).subscribe({
        next: () => {
          console.log('Google login successful');
          this.router.navigate(['/dashboard']);
        },
        error: (error) => {
          console.error('Google login failed:', error);
          this.errorMessage = error.error?.detail || 'Google login failed. Please try again.';
          this.isLoading = false;
        }
      });
    });
  }

  /**
   * Handle email/password login
   */
  onLogin(): void {
    if (!this.email || !this.password) {
      this.errorMessage = 'Please enter email and password';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.authService.login(this.email, this.password).subscribe({
      next: () => {
        console.log('Login successful');
        this.router.navigate(['/dashboard']);
      },
      error: (error) => {
        console.error('Login failed:', error);
        this.errorMessage = error.error?.detail || 'Login failed. Please check your credentials.';
        this.isLoading = false;
      }
    });
  }

  /**
   * Navigate to registration page
   */
  goToRegister(): void {
    this.router.navigate(['/register']);
  }

  /**
   * Toggle password visibility
   */
  togglePasswordVisibility(): void {
    this.showPassword = !this.showPassword;
  }
}
