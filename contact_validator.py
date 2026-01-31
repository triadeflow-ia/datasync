"""
Contact Data Validator
Valida e formata emails e telefones brasileiros
"""

import pandas as pd
import re
from typing import List, Tuple

class ContactDataValidator:
    def __init__(self, default_ddd='85'):
        self.default_ddd = default_ddd
        self.validation_report = {
            'total_rows': 0,
            'valid_emails': 0,
            'invalid_emails': 0,
            'valid_phones': 0,
            'invalid_phones': 0,
            'phones_with_ddd_added': 0,
            'errors': []
        }

    def validate_and_format_email(self, email_str: str) -> Tuple[str, str, List[str]]:
        if pd.isna(email_str) or str(email_str).strip() == '':
            return '', '', []

        email_str = str(email_str).lower().strip()
        potential_emails = re.split(r'[;/,\s]+', email_str)

        valid_emails = []
        invalid_emails = []

        for email in potential_emails:
            email = email.strip()
            if not email or '@' not in email:
                continue

            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(pattern, email):
                valid_emails.append(email)
                self.validation_report['valid_emails'] += 1
            else:
                invalid_emails.append(email)
                self.validation_report['invalid_emails'] += 1

        if len(valid_emails) == 0:
            return '', '', invalid_emails
        elif len(valid_emails) == 1:
            return valid_emails[0], '', invalid_emails
        else:
            return valid_emails[0], ', '.join(valid_emails[1:]), invalid_emails

    def parse_brazilian_phone(self, phone_str: str) -> List[str]:
        if pd.isna(phone_str) or str(phone_str).strip() == '':
            return []

        phone_str = str(phone_str).strip()
        digits_only = re.sub(r'\D', '', phone_str)

        if len(digits_only) == 8:
            digits_only = self.default_ddd + digits_only
            self.validation_report['phones_with_ddd_added'] += 1

        if len(digits_only) == 9:
            digits_only = self.default_ddd + digits_only
            self.validation_report['phones_with_ddd_added'] += 1

        return [digits_only]

    def format_phone(self, phone_digits: str) -> str:
        if len(phone_digits) == 11:
            return f"+55 {phone_digits[:2]} {phone_digits[2:7]}-{phone_digits[7:]}"
        elif len(phone_digits) == 10:
            return f"+55 {phone_digits[:2]} {phone_digits[2:6]}-{phone_digits[6:]}"
        else:
            return f"+55 {self.default_ddd} {phone_digits}"

    def validate_and_format_phones(self, phone_str: str) -> Tuple[str, str]:
        phone_numbers = self.parse_brazilian_phone(phone_str)

        valid_phones = []

        for phone in phone_numbers:
            formatted = self.format_phone(phone)
            valid_phones.append(formatted)
            self.validation_report['valid_phones'] += 1

        if len(valid_phones) == 0:
            return '', ''
        elif len(valid_phones) == 1:
            return valid_phones[0], ''
        else:
            return valid_phones[0], ', '.join(valid_phones[1:])
