import os
import requests

import json

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.errors import AnsibleError, AnsibleOptionsError



DOCUMENTATION = '''
    name: jpclipffel.tenable.assets
    version_added: "2.4"
    short_description: Get hosts from Tenable assets list
    options:
      api_endpoint:
        description: Tenable API endpoint
        type: string
        default: 'https://cloud.tenable.com'
        env:
          - name: TENABLE_API_ENDPOINT
      access_key:
        description: Tenable access key
        type: string
        env:
          - name: TENABLE_ACCESS_KEY
      secret_key:
        description: Tenable secret key
        type: string
        env:
          - name: TENABLE_SECRET_KEY
    description:
        - No description
    notes:
        - No notes
'''


class InventoryModule(BaseInventoryPlugin, Constructable):
    """Tenable's assets inventory plugin.
    """

    NAME = 'jpclipffel.tenable.assets'

    def _tenable_load_cfg(self, path: str) -> None:
        """Reads and sets configuration.
        """
        # Read and set config
        cfg = self._read_config_data(path)
        self._tenable_cfg = {
            'api_endpoint': cfg.get(
                'api_endpoint',
                'https://cloud.tenable.com'),
            'access_key': os.environ.get('TENABLE_ACCESS_KEY'),
            'secret_key': os.environ.get('TENABLE_SECRET_KEY')
        }
        # Basic configuration check
        for k, v in self._tenable_cfg.items():
            if not isinstance(v, str) or len(v) < 1:
                raise AnsibleOptionsError((
                    f'Missing, empty or invalid option "{k}" '
                    f'for inventory plugin {self.NAME}'
                ))

    def _tenable_headers(self, headers: dict = {}) -> dict:
        """Returns proper headers for Tenable API usage.

        :param headers: Custom headers
        """
        return {**{
            'X-ApiKeys': (
                f'accessKey={self._tenable_cfg["access_key"]};'
                f'secretKey={self._tenable_cfg["secret_key"]};'
            ),
            'Accept': 'application/json'
        }, **headers}

    def _tenable_api(self, method: str, path: str, headers: dict = {},
            data: dict = {}) -> dict:
        """Interacts with Tenable API.

        :param method:  API method (GET, POST, ...)
        :param path:    API path relative to plugin's API endpoint
        """
        try:
            response = requests.request(
                method=method,
                url=f'{self._tenable_cfg["api_endpoint"]}/{path}',
                headers=self._tenable_headers(headers),
                data=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            raise AnsibleError((
                'Failed to run Tenable API call: '
                f'method="{method}", path="{path}", error="{str(error)}"'
            ))
        except Exception as error:
            raise AnsibleError((
                'Failed to decode Tenable response as JSON: '
                f'method="{method}", path="{path}", error="{str(error)}"'
            ))

    def _tenable_api_assets(self, inventory):
        """Retrieve Tenable assets.
        """
        assets = self._tenable_api('GET', 'assets').get('assets', [])
        for asset in assets:
            # print(json.dumps(asset, indent=2))
            inventory.add_host(asset['hostname'][0])
            # break

    def verify_file(self, path) -> bool:
        return True

    def parse(self, inventory, loader, path, cache):
        super().parse(inventory, loader, path, cache=cache)
        self._tenable_load_cfg(path)
        self._tenable_api_assets(inventory)
