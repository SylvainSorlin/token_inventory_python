"""
Microsoft Graph API Client
Handles all API calls to Microsoft Graph for token management
"""
import requests
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

@dataclass
class GraphAPIError(Exception):
    """Custom exception for Graph API errors"""
    message: str
    status_code: Optional[int] = None
    details: Optional[str] = None

class GraphAPIClient:
    """Client for Microsoft Graph API operations"""

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = None

    def _get_access_token(self) -> str:
        """Get OAuth2 access token"""
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }

        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            self._access_token = result.get('access_token')

            if not self._access_token:
                raise GraphAPIError("No access token received")

            return self._access_token

        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                error_data = e.response.json() if e.response.text else {}
                error_desc = error_data.get('error_description', str(e))

                if 'AADSTS70002' in error_desc or 'invalid_client' in error_desc:
                    raise GraphAPIError("Invalid Client ID or Client Secret")
                elif 'AADSTS90002' in error_desc or 'invalid_tenant' in error_desc:
                    raise GraphAPIError("Invalid Tenant ID")
                else:
                    raise GraphAPIError(f"Authentication failed: {error_desc}")
            else:
                raise GraphAPIError(f"Connection error: {str(e)}")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization"""
        if not self._access_token:
            self._get_access_token()

        return {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json'
        }

    def fetch_tokens(self) -> List[Dict[str, Any]]:
        """Fetch all hardware OATH tokens"""
        url = "https://graph.microsoft.com/beta/directory/authenticationMethodDevices/hardwareOathDevices"

        try:
            all_tokens = []

            while url:
                response = requests.get(url, headers=self._get_headers(), timeout=30)

                if response.status_code in [401, 403]:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get('error', {}).get('message', '')

                    if 'Insufficient privileges' in error_msg:
                        raise GraphAPIError(
                            "Missing API Permissions. Required:\n"
                            "• Policy.ReadWrite.AuthenticationMethod\n"
                            "• UserAuthenticationMethod.ReadWrite.All\n"
                            "• User.Read.All\n"
                            "• Directory.Read.All"
                        )
                    else:
                        raise GraphAPIError(f"Permission denied: {error_msg}")

                response.raise_for_status()
                data = response.json()

                all_tokens.extend(data.get('value', []))
                url = data.get('@odata.nextLink')

            return all_tokens

        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError):
                raise GraphAPIError(f"HTTP Error: {e.response.status_code}", e.response.status_code)
            raise GraphAPIError(f"Request failed: {str(e)}")

    def search_users(self, query: str = "") -> List[Dict[str, Any]]:
        """Search for users"""
        if query:
            filter_query = f"startswith(displayName,'{query}') or startswith(userPrincipalName,'{query}')"
            url = f"https://graph.microsoft.com/v1.0/users?$top=50&$filter={requests.utils.quote(filter_query)}"
        else:
            url = "https://graph.microsoft.com/v1.0/users?$top=50"

        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('value', [])

        except requests.exceptions.RequestException as e:
            raise GraphAPIError(f"User search failed: {str(e)}")

    def import_token(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import a single token"""
        url = "https://graph.microsoft.com/beta/directory/authenticationMethodDevices/hardwareOathDevices"

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=token_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            error_data = {}
            if hasattr(e, 'response') and e.response is not None and e.response.text:
                try:
                    error_data = e.response.json()
                except:
                    pass
            raise GraphAPIError(f"Import failed: {str(e)}", details=error_data)

    def assign_token(self, user_id: str, token_id: str) -> Dict[str, Any]:
        """Assign token to user"""
        url = f"https://graph.microsoft.com/beta/users/{user_id}/authentication/hardwareOathMethods"
        data = {"device": {"id": token_id}}

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json() if response.text else {}

        except requests.exceptions.RequestException as e:
            raise GraphAPIError(f"Assignment failed: {str(e)}")

    def activate_token(self, user_id: str, token_id: str, verification_code: str) -> bool:
        """Activate token with verification code"""
        url = f"https://graph.microsoft.com/beta/users/{user_id}/authentication/hardwareOathMethods/{token_id}/activate"
        data = {"verificationCode": verification_code}

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=data,
                timeout=30
            )
            return response.status_code in [200, 204]

        except requests.exceptions.RequestException as e:
            raise GraphAPIError(f"Activation failed: {str(e)}")

    def unassign_token(self, user_id: str, token_id: str) -> bool:
        """Unassign token from user"""
        url = f"https://graph.microsoft.com/beta/users/{user_id}/authentication/hardwareOathMethods/{token_id}"

        try:
            response = requests.delete(url, headers=self._get_headers(), timeout=30)
            return response.status_code in [200, 204]

        except requests.exceptions.RequestException as e:
            raise GraphAPIError(f"Unassign failed: {str(e)}")

    def delete_token(self, token_id: str) -> bool:
        """Delete token permanently"""
        url = f"https://graph.microsoft.com/beta/directory/authenticationMethodDevices/hardwareOathDevices/{token_id}"

        try:
            response = requests.delete(url, headers=self._get_headers(), timeout=30)
            return response.status_code in [200, 204]

        except requests.exceptions.RequestException as e:
            raise GraphAPIError(f"Delete failed: {str(e)}")

    def import_csv_tokens(self, csv_data: str, import_mode: str = 'import_assign_activate') -> Dict[str, Any]:
        """
        Import tokens from CSV data

        Args:
            csv_data: CSV string with headers
            import_mode: 'import_only', 'import_assign', or 'import_assign_activate'

        Returns:
            Dictionary with results for each token
        """
        from .totp import generate_totp_code, validate_base32_secret
        import csv
        from io import StringIO

        results = {}
        reader = csv.DictReader(StringIO(csv_data))

        for row_num, row in enumerate(reader, start=2):
            serial_number = row.get('serial number', '').strip()
            secret_key = row.get('secret key', '').strip().upper().replace(' ', '')
            upn = row.get('upn', '').strip()
            time_interval = int(row.get('timeinterval', 30))
            manufacturer = row.get('manufacturer', '').strip()
            model = row.get('model', '').strip()

            # Validate required fields
            if not serial_number or not secret_key:
                results[serial_number or f"line_{row_num}"] = {
                    'success': False,
                    'error': 'Missing serial number or secret key'
                }
                continue

            # Validate UPN for assignment modes
            if import_mode in ['import_assign', 'import_assign_activate'] and not upn:
                results[serial_number] = {
                    'success': False,
                    'error': 'UPN required for assignment mode'
                }
                continue

            # Validate secret key
            is_valid, error_msg = validate_base32_secret(secret_key)
            if not is_valid:
                results[serial_number] = {
                    'success': False,
                    'error': error_msg
                }
                continue

            # Determine hash function
            hash_function = 'hmacsha1' if len(secret_key) <= 32 else 'hmacsha256'

            # Import token
            token_data = {
                "displayName": f"{manufacturer} {model} - {serial_number}",
                "serialNumber": serial_number,
                "manufacturer": manufacturer,
                "model": model,
                "secretKey": secret_key,
                "timeIntervalInSeconds": time_interval,
                "hashFunction": hash_function
            }

            try:
                import_result = self.import_token(token_data)
                token_id = import_result.get('id')

                results[serial_number] = {
                    'success': True,
                    'token_id': token_id,
                    'import_result': import_result
                }

                # Assign if needed
                if token_id and import_mode in ['import_assign', 'import_assign_activate'] and upn:
                    try:
                        self.assign_token(upn, token_id)
                        results[serial_number]['assigned'] = True

                        # Activate if needed
                        if import_mode == 'import_assign_activate':
                            code = generate_totp_code(secret_key, time_interval)
                            if code:
                                activated = self.activate_token(upn, token_id, code)
                                results[serial_number]['activated'] = activated
                            else:
                                results[serial_number]['activated'] = False
                                results[serial_number]['activation_error'] = 'Failed to generate TOTP code'

                    except GraphAPIError as e:
                        results[serial_number]['assigned'] = False
                        results[serial_number]['error'] = str(e)

            except GraphAPIError as e:
                results[serial_number] = {
                    'success': False,
                    'error': str(e)
                }

        return results
