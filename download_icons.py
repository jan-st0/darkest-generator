import argparse
import concurrent.futures
import html
import re
import unicodedata
from collections import defaultdict
from difflib import get_close_matches
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from game_data_manager import GameDataManager

OUT_DIR = Path("frontend/public/assets")
for sub in ["heroes", "skills", "trinkets"]:
    (OUT_DIR / sub).mkdir(parents=True, exist_ok=True)

WIKI_BASE = "https://darkestdungeon.wiki.gg"
API_URL = f"{WIKI_BASE}/api.php"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

HERO_ABBREVIATIONS: dict[str, list[str]] = {
    "Abomination": ["ab", "abom"],
    "Antiquarian": ["aq", "ant"],
    "Arbalest": ["ar", "arb"],
    "Bounty Hunter": ["bh"],
    "Crusader": ["cr", "cru"],
    "Flagellant": ["fl", "flag"],
    "Grave Robber": ["gr"],
    "Hellion": ["hl", "hel"],
    "Highwayman": ["hwm"],
    "Houndmaster": ["hm"],
    "Jester": ["js", "jes"],
    "Leper": ["le", "lep"],
    "Man-at-Arms": ["maa"],
    "Musketeer": ["ms", "musk"],
    "Occultist": ["occ"],
    "Plague Doctor": ["pd"],
    "Shieldbreaker": ["sb"],
    "Vestal": ["ve", "ves"],
}

# Explicit aliases mapping display names to internal Red Hook / Wiki asset names
KNOWN_SKILL_ALIASES: dict[str, list[str]] = {
    "Target Whistle": ["whistle", "hm_whistle", "houndmaster_whistle"],
    "Transform (to Beast)": ["transform", "transform_beast", "ab_transform"],
    "Transform (to Human)": ["transform", "transform_human", "ab_transform"],
    "Rain of Sorrows": ["rain_of_sorrows", "fl_rain_of_sorrows", "icon_flagellant_rain_of_sorrows"],
    "Exsanguinate": ["exsanguinate", "fl_exsanguinate", "icon_flagellant_exsanguinate"],
    "Redeem": ["redeem", "fl_redeem", "icon_flagellant_redeem"],
    "Endure": ["endure", "fl_endure", "icon_flagellant_endure"],
    "Call the Shot": [
        "call_the_shot", "musketeer_call_the_shot", "icon_musketeer_call_the_shot",
        "musketeer_mark", "ms_call_the_shot", "calltheshot", "sniper's_mark"
    ],
    "Patch Up": [
        "patch_up", "musketeer_patch_up", "icon_musketeer_patch_up",
        "musketeer_bandage", "musketeer_heal", "ms_patch_up", "patchup"
    ],
    "Pierce": ["pierce", "sb_pierce", "shieldbreaker_pierce", "shieldbreaker_spear", "icon_shieldbreaker_pierce"],
    "Puncture": [
        "puncture", "sb_puncture", "shieldbreaker_puncture",
        "shieldbreaker_pull", "shieldbreaker_hook", "icon_shieldbreaker_puncture"
    ],
    "Adder's Kiss": ["adders_kiss", "adder_kiss", "sb_adders_kiss", "shieldbreaker_kiss"],
    "Impale": ["impale", "sb_impale", "shieldbreaker_impale", "shieldbreaker_aoe"],
    "Expose": ["expose", "sb_expose", "shieldbreaker_expose", "shieldbreaker_debuff"],
    "Captivate": [
        "captivate", "sb_captivate", "shieldbreaker_captivate",
        "shieldbreaker_mark", "shieldbreaker_hold", "icon_shieldbreaker_captivate"
    ],
    "Serpent Sway": [
        "serpent_sway", "serpents_sway", "shieldbreaker_sway",
        "shieldbreaker_serpent_sway", "sb_serpent_sway", "icon_shieldbreaker_serpent_sway"
    ],
}

