#!/usr/bin/env python3
"""
生成 2026-06-12 每日限免速报 HTML 文件
使用字符串替换正确插入卡片
"""

import urllib.request
import urllib.parse
import json
import time
import re

# ============================================================
# 应用数据
# ============================================================

iap_apps = [
    {"id": 6756003882, "name": "货币转换器・单位换算: Omni", "code": None, "code_type": None},
    {"id": 6775073342, "name": "Inku — 照片日记 & 地图", "code": None, "code_type": None},
    {"id": 1492707861, "name": "NanoRadio", "code": None, "code_type": None},
    {"id": 6770463236, "name": "Diamond Sort : Pixel Coloring", "code": None, "code_type": None},
    {"id": 1581274825, "name": "Mono Browser", "code": None, "code_type": None},
    {"id": 6756500302, "name": "Grocery List - Shared & Easy", "code": "REDDITAPPGIVEAWAY", "code_type": "redeem", "free_duration": "限免内购", "redeem_id": 6756500302},
    {"id": 6749005255, "name": "MiiTrans - AI 翻译助手", "code": None, "code_type": None},
    {"id": 6759787939, "name": "Unhook: App Blocker & Focus", "code": None, "code_type": None},
    {"id": 1673323619, "name": "NeoAria2", "code": None, "code_type": None},
    {"id": 1270620536, "name": "CV Mania: Resume Maker, Editor", "code": None, "code_type": None},
    {"id": 6757937579, "name": "戒习惯天数追踪与打卡记录", "code": "QUITHABITLIFETIME", "code_type": "redeem", "free_duration": "终身免费", "redeem_id": 6757937579},
    {"id": 6767311346, "name": "Home Workout for Women: Fit", "code": "FITWOMENLIFETIME", "code_type": "redeem", "free_duration": "终身免费", "redeem_id": 6767311346},
    {"id": 6760931929, "name": "GLOWD — Golden Ratio & Glow Up", "code": "GLOWVIP", "code_type": "referral"},
]

code_apps = [
    {"id": 6756500302, "name": "Grocery List - Shared & Easy", "code": "REDDITAPPGIVEAWAY", "code_type": "redeem", "free_duration": "限免内购", "redeem_id": 6756500302, "remaining": ""},
    {"id": 6757937579, "name": "戒习惯天数追踪与打卡记录", "code": "QUITHABITLIFETIME", "code_type": "redeem", "free_duration": "终身免费", "redeem_id": 6757937579, "remaining": ""},
    {"id": 6767311346, "name": "Home Workout for Women: Fit", "code": "FITWOMENLIFETIME", "code_type": "redeem", "free_duration": "终身免费", "redeem_id": 6767311346, "remaining": ""},
    {"id": 6760931929, "name": "GLOWD — Golden Ratio & Glow Up", "code": "GLOWVIP", "code_type": "referral", "free_duration": "VIP功能", "remaining": ""},
    {"id": 6473834966, "name": "Monymo: Income Time Tracker", "code": None, "code_type": "promies", "promies_url": "https://www.promies.net/promotion/23f3ae9b-9be4-4f26-96e9-f98a4ee69b2b", "free_duration": "前6个月免费", "remaining": "487/500"},
    {"id": 6756430690, "name": "DreamOn：AI梦境解读", "code": None, "code_type": "promies", "promies_url": "https://www.promies.net/promotion/b710f706-d765-4a3c-b9fe-95d356c150ea", "free_duration": "首月免费", "remaining": "656/665"},
]

free_apps_names = [
    ("转盘做决定", "1元→免费"),
    ("实时天气雷达Pro", "98元→免费"),
    ("度量衡单位换算器", "8元→免费"),
    ("高清计算器", "8元→免费"),
    ("screenTools", "3元→免费"),
    ("AirDisk Pro", "38元→免费"),
    ("DualShot Recorder", "$9.99→免费"),
    ("Cubic Yard Calculator Pro", "$0.99→免费"),
    ("ChordMarker", "$0.99→免费"),
    ("DueView", "$0.99→免费"),
]

deal_apps_names = [
    ("AI趣记账", "168元", "冰点价", "特邀冰点"),
    ("uPaste", "68元", "冰点价", "特邀冰点"),
    ("英语读书", "428元", "冰点价", "特邀冰点"),
    ("水球清单", "63元", "冰点价", "特邀冰点"),
    ("Twos", "88元", "冰点价", "特邀冰点"),
    ("学play专注", "88元", "冰点价", "特邀冰点"),
]

