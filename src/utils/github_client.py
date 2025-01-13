import logging
import re
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class GitHubClient:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.config.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'RDP-Monitor-Service'
        })

    def find_rdp_config(self, rdp_version: str) -> Optional[str]:
        try:
            # First try to find in issue comments
            config = self._search_in_issues(rdp_version)
            if config:
                return config

            # If not found in comments, try repository files
            config = self._search_in_repository(rdp_version)
            if config:
                return config

            logging.warning(
                f"No configuration found for RDP version {rdp_version}")
            return None

        except requests.RequestException as e:
            logging.error(f"GitHub API error: {e}")
            return None

    def _search_in_issues(self, rdp_version: str) -> Optional[str]:
        issues_url = 'https://api.github.com/repos/stascorp/rdpwrap/issues'
        params = {
            'per_page': 100,
            'state': 'all',
            'sort': 'updated',
            'direction': 'desc'
        }

        try:
            response = self.session.get(issues_url, params=params)
            response.raise_for_status()
            issues = response.json()

            # Create progress bar for issues
            with tqdm(total=len(issues), desc="Searching issues", unit="issue") as pbar:
                # Search through each issue and its comments
                for issue in issues:
                    pbar.set_postfix_str(f"Checking issue #{issue['number']}")

                    # Check issue body first
                    if issue.get('body'):
                        config = self._extract_config_from_comment(
                            issue['body'], rdp_version)
                        if config:
                            pbar.close()
                            logging.info(
                                f"Found config in issue #{issue['number']}")
                            return config

                    # Then check comments if issue has any
                    if issue['comments'] > 0:
                        comments_url = issue['comments_url']
                        comments_response = self.session.get(comments_url)
                        comments_response.raise_for_status()

                        comments = comments_response.json()
                        for comment in comments:
                            config = self._extract_config_from_comment(
                                comment['body'], rdp_version)
                            if config:
                                pbar.close()
                                logging.info(
                                    f"Found config in comment of issue #{issue['number']}")
                                return config

                    pbar.update(1)

            # # If not found in recent issues, check issue #3280 specifically
            # pbar = tqdm(total=1, desc="Checking issue #3280", unit="issue")
            # specific_issue_url = 'https://api.github.com/repos/stascorp/rdpwrap/issues/3280'
            # issue_response = self.session.get(specific_issue_url)

            # if issue_response.status_code == 200:
            #     issue_data = issue_response.json()
            #     pbar.set_postfix_str("Checking issue body")

            #     if issue_data.get('body'):
            #         config = self._extract_config_from_comment(
            #             issue_data['body'], rdp_version)
            #         if config:
            #             pbar.close()
            #             return config

            #     pbar.set_postfix_str("Checking comments")
            #     comments_response = self.session.get(
            #         issue_data['comments_url'])
            #     if comments_response.status_code == 200:
            #         comments = comments_response.json()
            #         for comment in comments:
            #             config = self._extract_config_from_comment(
            #                 comment['body'], rdp_version)
            #             if config:
            #                 pbar.close()
            #                 return config

            # pbar.close()
            return None

        except requests.RequestException as e:
            logging.error(f"Error searching issues: {e}")
            return None

    def _search_in_repository(self, rdp_version: str) -> Optional[str]:
        search_url = 'https://api.github.com/search/code'
        query = f'repo:stascorp/rdpwrap {rdp_version} extension:ini'

        try:
            with tqdm(total=1, desc="Searching repository files", unit="query") as pbar:
                response = self.session.get(
                    search_url,
                    params={'q': query}
                )
                response.raise_for_status()

                results = response.json()
                if not results.get('items'):
                    pbar.close()
                    return None

                pbar.total = len(results['items'])
                pbar.refresh()

                for item in results['items']:
                    pbar.set_postfix_str(f"Checking {item['name']}")
                    raw_url = item['html_url'].replace(
                        'github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    content_response = self.session.get(raw_url)
                    if content_response.status_code == 200:
                        content = content_response.text
                        if self._validate_config_content(content, rdp_version):
                            pbar.close()
                            return content
                    pbar.update(1)

            return None

        except requests.RequestException as e:
            logging.error(f"Error searching repository: {e}")
            return None

    def _validate_config_content(self, content: str, version: str) -> bool:
        return f'[{version}]' in content

    def _extract_config_from_comment(self, comment_body: str, version: str) -> Optional[str]:
        if not comment_body:
            return None

        version_patterns = [
            re.escape(version),
            re.escape(version).replace(r'\.', r'[._]'),
            r'\b' + re.escape(version).replace(r'\.', r'[._]') + r'\b'
        ]

        def extract_section(text: str, section_pattern: str) -> Optional[str]:
            matches = re.finditer(section_pattern, text, re.MULTILINE)
            for match in matches:
                # Get the matched section
                section_text = match.group(0)
                # Split into lines and process until first empty line
                lines = section_text.split('\n')
                result_lines = []
                for line in lines:
                    if not line.strip():
                        break
                    result_lines.append(line)
                if result_lines:
                    return '\n'.join(result_lines)
            return None

        for pattern in version_patterns:
            # Find main section
            main_section = extract_section(
                comment_body,
                rf'\[{pattern}\][^\n]*\n(?:(?![^\n]*\[)[^\n]*\n)*'
            )

            if main_section:
                # Find SLInit section
                sl_init_section = extract_section(
                    comment_body,
                    rf'\[{pattern}-SLInit\][^\n]*\n(?:(?![^\n]*\[)[^\n]*\n)*'
                )

                if sl_init_section:
                    return f"{main_section}\n\n{sl_init_section}"
                return main_section

        return None