HEIRLOOM_FILENAMES = {
    "crest.png", "deed.png", "bust.png", "portrait.png",
    "gold.png", "shard.png", "heirloom_crest.png", "item_crest.png"
}

VALID_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(pool_connections=30, pool_maxsize=30, max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# =====================================================================
# 1. Validation & String Normalization
# =====================================================================

def is_valid_image(data: bytes) -> bool:
    if len(data) < 100:
        return False
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if data.startswith(b"\xff\xd8"):
        return True
    if data.startswith(b"RIFF") and len(data) > 12 and data[8:12] == b"WEBP":
        return True
    if data.startswith((b"GIF87a", b"GIF89a")):
        return True
    return False


def clean_corrupt_files():
    purged = 0
    for file_path in OUT_DIR.rglob("*.png"):
        if file_path.is_file():
            try:
                if not is_valid_image(file_path.read_bytes()):
                    file_path.unlink()
                    purged += 1
            except Exception:
                pass
    if purged > 0:
        print(f"[CLEANUP] Purged {purged} invalid/empty files.")


def normalize_token(text: str) -> str:
    t = html.unescape(text)
    t = unicodedata.normalize("NFKD", t)
    t = t.replace("’", "").replace("'", "").replace("`", "")
    return re.sub(r"[^\w]", "", t).strip().lower()


def generate_search_variants(name: str, hero_class: Optional[str] = None) -> list[str]:
    """Generates lexical and prefix variants for a target asset."""
    base_variants = [name]

    if name in KNOWN_SKILL_ALIASES:
        base_variants.extend(KNOWN_SKILL_ALIASES[name])

    if "'s" in name or "’s" in name:
        base_variants.append(name.replace("'s", "").replace("’s", ""))
        base_variants.append(name.replace("'s", "s").replace("’s", "s"))

    expanded = list(base_variants)
    if hero_class:
        clean_hero = hero_class.lower().replace(" ", "_").replace("-", "_")
        for v in base_variants:
            expanded.append(f"{clean_hero}_{v}")
            expanded.append(f"icon_{clean_hero}_{v}")
            for abbrev in HERO_ABBREVIATIONS.get(hero_class, []):
                expanded.append(f"{abbrev}_{v}")
                expanded.append(f"icon_{abbrev}_{v}")

    seen = set()
    deduped = []
    for v in expanded:
        v_clean = v.strip()
        if v_clean and v_clean not in seen:
            seen.add(v_clean)
            deduped.append(v_clean)
    return deduped


def to_full_image_url(url: str) -> str:
    if url.startswith("/"):
        url = WIKI_BASE + url
    m = re.match(r"(https?://[^/]+/images)/thumb/([0-9a-fA-F]/[0-9a-fA-F]{2}/[^/]+)/.*", url)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return url


# =====================================================================
# 2. Bulk Catalog Indexing (Strictly Filtered to Images)
# =====================================================================

def build_wiki_file_catalog(session: requests.Session) -> dict[str, str]:
    """Indexes all image files in the wiki, ignoring audio (.wav/.ogg) and stripping prefixes."""
    catalog: dict[str, str] = {}
    aicontinue: Optional[str] = None
    total_images = 0

    prefixes_to_strip = [
        "icon_", "icon", "inv_", "inv", "trinket_", "trinket", "skill_", "skill", "hero_", "hero"
    ]
    for abbrevs in HERO_ABBREVIATIONS.values():
        for a in abbrevs:
            prefixes_to_strip.extend([f"icon_{a}_", f"{a}_", a])
    for hero_name in HERO_ABBREVIATIONS.keys():
        h_clean = hero_name.lower().replace(" ", "_").replace("-", "_")
        prefixes_to_strip.extend([f"icon_{h_clean}_", f"{h_clean}_", h_clean])

    print("[CATALOG] Indexing wiki image namespace...")
    while True:
        params = {
            "action": "query",
            "list": "allimages",
            "ailimit": "500",
            "aiprop": "url",
            "format": "json",
        }
        if aicontinue:
            params["aicontinue"] = aicontinue

        try:
            resp = session.get(API_URL, params=params, timeout=(3.05, 10))
            if resp.status_code != 200:
                break
            data = resp.json()
            images = data.get("query", {}).get("allimages", [])
            for img in images:
                name = img.get("name", "")
                url = img.get("url", "")
                if not name or not url:
                    continue

                ext = Path(name).suffix.lower()
                if ext not in VALID_IMAGE_EXTENSIONS:
                    continue

                total_images += 1
                stem = Path(name).stem
                raw_clean = normalize_token(name)
                stem_clean = normalize_token(stem)

                catalog[raw_clean] = url
                catalog[stem_clean] = url

                # Strip qualifiers like (Darkest Dungeon), (DD1), (DLC), or trailing numbers (camp4, sway4)
                no_parens = re.sub(r"\(.*?\)", "", stem).strip()
                no_parens_clean = normalize_token(no_parens)
                if no_parens_clean:
                    catalog.setdefault(no_parens_clean, url)

                no_trailing_num = re.sub(r"[0-9]+$", "", no_parens_clean)
                if no_trailing_num and len(no_trailing_num) >= 4:
                    catalog.setdefault(no_trailing_num, url)

                # Strip prefixes (icon_flagellant_, sb_, inv_, etc.)
                for p in prefixes_to_strip:
                    p_tok = normalize_token(p)
                    if stem_clean.startswith(p_tok):
                        stripped = stem_clean[len(p_tok):]
                        if stripped and len(stripped) >= 3:
                            catalog.setdefault(stripped, url)

            if "continue" in data and "aicontinue" in data["continue"]:
                aicontinue = data["continue"]["aicontinue"]
            else:
                break
        except Exception as e:
            print(f"[WARN] Catalog pagination interrupted: {e}")
            break

    print(f"[CATALOG] Indexed {total_images} image files into {len(catalog)} lookup keys.")
    return catalog


# =====================================================================
# 3. Nesting-Safe HTML Table Scraper
# =====================================================================

class FastTableParser(HTMLParser):
    """Parses wiki tables while preserving outer row state across nested sub-tables."""

    def __init__(self):
        super().__init__()
        self.infobox_images: list[str] = []
        self.row_entries: list[dict] = []
        self._in_infobox = False
        self._tr_depth = 0
        self._row_text: list[str] = []
        self._row_images: list[dict] = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        classes = attr_dict.get("class", "").split()

        if tag in ("table", "aside"):
            if any(c in ["infobox", "pi-layout", "portable-infobox"] for c in classes):
                self._in_infobox = True

        if tag == "tr":
            if self._tr_depth == 0:
                self._row_text = []
                self._row_images = []
            self._tr_depth += 1

        if tag == "img":
            src = attr_dict.get("data-src") or attr_dict.get("src") or ""
            alt = attr_dict.get("alt", "")
            title = attr_dict.get("title", "")

            if src and not src.startswith("data:"):
                fname = Path(src.split("?")[0]).name.lower()
                ext = Path(fname).suffix.lower()
                if fname not in HEIRLOOM_FILENAMES and ext in VALID_IMAGE_EXTENSIONS:
                    if self._in_infobox and len(self.infobox_images) < 4:
                        self.infobox_images.append(src)
                    if self._tr_depth > 0:
                        self._row_images.append({"src": src, "alt": alt, "title": title})

            if self._tr_depth > 0:
                if alt:
                    self._row_text.append(alt)
                if title:
                    self._row_text.append(title)

        if tag == "a" and self._tr_depth > 0:
            title = attr_dict.get("title", "")
            if title:
                self._row_text.append(title)

    def handle_endtag(self, tag):
        if tag in ("table", "aside"):
            self._in_infobox = False
        if tag == "tr" and self._tr_depth > 0:
            self._tr_depth -= 1
            if self._tr_depth == 0:
                combined = " ".join(self._row_text).strip()
                if combined and self._row_images:
                    self.row_entries.append({
                        "text": combined,
                        "token": normalize_token(combined),
                        "images": self._row_images,
                    })

    def handle_data(self, data):
        if self._tr_depth > 0:
            t = data.strip()
            if t:
                self._row_text.append(t)


def fetch_page_tables(page_name: str, session: requests.Session) -> tuple[str, int, list[str], list[dict]]:
    url = f"{WIKI_BASE}/wiki/{quote(page_name.strip().replace(' ', '_'))}"
    try:
        resp = session.get(url, timeout=(3.05, 8))
        if resp.status_code == 200:
            parser = FastTableParser()
            parser.feed(resp.text)
            return page_name, resp.status_code, parser.infobox_images, parser.row_entries
        return page_name, resp.status_code, [], []
    except Exception:
        return page_name, 0, [], []


# =====================================================================
# 4. Multi-Tier Resolver with Provenance & Diagnostics
# =====================================================================

def score_row_image(img_meta: dict, target_tokens: list[str]) -> int:
    src = img_meta.get("src", "").lower()
    alt = img_meta.get("alt", "").lower()
    title = img_meta.get("title", "").lower()
    combined_token = normalize_token(f"{src} {alt} {title}")

    for t in target_tokens:
        if t and t in combined_token:
            return -100

    score = 0
    for pat in [
        "launch", "target", "pos1", "pos2", "pos3", "pos4", "rank",
        "bleed", "blight", "stun", "debuff", "buff", "mark", "stress",
        "heal", "stealth", "guard", "riposte", "horror", "aegis"
    ]:
        if pat in src or pat in alt:
            score += 40
    return score


def resolve_image_url(
    target_name: str,
    catalog: dict[str, str],
    page_row_map: dict[str, list[dict]],
    hero_class: Optional[str] = None,
    is_hero: bool = False,
) -> tuple[Optional[str], str]:
    variants = generate_search_variants(target_name, hero_class)
    tokens = [normalize_token(v) for v in variants if v]

    # 1. Hero portrait specific patterns
    if is_hero:
        for t in tokens:
            for pat in [f"{t}portrait", f"portrait{t}", f"{t}hero"]:
                if pat in catalog:
                    return catalog[pat], f"Catalog: Hero Portrait ({pat})"

    # 2. Direct catalog lookups across all generated variants
    for v in variants:
        t = normalize_token(v)
        if t in catalog:
            return catalog[t], f"Catalog: Direct ('{v}')"
        for prefix in ["icon", "inv", "trinket", "skill"]:
            cand = f"{prefix}{t}"
            if cand in catalog:
                return catalog[cand], f"Catalog: Prefixed ('{cand}')"

    # 3. Table row searches (prioritize relevant hero pages first)
    search_pages = []
    if hero_class:
        for p_cand in [hero_class, f"{hero_class}_(Darkest_Dungeon)"]:
            if p_cand in page_row_map:
                search_pages.append(p_cand)
    search_pages.extend([p for p in page_row_map.keys() if p not in search_pages])

    primary_token = normalize_token(target_name)
    for p in search_pages:
        for row in page_row_map[p]:
            if primary_token in row["token"] or any(t in row["token"] for t in tokens[:3]):
                sorted_imgs = sorted(row["images"], key=lambda im: score_row_image(im, tokens))
                if sorted_imgs:
                    return sorted_imgs[0]["src"], f"Table: {p} (Row Match)"

    # 4. Fuzzy catalog matching
    for t in tokens:
        if len(t) >= 5:
            matches = get_close_matches(t, catalog.keys(), n=1, cutoff=0.82)
            if matches:
                return catalog[matches[0]], f"Catalog: Fuzzy ('{t}' -> '{matches[0]}')"

    return None, "Not Found"


def diagnose_failure(
    target_name: str,
    asset_type: str,
    hero_class: Optional[str],
    catalog: dict[str, str],
    page_row_map: dict[str, list[dict]],
):
    variants = generate_search_variants(target_name, hero_class)
    tokens = [normalize_token(v) for v in variants if v]

    all_fuzzy = []
    for t in tokens[:5]:
        all_fuzzy.extend(get_close_matches(t, catalog.keys(), n=3, cutoff=0.65))
    all_fuzzy = list(dict.fromkeys(all_fuzzy))[:6]

    page_status = "Not Scraped"
    if hero_class and hero_class in page_row_map:
        page_status = f"Scraped ({len(page_row_map[hero_class])} rows)"

    print(f"\n[DIAGNOSTIC] Asset Miss: {asset_type} '{target_name}'")
    print(f"  * Hero Context   : {hero_class or 'Generic'}")
    print(f"  * Tokens Tested  : {tokens[:6]} (and {max(0, len(tokens) - 6)} more)")
    print(f"  * Hero Page State: {page_status}")
    if all_fuzzy:
        print(f"  * Catalog Close Matches (Cutoff 0.65): {all_fuzzy}")
        print("  * Diagnosis      : SEARCH issue (Add matching catalog key to KNOWN_SKILL_ALIASES).")
    else:
        print("  * Catalog Close Matches : None found.")
        print("  * Diagnosis      : SOURCE issue (Wiki lacks a matching image file).")


# =====================================================================
# 5. MediaWiki API Search Fallback
# =====================================================================

def query_mediawiki_api_search(name: str, session: requests.Session) -> Optional[str]:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"{name} png",
        "srnamespace": "6",
        "format": "json",
    }
    try:
        res = session.get(API_URL, params=params, timeout=(3.05, 8)).json()
        results = res.get("query", {}).get("search", [])
        for r in results:
            title = r.get("title", "")
            clean_filename = title.replace("File:", "").strip()
            if Path(clean_filename).suffix.lower() in VALID_IMAGE_EXTENSIONS:
                url = f"{WIKI_BASE}/wiki/Special:FilePath/{quote(clean_filename)}"
                resp = session.get(url, allow_redirects=True, timeout=(3.05, 8))
                if resp.status_code == 200 and is_valid_image(resp.content):
                    return resp.url
    except Exception:
        pass
    return None