# ============================================================
# iTunes API 查询函数
# ============================================================

def itunes_lookup(ids, country="cn"):
    result = {}
    if not ids: return result
    id_str = ",".join(str(x) for x in ids)
    url = f"https://itunes.apple.com/lookup?id={id_str}&country={country}&entity=software"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for app in data.get("results", []):
            result[app["trackId"]] = app
    except Exception as e:
        print(f"  ✗ lookup 失败 (country={country}): {e}")
    time.sleep(0.3)
    return result

def itunes_search(name, country="cn"):
    query = urllib.parse.quote(name)
    url = f"https://itunes.apple.com/search?term={query}&entity=software&country={country}&limit=5"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("resultCount", 0) > 0:
            for app in data["results"]:
                tname = app.get("trackName", "")
                if name in tname or tname in name:
                    return app.get("trackId"), app
    except Exception:
        pass
    return None, None

print("=" * 60)
print("获取应用数据...")
print("=" * 60)

all_known_ids = list(set([a["id"] for a in iap_apps] + [a["id"] for a in code_apps]))
print(f"\n[1/3] 查询 {len(all_known_ids)} 个内购限免/兑换码应用...")
itunes_cache = itunes_lookup(all_known_ids, "cn")

missing = [i for i in all_known_ids if i not in itunes_cache]
if missing:
    print(f"  国区未找到 {len(missing)} 个，尝试美区...")
    us_data = itunes_lookup(missing, "us")
    itunes_cache.update(us_data)

print(f"\n[2/3] 查询本体限免应用...")
free_apps_data = []
for name, price_info in free_apps_names:
    app_id, data = itunes_search(name, "cn")
    if not data and " " not in name:
        app_id, data = itunes_search(name, "us")
    if data:
        itunes_cache[app_id] = data
        free_apps_data.append({
            "id": app_id, "name": data.get("trackName", name),
            "price_info": price_info,
            "icon": data.get("artworkUrl100", ""),
            "desc": (data.get("description", "")[:120] + "...") if len(data.get("description", "")) > 120 else data.get("description", "")
        })
    else:
        print(f"  ✗ 未找到: {name}")
        free_apps_data.append({"id": None, "name": name, "price_info": price_info, "icon": "", "desc": ""})
    time.sleep(0.2)

print(f"\n[3/3] 查询折扣精选应用...")
deal_apps_data = []
for name, old_price, new_price, discount in deal_apps_names:
    app_id, data = itunes_search(name, "cn")
    if not data:
        app_id, data = itunes_search(name, "us")
    if data:
        itunes_cache[app_id] = data
        deal_apps_data.append({
            "id": app_id, "name": data.get("trackName", name),
            "old_price": old_price, "new_price": new_price, "discount": discount,
            "icon": data.get("artworkUrl100", ""),
            "desc": (data.get("description", "")[:120] + "...") if len(data.get("description", "")) > 120 else data.get("description", "")
        })
    else:
        print(f"  ✗ 未找到: {name}")
        deal_apps_data.append({"id": None, "name": name, "old_price": old_price, "new_price": new_price, "discount": discount, "icon": "", "desc": ""})
    time.sleep(0.2)

print(f"\n缓存中共有 {len(itunes_cache)} 个应用数据")
print("=" * 60)

# ============================================================
# 生成卡片 HTML
# ============================================================

def app_icon(id_, cache):
    if id_ and id_ in cache:
        return cache[id_].get("artworkUrl100", "")
    return ""

def app_desc(id_, cache, name=""):
    if id_ and id_ in cache:
        d = cache[id_].get("description", "")
        genre = cache[id_].get("primaryGenreName", "应用")
        track_name = cache[id_].get("trackName", name)
        if d:
            d_clean = d.replace("\n", " ")[:120]
            # 检查是否包含中文字符
            import re
            if re.search(r'[\u4e00-\u9fff]', d_clean):
                # 有中文，保持原描述
                return d_clean + "..." if len(cache[id_].get("description", "")) > 120 else d_clean
            else:
                # 纯英文描述，用名称+类别生成中文描述
                return f"{track_name} — {genre}类应用"
    return ""

def app_name(id_, fallback, cache):
    if id_ and id_ in cache:
        return cache[id_].get("trackName", fallback)
    return fallback

