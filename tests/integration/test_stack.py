import json
import os
import unittest
from urllib.request import Request, urlopen


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

    def test_agent_request_crosses_gateway_and_is_audited(self) -> None:
        request = Request(
            "http://localhost:8000/api/v1/agent/run",
            data=json.dumps({"prompt": "Look up customer 1001"}).encode(),
            headers={"Content-Type": "application/json", "X-Request-ID": "integration-safe-1"},
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            payload = json.load(response)

        self.assertEqual(response.status, 200)
        self.assertEqual(payload["request_id"], "integration-safe-1")
        self.assertEqual(payload["decision"]["tool_name"], "get_customer")
        self.assertIsNotNone(payload["tool_call_id"])

        with urlopen("http://localhost:8000/api/v1/agent/tool-calls?limit=10", timeout=5) as response:
            calls = json.load(response)

        matching = [call for call in calls if call["request_id"] == "integration-safe-1"]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["status"], "success")


if __name__ == "__main__":
    unittest.main()
