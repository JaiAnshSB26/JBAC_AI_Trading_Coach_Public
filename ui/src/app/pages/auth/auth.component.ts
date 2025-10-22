import { Component, OnInit, AfterViewInit, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { ApiService } from '../../services/api.service';
import { environment } from '../../../environments/environment';

declare const google: any;

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, MatIconModule],
  templateUrl: './auth.component.html',
  styleUrls: ['./auth.component.scss']
})
export class AuthComponent implements OnInit, AfterViewInit {
  loginForm: FormGroup;
  registerForm: FormGroup;
  isLoginMode = true;
  loading = false;
  errorMessage = '';
  returnUrl = '/dashboard';
  
  // Google OAuth Client ID
  private googleClientId = environment.googleClientId;

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private router: Router,
    private route: ActivatedRoute,
    private ngZone: NgZone
  ) {
    // Initialize login form
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]]
    });

    // Initialize register form
    this.registerForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', [Validators.required]],
      displayName: ['', [Validators.required, Validators.minLength(2)]]
    }, { validators: this.passwordMatchValidator });
  }

  ngOnInit(): void {
    // Get return URL from route parameters or default to dashboard
    this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';

    // Redirect if already logged in
    if (this.apiService.isAuthenticated()) {
      this.router.navigate([this.returnUrl]);
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

      // Render button if element exists
      const buttonElement = document.getElementById('google-signin-button');
      if (buttonElement) {
        google.accounts.id.renderButton(buttonElement, {
          theme: 'outline',
          size: 'large',
          width: '100%',
          text: 'signin_with'
        });
      }
    }
  }

  /**
   * Handle Google Sign-In callback
   */
  private handleGoogleCallback(response: any): void {
    this.ngZone.run(() => {
      this.loading = true;
      this.errorMessage = '';

      this.apiService.googleLogin(response.credential).subscribe({
        next: (authResponse) => {
          console.log('Google login successful:', authResponse);
          
          // Store user data
          localStorage.setItem('current_user', JSON.stringify(authResponse.user));
          
          // Navigate to return URL or dashboard
          this.router.navigate([this.returnUrl]);
        },
        error: (error) => {
          console.error('Google login failed:', error);
          this.errorMessage = error.message || 'Google login failed. Please try again.';
          this.loading = false;
        }
      });
    });
  }

  // Custom validator to check if passwords match
  passwordMatchValidator(group: FormGroup): { [key: string]: boolean } | null {
    const password = group.get('password')?.value;
    const confirmPassword = group.get('confirmPassword')?.value;
    return password === confirmPassword ? null : { passwordMismatch: true };
  }

  // Toggle between login and register modes
  toggleMode(): void {
    this.isLoginMode = !this.isLoginMode;
    this.errorMessage = '';
  }

  // Handle login
  onLogin(): void {
    if (this.loginForm.invalid) {
      return;
    }

    this.loading = true;
    this.errorMessage = '';

    const { email, password } = this.loginForm.value;

    this.apiService.login(email, password).subscribe({
      next: (response) => {
        console.log('Login successful:', response);
        
        // Store user data
        localStorage.setItem('current_user', JSON.stringify(response.user));
        
        // Navigate to return URL or dashboard
        this.router.navigate([this.returnUrl]);
      },
      error: (error) => {
        console.error('Login failed:', error);
        this.errorMessage = error.message || 'Login failed. Please check your credentials.';
        this.loading = false;
      }
    });
  }

  // Handle registration
  onRegister(): void {
    if (this.registerForm.invalid) {
      return;
    }

    this.loading = true;
    this.errorMessage = '';

    const { email, password, displayName } = this.registerForm.value;

    this.apiService.register(email, password, displayName).subscribe({
      next: (response) => {
        console.log('Registration successful:', response);
        
        // Store user data
        localStorage.setItem('current_user', JSON.stringify(response.user));
        
        // Navigate to dashboard
        this.router.navigate(['/dashboard']);
      },
      error: (error) => {
        console.error('Registration failed:', error);
        this.errorMessage = error.message || 'Registration failed. Please try again.';
        this.loading = false;
      }
    });
  }

  // Handle Google OAuth
  onGoogleLogin(): void {
    // Google Sign-In is handled by the button callback
    // This method can be used for programmatic login if needed
    console.log('Google Sign-In button should handle authentication');
  }

  // Get form field for validation display
  getLoginControl(field: string) {
    return this.loginForm.get(field);
  }

  getRegisterControl(field: string) {
    return this.registerForm.get(field);
  }
}