# 内购限免卡片
iap_cards = []
for app in iap_apps:
    aid = app["id"]
    name = app_name(aid, app["name"], itunes_cache)
    icon = app_icon(aid, itunes_cache)
    desc = app_desc(aid, itunes_cache, app["name"])
    badge = ""
    if app.get("code"):
        if app["code_type"] == "redeem":
            badge = f'<span class="code-badge">兑换码: {app["code"]}</span>'
        elif app["code_type"] == "referral":
            badge = f'<span class="code-badge">推荐码: {app["code"]}</span>'
    name_html = f'{name} {badge}' if badge else name
    store = f'<a href="https://apps.apple.com/app/id{aid}" target="_blank" class="store-link">App Store 下载</a>' if aid else ''
    qr = f'<img src="https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=https://apps.apple.com/app/id{aid}" alt="QR" class="qr" loading="lazy" />' if aid else ''
    iap_cards.append(f'''        <div class="iap-card">
          <img src="{icon}" alt="{name}" class="app-icon" loading="lazy" />
          <div class="app-info">
            <div class="app-name">{name_html}</div>
            <div class="app-desc">{desc}</div>
            {store}
            {qr}
          </div>
        </div>''')
iap_html = "\n".join(iap_cards)

# 兑换码卡片
type_order = {"redeem": 0, "referral": 1, "promies": 2}
code_apps_sorted = sorted(code_apps, key=lambda x: type_order.get(x.get("code_type", ""), 99))

code_cards = []
for app in code_apps_sorted:
    aid = app["id"]
    name = app_name(aid, app["name"], itunes_cache)
    icon = app_icon(aid, itunes_cache)
    desc = app_desc(aid, itunes_cache, app["name"])
    duration_html = f'<div style="font-size:12px;color:#975a16;margin-bottom:6px;">⏱ {app["free_duration"]}</div>' if app.get("free_duration") else ""
    remaining_html = f'<div style="font-size:11px;color:#999;margin-bottom:6px;">剩余名额: {app["remaining"]}</div>' if app.get("remaining") else ""
    if app["code_type"] == "redeem":
        redeem_url = f"https://apps.apple.com/redeem/?ctx=offercodes&id={app['redeem_id']}&code={app['code']}"
        btn = f'<a href="{redeem_url}" target="_blank" class="code-box">一键兑换: {app["code"]}</a>'
    elif app["code_type"] == "referral":
        btn = f'<span class="code-box" style="cursor:default;">应用内输入: {app["code"]}</span>'
    elif app["code_type"] == "promies":
        btn = f'<a href="{app["promies_url"]}" target="_blank" class="code-box">promies.net → 领取页面</a>'
    else:
        btn = ""
    code_cards.append(f'''        <div class="code-card">
          <img src="{icon}" alt="{name}" class="app-icon" loading="lazy" />
          <div class="app-info">
            <div class="app-name">{name}</div>
            {duration_html}
            {remaining_html}
            <div class="app-desc">{desc}</div>
            {btn}
          </div>
        </div>''')
code_html = "\n".join(code_cards)

# 本体限免卡片
free_cards = []
for app in free_apps_data:
    aid = app.get("id")
    name = app["name"]
    icon = app.get("icon", "")
    desc = app.get("desc", "")
    price_info = app.get("price_info", "")
    store = f'<a href="https://apps.apple.com/app/id{aid}" target="_blank" class="store-link">App Store 下载</a>' if aid else ''
    badge = f'<span class="badge-free">{price_info}</span>' if price_info else ''
    name_html = f'{name} {badge}' if badge else name
    free_cards.append(f'''        <div class="free-card">
          <img src="{icon}" alt="{name}" class="app-icon" loading="lazy" />
          <div class="app-info">
            <div class="app-name">{name_html}</div>
            <div class="app-desc">{desc}</div>
            {store}
          </div>
        </div>''')
free_html = "\n".join(free_cards)

