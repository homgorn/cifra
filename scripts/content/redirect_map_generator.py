#!/usr/bin/env python3
"""
Redirect Map Generator — 301 редиректы Bitrix → WP
Вход: Битрикс экспорт статей + каталог
Выход: nginx/htaccess редиректы + CSV для проверки
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

BITRIX_EXPORT_DIR = Path("data/exports/bitrix/latest")
OUTPUT_DIR = Path("scripts/dev-fixes/redirects")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WP_SUBDOMAIN = "blog.cifra18.рф"  # или articles.cifra18.рф
BITRIX_DOMAIN = "xn--18-6kc5a3bxam.xn--p1ai"

def generate_article_redirects():
    """Редиректы для 290 статей: /news/* → /blog/*"""
    input_file = BITRIX_EXPORT_DIR / "articles_290.csv"
    if not input_file.exists():
        return []
    
    redirects = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            old_url = row.get('detail_page_url', '')
            if not old_url:
                continue
            
            # Парсим старый URL
            parsed = urlparse(old_url)
            old_path = parsed.path
            
            # Битрикс обычно: /news/YYYY-MM-DD-slug/ или /news/detail/ID/
            # WP будет: /blog/slug/ (без даты)
            
            # Извлекаем slug
            path_parts = [p for p in old_path.split('/') if p]
            if len(path_parts) >= 2 and path_parts[0] == 'news':
                # Пробуем найти slug без даты
                slug_candidate = path_parts[-1]
                # Удаляем дату в начале если есть: YYYY-MM-DD-
                import re
                slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', slug_candidate)
                slug = slug.rstrip('/')
                
                new_path = f"/blog/{slug}/"
                redirects.append({
                    "source": old_path,
                    "destination": f"https://{WP_SUBDOMAIN}{new_path}",
                    "type": "article",
                    "bitrix_id": row.get('id', ''),
                    "status": "301"
                })
    
    return redirects

def generate_catalog_redirects():
    """Редиректы для каталога (если меняются URLs)"""
    # Пока URLs каталога остаются на Bitrix — редиректы не нужны
    # Если будет миграция каталога — добавить логику
    return []

def generate_nginx_config(redirects):
    """Генерация nginx map + server блок"""
    lines = [
        "# ЦИФРА18 — Redirects Bitrix → WP",
        f"# Generated: {datetime.now().isoformat()}",
        f"# Total redirects: {len(redirects)}",
        "",
        "map $request_uri $redirect_target {",
        "    default \"\";",
    ]
    
    for r in redirects:
        source = r['source'].replace('$', '\\$')
        dest = r['destination']
        lines.append(f'    "{source}" "{dest}";')
    
    lines.extend([
        "}",
        "",
        "# In server block:",
        "# if ($redirect_target) {",
        "#     return 301 $redirect_target;",
        "# }"
    ])
    
    return '\n'.join(lines)

def generate_apache_htaccess(redirects):
    """Генерация .htaccess для Apache"""
    lines = [
        "# ЦИФРА18 — Redirects Bitrix → WP",
        f"# Generated: {datetime.now().isoformat()}",
        f"# Total redirects: {len(redirects)}",
        "",
        "RewriteEngine On",
    ]
    
    for r in redirects:
        source = r['source'].lstrip('/')
        dest = r['destination']
        lines.append(f'RewriteRule ^{source}$ {dest} [R=301,L]')
    
    return '\n'.join(lines)

def generate_verification_csv(redirects):
    """CSV для проверки редиректов (curl -I)"""
    output_file = OUTPUT_DIR / f"redirects_verification_{datetime.now().strftime('%Y-%m-%d')}.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['source_url', 'expected_destination', 'status_code', 'final_url', 'redirect_chain', 'tested_at'])
        for r in redirects:
            source_full = f"https://{BITRIX_DOMAIN}{r['source']}"
            writer.writerow([source_full, r['destination'], '', '', '', ''])
    
    return output_file

def main():
    print("=== Redirect Map Generator ===")
    
    all_redirects = []
    all_redirects.extend(generate_article_redirects())
    all_redirects.extend(generate_catalog_redirects())
    
    if not all_redirects:
        print("No redirects generated. Check export files.")
        return
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # JSON для программного использования
    json_file = OUTPUT_DIR / f"redirects_map_{date_str}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "bitrix_domain": BITRIX_DOMAIN,
            "wp_subdomain": WP_SUBDOMAIN,
            "total": len(all_redirects),
            "redirects": all_redirects
        }, f, ensure_ascii=False, indent=2)
    
    # Nginx config
    nginx_file = OUTPUT_DIR / f"redirects_nginx_{date_str}.conf"
    with open(nginx_file, 'w', encoding='utf-8') as f:
        f.write(generate_nginx_config(all_redirects))
    
    # Apache .htaccess
    htaccess_file = OUTPUT_DIR / f"redirects_htaccess_{date_str}.txt"
    with open(htaccess_file, 'w', encoding='utf-8') as f:
        f.write(generate_apache_htaccess(all_redirects))
    
    # Verification CSV
    csv_file = generate_verification_csv(all_redirects)
    
    print(f"Generated {len(all_redirects)} redirects")
    print(f"JSON: {json_file}")
    print(f"Nginx: {nginx_file}")
    print(f"Apache: {htaccess_file}")
    print(f"Verification CSV: {csv_file}")
    
    # Примеры
    print("\nFirst 5 redirects:")
    for r in all_redirects[:5]:
        print(f"  {r['source']} -> {r['destination']}")

if __name__ == "__main__":
    main()