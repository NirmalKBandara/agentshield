import json
import os
import unittest
from urllib.request import urlopen


@unittest.skipUnless(os.getenv("RUN_INTEGRATION") == "1", "set RUN_INTEGRATION=1")
class StackIntegrationTest(unittest.TestCase):
    def test_frontend_proxy_reaches_backend(self) -> None:
        with urlopen("http://localhost:3000/api/backend-health", timeout=5) as response:
            payload = json.load(response)
            status = response.status

        self.assertEqual(status, 200)
        self.assertEqual(payload, {"status": "ok", "service": "agentshield-api"})

    def test_backend_is_database_ready(self) -> None:
        with urlopen("http://localhost:8000/api/v1/ready", timeout=5) as response:
            payload = json.load(response)
            status = response.status

        self.assertEqual(status, 200)
        self.assertEqual(payload["database"], "connected")


if __name__ == "__main__":
    unittest.main()
