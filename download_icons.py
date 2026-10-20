import re
import time
from html.parser import HTMLParser
from pathlib import Path

import requests

from game_data_manager import GameDataManager

OUT_DIR = Path("frontend/public/assets")
for sub in ["heroes", "skills", "trinkets"]:
    (OUT_DIR / sub).mkdir(parents=True, exist_ok=True)

WIKI_BASE = "https://darkestdungeon.wiki.gg"
session = requests.Session()
session.headers.update({"User-Agent": "DarkestGenerator/3.0 (AssetSync)"})


def is_valid_image(data: bytes) -> bool:
    """Ensures file content is a valid image and not an audio file (.wav) or HTML error."""
    if len(data) < 100:
        return False
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if data.startswith(b"\xff\xd8"):
        return True
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return True
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return True
    return False


def clean_corrupt_files():
    """Purges any non-image files saved during previous runs (e.g. .wav files)."""
    for file_path in OUT_DIR.rglob("*.png"):
        if file_path.is_file():
            try:
                if not is_valid_image(file_path.read_bytes()):
                    print(f"[PURGE] Removing invalid/corrupt file: {file_path.name}")
                    file_path.unlink()
            except Exception:
                pass


def to_full_image_url(url: str) -> str:
    """Converts MediaWiki thumbnail URLs into direct master asset URLs."""
    if url.startswith("/"):
        url = WIKI_BASE + url
    m = re.match(
        r"(https?://[^/]+/images)/thumb/([0-9a-fA-F]/[0-9a-fA-F]{2}/[^/]+)/.*", url
    )
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return url


def download_and_save(img_url: str, dest_path: Path) -> bool:
    """Attempts to download full image or fallback thumbnail, verifying magic bytes."""
    if dest_path.exists() and is_valid_image(dest_path.read_bytes()):
        return True

    full_url = to_full_image_url(img_url)
    for u in [full_url, img_url]:
        try:
            resp = session.get(u, timeout=12)
            if resp.status_code == 200 and is_valid_image(resp.content):
                dest_path.write_bytes(resp.content)
                print(f"[OK] Saved {dest_path.name}")
                return True
        except Exception:
            pass
    return False


class WikiTableParser(HTMLParser):
    """Extracts infobox portraits and table row image-text associations."""

    def __init__(self):
        super().__init__()
        self.infobox_images: list[str] = []
        self.row_images: list[tuple[str, list[str]]] = []
        self._in_infobox = False
        self._in_tr = False
        self._cur_row_text: list[str] = []
        self._cur_row_images: list[str] = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        classes = attr_dict.get("class", "").split()

        if tag in ("table", "aside"):
            if any("infobox" in c or "pi-layout" in c for c in classes):
                self._in_infobox = True

        if tag == "tr":
            self._in_tr = True
            self._cur_row_text = []
            self._cur_row_images = []

        if tag == "img":
            src = attr_dict.get("data-src") or attr_dict.get("src") or ""
            alt = attr_dict.get("alt", "")
            title = attr_dict.get("title", "")
            if src and not src.startswith("data:"):
                # Ignore non-icon UI graphics
                if not any(
                    skip in src.lower()
                    for skip in ["rarity", "gold.png", "crest.png", "portrait.png"]
                ):
                    if self._in_infobox and len(self.infobox_images) < 4:
                        self.infobox_images.append(src)
                    if self._in_tr:
                        self._cur_row_images.append(src)
            if self._in_tr:
                if alt:
                    self._cur_row_text.append(alt)
                if title:
                    self._cur_row_text.append(title)

        if tag == "a" and self._in_tr:
            title = attr_dict.get("title", "")
            if title:
                self._cur_row_text.append(title)

    def handle_endtag(self, tag):
        if tag in ("table", "aside"):
            self._in_infobox = False
        if tag == "tr":
            self._in_tr = False
            combined_text = " ".join(self._cur_row_text).strip()
            if combined_text and self._cur_row_images:
                self.row_images.append((combined_text, self._cur_row_images))

    def handle_data(self, data):
        if self._in_tr:
            t = data.strip()
            if t:
                self._cur_row_text.append(t)


def fetch_page_html(page_name: str) -> str:
    url = f"{WIKI_BASE}/wiki/{page_name.strip().replace(' ', '_')}"
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        print(f"[WARN] Failed fetching page {page_name}: {e}")
    return ""


def main():
    clean_corrupt_files()
    gman = GameDataManager()

    print("--- 1. Resolving Heroes & Combat Skills via Hero Articles ---")
    for hero in gman.heroes:
        hero_dest = OUT_DIR / "heroes" / f"{hero.class_name}.png"
        hero_html = fetch_page_html(hero.class_name)

        if not hero_html:
            print(f"[FAIL] Could not load wiki page for hero: {hero.class_name}")
            continue

        parser = WikiTableParser()
        parser.feed(hero_html)

        # 1.1 Hero Portrait from Infobox
        if not (hero_dest.exists() and is_valid_image(hero_dest.read_bytes())):
            saved = False
            for img_url in parser.infobox_images:
                if download_and_save(img_url, hero_dest):
                    saved = True
                    break
            if not saved:
                print(
                    f"[FAIL] Could not locate infobox portrait for: {hero.class_name}"
                )

        # 1.2 Skills from Ability Table Rows
        for skill in hero.combat_skills:
            skill_dest = OUT_DIR / "skills" / f"{skill.name}.png"
            if skill_dest.exists() and is_valid_image(skill_dest.read_bytes()):
                continue

            # Handle Transform aliases
            search_name = "Transform" if "Transform" in skill.name else skill.name
            target_norm = search_name.replace("!", "").strip().lower()

            found_skill = False
            for row_text, row_imgs in parser.row_images:
                if target_norm in row_text.lower():
                    for s_img in row_imgs:
                        if download_and_save(s_img, skill_dest):
                            found_skill = True
                            break
                if found_skill:
                    break

            if not found_skill:
                print(f"[FAIL] Could not find skill image for: {skill.name}")

        time.sleep(0.05)

    print("\n--- 2. Resolving Trinkets via Wiki Master Tables ---")
    trinket_pages = [
        "Trinkets",
        "Color_of_Madness_(DLC)",
        "Crimson_Court_(DLC)",
    ]

    all_trinket_rows: list[tuple[str, list[str]]] = []
    for t_page in trinket_pages:
        html = fetch_page_html(t_page)
        if html:
            t_parser = WikiTableParser()
            t_parser.feed(html)
            all_trinket_rows.extend(t_parser.row_images)
        time.sleep(0.05)

    for trinket in gman.usable_trinkets:
        t_dest = OUT_DIR / "trinkets" / f"{trinket.name}.png"
        if t_dest.exists() and is_valid_image(t_dest.read_bytes()):
            continue

        clean_t_name = trinket.name.lower()
        saved = False

        for row_text, row_imgs in all_trinket_rows:
            if clean_t_name in row_text.lower():
                for t_img in row_imgs:
                    if download_and_save(t_img, t_dest):
                        saved = True
                        break
            if saved:
                break

        # Fallback: Query the trinket's dedicated page directly if missed in the tables
        if not saved:
            t_html = fetch_page_html(trinket.name)
            if t_html:
                single_parser = WikiTableParser()
                single_parser.feed(t_html)
                for t_img in single_parser.infobox_images:
                    if download_and_save(t_img, t_dest):
                        saved = True
                        break

        if not saved:
            print(f"[FAIL] Could not resolve trinket image for: {trinket.name}")


if __name__ == "__main__":
    main()
