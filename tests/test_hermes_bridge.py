"""Offline contract tests: no Telegram, video, or paid API calls."""

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("BOT_TOKEN", "123456:test-only")
os.environ.setdefault("OPENAI_API_KEY", "test-only")

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app import hermes_bridge


class UrlTests(unittest.TestCase):
    def test_only_direct_video_urls(self):
        accepted = (
            "https://www.instagram.com/reel/ABC123_/",
            "https://instagram.com/p/ABC123/",
            "https://www.tiktok.com/@owner/video/1234567890",
        )
        rejected = (
            "https://www.instagram.com/owner/",
            "https://www.instagram.com.evil.test/reel/ABC123/",
            "https://www.tiktok.com/@owner",
            "https://127.0.0.1/reel/ABC123/",
            "https://www.instagram.com:bad/reel/ABC123/",
            "http://www.instagram.com/reel/ABC123/",
        )
        for url in accepted:
            self.assertTrue(hermes_bridge.valid_video_url(url), url)
        for url in rejected:
            self.assertFalse(hermes_bridge.valid_video_url(url), url)

    def test_missing_token_disables_routes(self):
        with patch.dict(os.environ, {"HERMES_BRIDGE_TOKEN": ""}):
            self.assertFalse(hermes_bridge.register_bridge_routes(web.Application()))


class HttpTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.token = "offline-test-token-" * 3
        self.app = web.Application(client_max_size=4096)
        with patch.dict(os.environ, {"HERMES_BRIDGE_TOKEN": self.token}):
            self.assertTrue(hermes_bridge.register_bridge_routes(self.app))
        self.client = TestClient(TestServer(self.app))
        await self.client.start_server()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.url = "https://www.instagram.com/reel/ABC123/"
        self.request_id = "4f455cec-94b5-4fcb-9b84-8b6f706c5357"

    async def asyncTearDown(self):
        await self.client.close()

    async def test_status_requires_token_and_does_not_process(self):
        with patch.object(hermes_bridge, "process_video", new_callable=AsyncMock) as process:
            unauthorized = await self.client.get("/v1/hermes/status")
            self.assertEqual(unauthorized.status, 401)
            response = await self.client.get("/v1/hermes/status", headers=self.headers)
            self.assertEqual(response.status, 200)
            self.assertEqual((await response.json())["bridge"], "hermes-v1")
            process.assert_not_awaited()

    async def test_process_is_authenticated_validated_and_deduplicated(self):
        payload = {"url": self.url, "request_id": self.request_id}
        fake_result = {"url": self.url, "analysis": "test analysis"}
        with patch.object(hermes_bridge, "process_video", new=AsyncMock(return_value=fake_result)) as process:
            unauthorized = await self.client.post("/v1/hermes/process", json=payload)
            self.assertEqual(unauthorized.status, 401)
            invalid = await self.client.post(
                "/v1/hermes/process", headers=self.headers,
                json={"url": "https://example.com", "request_id": self.request_id},
            )
            self.assertEqual(invalid.status, 400)
            first = await self.client.post("/v1/hermes/process", headers=self.headers, json=payload)
            self.assertEqual(first.status, 202)
            self.assertEqual((await first.json())["request_id"], self.request_id)
            await asyncio.sleep(0)
            duplicate = await self.client.post("/v1/hermes/process", headers=self.headers, json=payload)
            self.assertEqual(duplicate.status, 200)
            result = await self.client.get(
                f"/v1/hermes/jobs/{self.request_id}", headers=self.headers,
            )
            self.assertEqual(result.status, 200)
            self.assertEqual((await result.json())["result"], fake_result)
            process.assert_awaited_once_with(self.url)
            conflict = await self.client.post(
                "/v1/hermes/process", headers=self.headers,
                json={"url": "https://www.instagram.com/p/XYZ/", "request_id": self.request_id},
            )
            self.assertEqual(conflict.status, 409)

    async def test_only_one_paid_job_runs_and_job_read_requires_auth(self):
        gate = asyncio.Event()

        async def held_process(_url):
            await gate.wait()
            return {"analysis": "finished"}

        payload = {"url": self.url, "request_id": self.request_id}
        with patch.object(hermes_bridge, "process_video", side_effect=held_process) as process:
            first = await self.client.post("/v1/hermes/process", headers=self.headers, json=payload)
            self.assertEqual(first.status, 202)
            duplicate = await self.client.post("/v1/hermes/process", headers=self.headers, json=payload)
            self.assertEqual(duplicate.status, 202)
            other = await self.client.post(
                "/v1/hermes/process", headers=self.headers,
                json={"url": "https://www.instagram.com/p/XYZ/",
                      "request_id": "72743464-cbbe-4b6b-8797-a1e8644d23cf"},
            )
            self.assertEqual(other.status, 429)
            unauthorized = await self.client.get(f"/v1/hermes/jobs/{self.request_id}")
            self.assertEqual(unauthorized.status, 401)
            gate.set()
            await asyncio.sleep(0)
            completed = await self.client.get(
                f"/v1/hermes/jobs/{self.request_id}", headers=self.headers,
            )
            self.assertEqual((await completed.json())["state"], "completed")
            self.assertEqual(process.call_count, 1)
