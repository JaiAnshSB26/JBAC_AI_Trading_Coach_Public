import { Routes } from '@angular/router';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { MarketComponent } from './pages/market/market.component';
import { CoachComponent } from './pages/coach/coach.component';
import { TradesComponent } from './pages/trades/trades.component';
import { AuthComponent } from './pages/auth/auth.component';
import { AuthGuard } from './guards/auth.guard';


export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'login', component: AuthComponent },
  { path: 'dashboard', component: DashboardComponent, canActivate: [AuthGuard] },
  { path: 'market', component: MarketComponent, canActivate: [AuthGuard] },
  { path: 'coach', component: CoachComponent, canActivate: [AuthGuard] },
  { path: 'trades', component: TradesComponent, canActivate: [AuthGuard] },
  { path: '**', redirectTo: 'dashboard' }
];