# =====================================================================
# 6. Concurrent Download & Audit
# =====================================================================

def download_file_task(url: str, dest_path: Path, session: requests.Session) -> bool:
    full_url = to_full_image_url(url)
    for u in [full_url, url]:
        try:
            resp = session.get(u, timeout=(3.05, 8))
            if resp.status_code == 200 and is_valid_image(resp.content):
                dest_path.write_bytes(resp.content)
                return True
        except Exception:
            pass
    return False


def check_missing_icons(gman: GameDataManager) -> dict[str, list[str]]:
    missing = {"heroes": [], "skills": [], "trinkets": []}

    for hero in gman.heroes:
        p = OUT_DIR / "heroes" / f"{hero.class_name}.png"
        if not (p.exists() and is_valid_image(p.read_bytes())):
            missing["heroes"].append(hero.class_name)

        for skill in hero.combat_skills:
            sp = OUT_DIR / "skills" / f"{skill.name}.png"
            if not (sp.exists() and is_valid_image(sp.read_bytes())):
                if skill.name not in missing["skills"]:
                    missing["skills"].append(skill.name)

    for trinket in gman.trinkets:
        tp = OUT_DIR / "trinkets" / f"{trinket.name}.png"
        if not (tp.exists() and is_valid_image(tp.read_bytes())):
            missing["trinkets"].append(trinket.name)

    return missing


