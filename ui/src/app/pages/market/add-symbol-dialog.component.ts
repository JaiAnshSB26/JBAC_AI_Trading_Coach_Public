import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { FormsModule } from '@angular/forms';


@Component({
  selector: 'app-add-symbol-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    FormsModule
  ],
  templateUrl: './add-symbol-dialog.component.html',
  styleUrls: ['./add-symbol-dialog.component.scss']
})
export class AddSymbolDialogComponent {
  symbol = '';
  displayName = '';

  constructor(private dialogRef: MatDialogRef<AddSymbolDialogComponent>) {}

  onSymbolInput() {
    // Convert to uppercase as user types
    this.symbol = this.symbol.toUpperCase();
  }

  selectSuggestion(symbol: string, name: string) {
    this.symbol = symbol;
    this.displayName = name;
  }

  addSymbol() {
    if (!this.symbol || !this.symbol.trim()) {
      return;
    }

    const symbolUpper = this.symbol.toUpperCase().trim();
    this.dialogRef.close({ 
      symbol: symbolUpper, 
      name: this.displayName || symbolUpper 
    });
  }
}
