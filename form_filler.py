"""
SmartCart Agent — Browser Form Filler (Playwright)
Automates checkout form filling with human approval before any purchase.
"""

import asyncio
import json
from playwright.async_api import async_playwright, Page, Browser


# ── Main Browser Agent ────────────────────────────────────────────────────────
class FormFiller:
    def __init__(self):
        self.browser: Browser = None
        self.page: Page = None
        self.learned_workflows = {}  # webcmd-style: cached site knowledge

    async def start(self, headless: bool = False):
        """Launch browser (visible so user can see & approve)."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        self.page = await context.new_page()
        print("✅ Browser started")

    async def stop(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def navigate_to_product(self, url: str) -> bool:
        """Open the product page."""
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_timeout(2000)
            print(f"✅ Navigated to: {url[:60]}...")
            return True
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False

    async def click_add_to_cart(self, site: str) -> bool:
        """Add product to cart based on site."""
        selectors = {
            "amazon": [
                "#add-to-cart-button",
                "input[name='submit.add-to-cart']",
                "#buy-now-button"
            ],
            "flipkart": [
                "._2KpZ6l._2U9uOA._3v1-ww",  # Add to Cart
                "button._2KpZ6l._2U9uOA._3v1-ww",
                "div[class*='_2KpZ6l']"
            ]
        }

        for selector in selectors.get(site, []):
            try:
                btn = await self.page.query_selector(selector)
                if btn:
                    await btn.click()
                    await self.page.wait_for_timeout(2000)
                    print(f"✅ Clicked Add to Cart ({site})")
                    return True
            except Exception:
                continue

        print(f"⚠️ Could not find Add to Cart button for {site}")
        return False

    async def fill_form_field(self, field_name: str, value: str, hints: list[str]) -> bool:
        """Try multiple selectors to fill a form field."""
        selectors = [
            f"[placeholder*='{field_name.lower()}']",
            f"[name*='{field_name.lower()}']",
            f"[id*='{field_name.lower()}']",
            f"[aria-label*='{field_name}']",
        ] + [f"[placeholder*='{h}']" for h in hints]

        for selector in selectors:
            try:
                el = await self.page.query_selector(selector)
                if el:
                    await el.click()
                    await el.fill(value)
                    await self.page.wait_for_timeout(300)
                    print(f"  ✅ Filled '{field_name}' = '{value}'")
                    return True
            except Exception:
                continue

        print(f"  ⚠️ Could not fill '{field_name}' — field not found")
        return False

    async def fill_checkout_form(self, form_plan: dict, user_profile: dict) -> dict:
        """Fill all checkout form fields from the AI-generated plan."""
        results = {"filled": [], "missed": []}

        steps = form_plan.get("steps", [])
        for step in steps:
            field = step.get("field", "")
            value = step.get("value", "")
            hint  = step.get("selector_hint", "").split("/")

            success = await self.fill_form_field(field, value, hint)
            if success:
                results["filled"].append(field)
            else:
                results["missed"].append(field)

        return results

    async def take_screenshot(self, path: str = "screenshot.png") -> str:
        """Take a screenshot for the demo."""
        await self.page.screenshot(path=path, full_page=False)
        return path

    async def get_page_title(self) -> str:
        return await self.page.title()


# ── Sync Wrapper for Streamlit ────────────────────────────────────────────────
def fill_form_sync(product_url: str, site: str, form_plan: dict, user_profile: dict) -> dict:
    """
    Synchronous wrapper — opens browser, navigates to product,
    fills form, takes screenshot. Called from Streamlit.
    """
    async def _run():
        filler = FormFiller()
        await filler.start(headless=False)  # Visible browser!
        result = {
            "success": False,
            "filled_fields": [],
            "missed_fields": [],
            "screenshot": None,
            "message": ""
        }
        try:
            nav_ok = await filler.navigate_to_product(product_url)
            if not nav_ok:
                result["message"] = "Could not open product page"
                return result

            screenshot = await filler.take_screenshot("product_page.png")
            result["screenshot"] = screenshot

            # Note: We stop before checkout — human must approve!
            result["success"] = True
            result["message"] = (
                "✅ Product page opened! "
                "Review and click 'CONFIRM & PROCEED' to continue."
            )
            result["page_title"] = await filler.get_page_title()

            # Keep browser open for human to see
            await asyncio.sleep(5)

        finally:
            await filler.stop()
        return result

    return asyncio.run(_run())


if __name__ == "__main__":
    # Quick test — open Amazon product page
    test_url = "https://www.amazon.in/dp/B09B8YWXDF"
    result = fill_form_sync(test_url, "amazon", {}, {})
    print(result)