def print_status_report(gman: GameDataManager):
    missing = check_missing_icons(gman)
    total_heroes = len(gman.heroes)
    total_skills = len({s.name for h in gman.heroes for s in h.combat_skills})
    total_trinkets = len(gman.trinkets)

    h_cur = total_heroes - len(missing["heroes"])
    s_cur = total_skills - len(missing["skills"])
    t_cur = total_trinkets - len(missing["trinkets"])

    print("\n" + "=" * 70)
    print("DARKEST GENERATOR - ASSET AUDIT REPORT")
    print("=" * 70)
    print(f"  Heroes   : {h_cur:3d} / {total_heroes:3d} ({h_cur / total_heroes * 100:5.1f}%)")
    print(f"  Skills   : {s_cur:3d} / {total_skills:3d} ({s_cur / total_skills * 100:5.1f}%)")
    print(f"  Trinkets : {t_cur:3d} / {total_trinkets:3d} ({t_cur / total_trinkets * 100:5.1f}%)")
    print("-" * 70)
    total_expected = total_heroes + total_skills + total_trinkets
    total_present = h_cur + s_cur + t_cur
    print(f"  Overall  : {total_present:3d} / {total_expected:3d} ({total_present / total_expected * 100:5.1f}%)")
    print("=" * 70)

    if missing["heroes"]:
        print(f"\n[Missing Heroes ({len(missing['heroes'])})]:\n  " + ", ".join(missing["heroes"]))
    if missing["skills"]:
        print(f"\n[Missing Skills ({len(missing['skills'])})]:\n  " + ", ".join(missing["skills"]))
    if missing["trinkets"]:
        sample = missing["trinkets"][:15]
        suffix = f" ... and {len(missing['trinkets']) - 15} more" if len(missing["trinkets"]) > 15 else ""
        print(f"\n[Missing Trinkets ({len(missing['trinkets'])})]:\n  " + ", ".join(sample) + suffix)
    print()