# 折扣精选卡片
deal_cards = []
for app in deal_apps_data:
    aid = app.get("id")
    name = app["name"]
    icon = app.get("icon", "")
    desc = app.get("desc", "")
    old_price = app.get("old_price", "")
    new_price = app.get("new_price", "")
    discount = app.get("discount", "")
    store = f'<a href="https://apps.apple.com/app/id{aid}" target="_blank" class="store-link">App Store 下载</a>' if aid else ''
    badge = f'<span class="badge-deal">{old_price}→{new_price} ({discount})</span>' if old_price else ''
    name_html = f'{name} {badge}' if badge else name
    deal_cards.append(f'''        <div class="deal-card">
          <img src="{icon}" alt="{name}" class="app-icon" loading="lazy" />
          <div class="app-info">
            <div class="app-name">{name_html}</div>
            <div class="app-desc">{desc}</div>
            {store}
          </div>
        </div>''')
deal_html = "\n".join(deal_cards)

# ============================================================
# 读取模板并替换
# ============================================================

with open("/Users/qianyuan/WorkBuddy/2026-05-14-task-6/template_daily.html", "r", encoding="utf-8") as f:
    html = f.read()

# 替换日期和统计占位符
html = html.replace("{DATE}", "2026.06.12")
html = html.replace("{DATE_DISPLAY}", "2026.06.12")
html = html.replace("{IAP_COUNT}", str(len(iap_apps)))
html = html.replace("{FREE_COUNT}", str(len([a for a in free_apps_data if a.get("id")])))
html = html.replace("{DEAL_COUNT}", str(len([a for a in deal_apps_data if a.get("id")])))
html = html.replace("{CODE_COUNT}", str(len(code_apps)))

# 方法：先删除所有 HTML 注释块，然后在 section 的 </div> 前插入卡片
# 但这样会删除所有注释，包括有用的注释
# 更好的方法：只删除包含占位符的注释块

# 找到每个 section 中的大注释块并替换
def replace_comment_in_section(html, section_id, cards_html):
    """找到指定 section 中的 <!-- ... --> 注释块（包含占位符的），替换为卡片"""
    # 找到 section 的开始和结束
    section_start = html.find(f'<div class="section" id="{section_id}">')
    if section_start == -1:
        print(f"  ⚠️ 未找到 section {section_id}")
        return html
    
    # 找到 section 的结束（下一个 </div> 在正确的层级）
    # 简单方法：找到 section 后的第一个 \n    </div>\n\n    <!-- 或 \n    </div>\n\n    <div class="footer"> 或 \n    </div>\n\n    <div class="section">
    pos = section_start + len(f'<div class="section" id="{section_id}">')
    
    # 在 section 内部查找 <!--
    comment_start = html.find("<!--", pos)
    if comment_start == -1:
        print(f"  ⚠️ section {section_id} 中未找到注释")
        return html
    
    # 找到对应的 -->
    comment_end = html.find("-->", comment_start)
    if comment_end == -1:
        print(f"  ⚠️ section {section_id} 中注释未闭合")
        return html
    
    # 检查这个注释块是否包含占位符
    comment_content = html[comment_start:comment_end+3]
    if "{APP_NAME}" not in comment_content and "{ICON_URL}" not in comment_content:
        # 可能是其他注释（如 section-header 中的），跳过
        # 查找下一个注释
        comment_start2 = html.find("<!--", comment_end + 3)
        if comment_start2 != -1:
            comment_end2 = html.find("-->", comment_start2)
            if comment_end2 != -1:
                comment_content2 = html[comment_start2:comment_end2+3]
                if "{APP_NAME}" in comment_content2 or "{ICON_URL}" in comment_content2:
                    comment_start = comment_start2
                    comment_end = comment_end2
                    comment_content = comment_content2
    
    # 替换注释块为卡片
    before = html[:comment_start]
    after = html[comment_end+3:]
    
    # 确保后面有空行
    if after.startswith("\n"):
        after = after[1:]
    if after.startswith("\n"):
        after = after[1:]
    
    return before + "\n" + cards_html + "\n    " + after

html = replace_comment_in_section(html, "section-iap", iap_html)
html = replace_comment_in_section(html, "section-code", code_html)
html = replace_comment_in_section(html, "section-free", free_html)
html = replace_comment_in_section(html, "section-deal", deal_html)

# 写文件
output_path = "/Users/qianyuan/WorkBuddy/2026-05-14-task-6/限免速报-2026-06-12.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ HTML 已生成: {output_path}")
print(f"   内购限免: {len(iap_apps)} | 兑换码: {len(code_apps)} | 本体限免: {len([a for a in free_apps_data if a.get('id')])} | 折扣: {len([a for a in deal_apps_data if a.get('id')])}")
print("=" * 60)
