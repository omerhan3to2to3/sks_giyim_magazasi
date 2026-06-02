from pathlib import Path
from typing import Any, Optional

import requests

from client.config import load_config


class ApiError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    HEALTH_TIMEOUT = 2
    REQUEST_TIMEOUT = 10

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or load_config()["server_url"]).rstrip("/")

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(method, url, timeout=self.REQUEST_TIMEOUT, **kwargs)
        except requests.RequestException as exc:
            raise ApiError(f"Sunucuya bağlanılamadı: {exc}") from exc

        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                pass
            raise ApiError(str(detail), response.status_code)

        if response.content:
            return response.json()
        return None

    def health(self) -> bool:
        url = f"{self.base_url}/health"
        try:
            response = requests.get(url, timeout=self.HEALTH_TIMEOUT)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def lookup_card(self, card_uid: str) -> dict:
        return self._request("GET", f"/cards/lookup/{card_uid.upper()}")

    def register_card(self, data: dict) -> dict:
        return self._request("POST", "/cards/register", json=data)

    def topup_card(self, card_uid: str, amount: float) -> dict:
        return self._request("POST", "/cards/topup", json={"card_uid": card_uid, "amount": amount})

    def list_products(self) -> list:
        return self._request("GET", "/products/")

    def create_product(self, data: dict) -> dict:
        return self._request("POST", "/products/", json=data)

    def create_product_with_image(self, fields: dict, image_path: str) -> dict:
        with open(image_path, "rb") as image_file:
            files = {"image": (Path(image_path).name, image_file, "image/jpeg")}
            return self._request("POST", "/products/with-image", data=fields, files=files)

    def purchase(self, card_uid: str, items: list) -> dict:
        return self._request(
            "POST",
            "/sales/purchase",
            json={"card_uid": card_uid, "items": items},
        )

    def get_statistics(self) -> dict:
        return self._request("GET", "/statistics/")