# =====================================================================
# 7. Pipeline Orchestration
# =====================================================================

def sync_assets(force: bool = False):
    clean_corrupt_files()
    gman = GameDataManager()
    session = create_session()

    # Fast pre-check: Only run heavy scraping if items are actually missing
    missing_before = check_missing_icons(gman)
    total_missing = sum(len(v) for v in missing_before.values())
    if not force and total_missing == 0:
        print("[AUDIT] All 431 assets are already present and verified!")
        print_status_report(gman)
        return

    # Step 1: Bulk API indexing
    catalog = build_wiki_file_catalog(session)

    # Step 2: Scrape articles (removed dead 404 DLC URLs)
    print("\n[SCRAPE] Fetching master tables and hero articles...")
    pages_to_fetch = ["Trinkets"] + [h.class_name for h in gman.heroes]
    for dlc_hero in ["Shieldbreaker", "Flagellant", "Musketeer"]:
        pages_to_fetch.append(f"{dlc_hero}_(Darkest_Dungeon)")

    page_row_map: dict[str, list[dict]] = defaultdict(list)
    hero_infobox_map: dict[str, list[str]] = defaultdict(list)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_page_tables, page, session): page for page in pages_to_fetch}
        for future in concurrent.futures.as_completed(futures):
            page_name, status_code, infobox_imgs, row_entries = future.result()
            if status_code == 200:
                print(f"  [SCRAPE] [200 OK] {page_name:<32} ({len(row_entries):3d} outer rows parsed)")
                if infobox_imgs:
                    hero_infobox_map[page_name].extend(infobox_imgs)
                if row_entries:
                    page_row_map[page_name].extend(row_entries)
            else:
                print(f"  [SCRAPE] [{status_code or 'FAIL':>6}] {page_name:<32} (Skipped)")

    # Step 3: Match URLs
    print("\n[MATCH] Resolving image URLs with provenance tracking...")
    download_queue: list[tuple[str, Path, str]] = []
    source_stats: dict[str, int] = defaultdict(int)
    unresolved_items: list[tuple[str, str, Optional[str]]] = []

    # 3.1 Heroes
    for hero in gman.heroes:
        dest = OUT_DIR / "heroes" / f"{hero.class_name}.png"
        if not force and dest.exists() and is_valid_image(dest.read_bytes()):
            continue

        url = None
        source = ""
        if hero.class_name in hero_infobox_map and hero_infobox_map[hero.class_name]:
            url = hero_infobox_map[hero.class_name][0]
            source = f"Infobox ({hero.class_name})"

        if not url:
            url, source = resolve_image_url(
                hero.class_name, catalog, page_row_map, hero_class=hero.class_name, is_hero=True
            )

        if not url:
            url = query_mediawiki_api_search(f"{hero.class_name} portrait", session)
            source = "MediaWiki API Search" if url else "Not Found"

        if url:
            source_stats[source.split(":")[0]] += 1
            download_queue.append((url, dest, f"Hero: {hero.class_name} [{source}]"))
        else:
            unresolved_items.append((hero.class_name, "Hero", None))

    # 3.2 Skills
    for hero in gman.heroes:
        for skill in hero.combat_skills:
            dest = OUT_DIR / "skills" / f"{skill.name}.png"
            if not force and dest.exists() and is_valid_image(dest.read_bytes()):
                continue

            url, source = resolve_image_url(
                skill.name, catalog, page_row_map, hero_class=hero.class_name
            )

            if not url:
                url = query_mediawiki_api_search(f"{hero.class_name} {skill.name}", session)
                source = "MediaWiki API Search" if url else "Not Found"

            if url:
                source_stats[source.split(":")[0]] += 1
                download_queue.append((url, dest, f"Skill: {skill.name} [{source}]"))
            else:
                unresolved_items.append((skill.name, "Skill", hero.class_name))

    # 3.3 Trinkets
    for trinket in gman.trinkets:
        dest = OUT_DIR / "trinkets" / f"{trinket.name}.png"
        if not force and dest.exists() and is_valid_image(dest.read_bytes()):
            continue

        url, source = resolve_image_url(
            trinket.name, catalog, page_row_map, hero_class=trinket.class_restriction
        )

        if not url:
            url = query_mediawiki_api_search(trinket.name, session)
            source = "MediaWiki API Search" if url else "Not Found"

        if url:
            source_stats[source.split(":")[0]] += 1
            download_queue.append((url, dest, f"Trinket: {trinket.name} [{source}]"))
        else:
            unresolved_items.append((trinket.name, "Trinket", trinket.class_restriction))

    print(f"\n[MATCH] Successfully queued {len(download_queue)} assets.")
    if source_stats:
        print("  Resolution breakdown by source:")
        for src, count in sorted(source_stats.items(), key=lambda x: -x[1]):
            print(f"    - {src:<20}: {count:3d}")

    # Step 4: Parallel Downloads across 16 workers
    if download_queue:
        print(f"\n[DOWNLOAD] Downloading {len(download_queue)} assets across 16 threads...")
        completed = 0
        total_downloads = len(download_queue)

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            future_map = {
                executor.submit(download_file_task, url, dest, session): (desc, dest)
                for url, dest, desc in download_queue
            }
            for future in concurrent.futures.as_completed(future_map):
                desc, dest = future_map[future]
                success = future.result()
                completed += 1
                if success:
                    print(f"  [{completed:3d}/{total_downloads:3d}] Downloaded: {desc}")
                else:
                    print(f"  [DOWNLOAD FAIL] Could not save {desc}")

    # Step 5: Failure Diagnostics
    if unresolved_items:
        print("\n" + "=" * 70)
        print("DIAGNOSTICS: UNRESOLVED ASSETS")
        print("=" * 70)
        for name, a_type, h_class in unresolved_items:
            diagnose_failure(name, a_type, h_class, catalog, page_row_map)

    print("\n--- Download process finished. Verifying local repository ---")
    print_status_report(gman)


def main():
    parser = argparse.ArgumentParser(description="Darkest Generator Asset Manager")
    parser.add_argument("--check", "--audit", action="store_true", help="Audit local assets and exit")
    parser.add_argument("--force", action="store_true", help="Force redownloading all assets")
    args = parser.parse_args()

    gman = GameDataManager()
    if args.check:
        print_status_report(gman)
    else:
        sync_assets(force=args.force)


if __name__ == "__main__":
    main()