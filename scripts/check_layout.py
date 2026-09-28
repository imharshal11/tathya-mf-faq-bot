import asyncio
import json
from playwright.async_api import async_playwright

SELECTORS = [
    "#home-view",
    "#chat-view",
    ".bottom-nav",
    ".fund-tiles",
    ".start-chat-btn",
    ".topbar",
    ".sidebar",
    ".main-content",
    ".source-card"
]

STYLE_SELECTORS = {
    ".start-chat-btn": ["background-color", "border-radius", "height"],
    ".tile": ["background-color", "border-radius", "height"],
    ".bottom-nav": ["position", "bottom"]
}

async def check_viewport(page, name, width, height):
    print(f"\n{'='*60}")
    print(f"  {name.upper()} VIEWPORT ({width}x{height})")
    print(f"{'='*60}")
    
    await page.set_viewport_size({"width": width, "height": height})
    await page.wait_for_timeout(500)
    
    # Check visibility of elements
    print("\n--- Element Visibility ---")
    for sel in SELECTORS:
        try:
            el = page.locator(sel).first
            visible = await el.is_visible()
            print(f"  {sel}: {visible}")
        except Exception as e:
            print(f"  {sel}: error - {e}")
    
    # Check computed styles
    print("\n--- Computed Styles ---")
    for sel, props in STYLE_SELECTORS.items():
        try:
            el = page.locator(sel).first
            if await el.count() > 0:
                for prop in props:
                    val = await el.evaluate("(el, prop) => getComputedStyle(el).getPropertyValue(prop)", prop)
                    print(f"  {sel} {prop}: {val}")
            else:
                print(f"  {sel}: NOT FOUND")
        except Exception as e:
            print(f"  {sel}: error - {e}")
    
    # Check styles.css loaded
    print("\n--- Resource Loading ---")
    try:
        response = await page.request.get("http://127.0.0.1:8000/styles.css")
        print(f"  /styles.css HTTP status: {response.status}")
    except Exception as e:
        print(f"  /styles.css: error - {e}")
    
    # Check console errors
    print("\n--- Console Errors ---")
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    await page.reload()
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(500)
    if console_errors:
        for err in console_errors:
            print(f"  ERROR: {err}")
    else:
        print("  (none)")
    
    # Screenshot
    screenshot_path = f"scripts/{name}.png"
    await page.screenshot(path=screenshot_path, full_page=True)
    print(f"\n  Screenshot saved: {screenshot_path}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        
        # Mobile
        await check_viewport(page, "mobile", 390, 844)
        
        # Desktop
        await check_viewport(page, "desktop", 1440, 900)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())