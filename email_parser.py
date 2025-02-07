import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

class EmailParser:
    def __init__(self):
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def is_valid_domain(self, domain):
        """Validate domain format"""
        try:
            result = urlparse(domain)
            return all([result.scheme, result.netloc])
        except:
            return False

    def normalize_domain(self, domain):
        """Ensure domain has proper scheme"""
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain
        return domain

    def extract_emails(self, text):
        """Extract email addresses from text"""
        return set(self.email_pattern.findall(text))

    def parse_page(self, url):
        """Parse a single page for email addresses"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Also check href attributes for mailto: links
            mailto_links = [a.get('href', '') for a in soup.find_all('a', href=True)]
            mailto_emails = [
                href.replace('mailto:', '') 
                for href in mailto_links 
                if href.startswith('mailto:')
            ]
            
            # Combine both sources of emails
            emails = self.extract_emails(text)
            emails.update(mailto_emails)
            
            return emails
            
        except Exception as e:
            logging.error(f"Error parsing {url}: {str(e)}")
            return set()

    def parse_domains(self, domains):
        """Parse multiple domains for email addresses"""
        for domain in domains:
            try:
                domain = domain.strip()
                if not domain:
                    continue
                
                domain = self.normalize_domain(domain)
                if not self.is_valid_domain(domain):
                    yield domain, [f"Invalid domain format: {domain}"]
                    continue
                
                emails = self.parse_page(domain)
                yield domain, emails
                
            except Exception as e:
                logging.error(f"Error processing domain {domain}: {str(e)}")
                yield domain, [f"Error: {str(e)}"]
