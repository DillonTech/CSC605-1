import pdfplumber
import re
from decimal import Decimal
from datetime import datetime
import threading
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class StatementProcessor:
    def __init__(self, user_profile):
        self.user_profile = user_profile
        self.transactions = []

    def process_statement_async(self, uploaded_file):
        """Start asynchronous processing of the statement"""
        self.user_profile.statement_processing_status = 'processing'
        self.user_profile.save()

        # Save the file temporarily
        path = f'temp_statements/user_{self.user_profile.user.id}_{datetime.now().timestamp()}.pdf'
        saved_path = default_storage.save(path, ContentFile(uploaded_file.read()))

        # Start processing in a separate thread
        thread = threading.Thread(
            target=self._process_statement,
            args=(saved_path,)
        )
        thread.start()

    def _process_statement(self, file_path):
        """Process the PDF statement and extract transactions"""
        try:
            with pdfplumber.open(default_storage.open(file_path)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    self._extract_transactions(text)

            # Update profile status
            self.user_profile.statement_processing_status = 'completed'
            self.user_profile.last_statement_upload = datetime.now()
            self.user_profile.save()

            # Save extracted transactions
            self._save_transactions()

        except Exception as e:
            self.user_profile.statement_processing_status = 'error'
            self.user_profile.error_message = str(e)
            self.user_profile.save()
        finally:
            # Clean up temporary file
            default_storage.delete(file_path)

    def _extract_transactions(self, text):
        """Extract transactions from text using regex patterns"""
        # This is a basic example - adjust patterns based on your bank's statement format
        # Transaction pattern: date followed by description and amount
        pattern = r'(\d{2}/\d{2}/\d{4})\s+([A-Za-z0-9\s]+?)\s+([-+]?\$?\d+\.\d{2})'
        
        matches = re.finditer(pattern, text)
        for match in matches:
            date_str, description, amount_str = match.groups()
            
            # Clean up amount string and convert to decimal
            amount = Decimal(amount_str.replace('$', '').replace(',', ''))
            
            # Parse date
            date = datetime.strptime(date_str, '%m/%d/%Y').date()
            
            self.transactions.append({
                'date': date,
                'description': description.strip(),
                'amount': amount
            })

    def _save_transactions(self):
        """Save extracted transactions to database"""
        from kakeibo_finance.models import Transaction
        
        for trans in self.transactions:
            # Determine category based on description keywords
            category = self._categorize_transaction(trans['description'])
            
            Transaction.objects.create(
                owner=self.user_profile.user,
                category=category,
                description=trans['description'],
                amount=trans['amount'],
                transaction_date=trans['date']
            )

    def _categorize_transaction(self, description):
        """Categorize transaction based on description"""
        description = description.lower()
        
        # Define category keywords
        categories = {
            'ESSENTIAL': ['grocery', 'rent', 'utilities', 'water', 'electricity'],
            'WANTS': ['restaurant', 'cinema', 'entertainment'],
            'INCOME': ['salary', 'deposit'],
            'SAVINGS': ['investment', 'savings'],
        }

        for category, keywords in categories.items():
            if any(keyword in description for keyword in keywords):
                return category
        
        return 'OTHER'
