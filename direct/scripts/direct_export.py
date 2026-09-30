#!/usr/bin/env python3
"""Выгрузка данных Директа.

Кладёт рядом с выгрузками Метрики и Вебмастера, в ту же папку по дате,
чтобы три источника читались как один срез.

  data/exports/direct/<дата>/
      _index.json          что удалось, что нет, сколько баллов съедено
      campaigns.json       кампании с типами, статусами и стратегиями
      adgroups.json        группы объявлений
      keywords.json        ключевые фразы, до 2000 за вызов
      report_account.tsv   сводка по аккаунту
      report_campaign.tsv  сводка по кампаниям
      report_query.tsv     поисковые запросы, офлайн-очередь
      report_criteria.tsv  условия показа, то есть сами фразы

Зачем отчёт по запросам отдельным файлом и почему он идёт последним.
SEARCH_QUERY_PERFORMANCE_REPORT формируется только в офлайн-режиме,
это занимает минуты и ждёт своей очереди. Если поставить его первым,
каждая выгрузка встаёт на минуты даже когда нужен только список
кампаний. Поэтому сначала дешёвое и мгновенное, потом отчёт.

Порядок вызовов и цена. Clients.get стоит 10 баллов и не отдаёт
статистики, но по нему видно, чей это аккаунт, и это стоит проверить
до того, как что-то качать. Keywords.get стоит 15 баллов за вызов плюс
3 за каждую тысячу фраз, а с полями Productivity и StatisticsSearch
дороже втрое, поэтому они не запрашиваются: сейчас важна текстовая
выгрузка, а не продуктивность.

Запуск из корня проекта:
  python direct/scripts/direct_export.py             выгрузить всё
  python direct/scripts/direct_export.py --check     только проверить доступ
  python direct/scripts/direct_export.py --sandbox   в песочнице
"""
import json
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

import direct_api as D  # noqa: E402

ROOT = D.ROOT
EXPORT = os.path.join(ROOT, "data", "exports", "direct")

# Окно отчётов. Двенадцать месяцев назад от сегодняшнего числа, чтобы
# граница не съезжала от запуска к запуску. Query в Директе доступен
# только за 180 дней, поэтому годовой отчёт по запросам всё равно не
# получится, и об этом честно сказано в API_DIGEST.md.
TODAY = date.today()
DATE_TO = (TODAY - timedelta(days=1)).isoformat()
DATE_FROM = (TODAY - timedelta(days=365)).isoformat()

VAT = "NO"


def log(*a):
    print(*a, flush=True)


def out_dir(day=None):
    d = os.path.join(EXPORT, day or TODAY.isoformat())
    os.makedirs(d, exist_ok=True)
    return d


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    return path


def save_tsv(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def report_def(name, rtype, fields, date_from=None, date_to=None, limit=1_000_000):
    crit = {"DateFrom": date_from or DATE_FROM, "DateTo": date_to or DATE_TO}
    return {
        "params": {
            "SelectionCriteria": crit,
            "FieldNames": fields,
            "ReportName": name,
            "ReportType": rtype,
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": VAT,
            "Page": {"Limit": limit},
        }
    }


def check_access(c):
    """Проверяет доступ до того, как создана папка и что-то записано.

    Тот же приём, что в выгрузках Метрики и Вебмастера: код 58 и 34
    означают, что доступа нет, и запись в этом случае только вредна.
    """
    try:
        r = c.call("Clients", "get")
    except D.DirectError as e:
        log()
        log("ОТКАЗ: доступа к API Директа нет. Код %s." % e.code)
        log("  %s" % e.message)
        if e.hint:
            log("  %s" % e.hint)
        log("Ничего не записано, предыдущие выгрузки не тронуты.")
        log()
        if str(e.code) == "58":
            log("Что сделать: заявка на доступ подаётся отдельно от прав")
            log("в приложении, на direct.yandex.ru, вкладка «Мои заявки»,")
            log("https://direct.yandex.ru/registered/main.pl?cmd=apiCertificationRequestList")
            log("Рассматривается от часа до трёх суток, до семи в пик.")
            log("Пользователь должен принять условия на")
            log("https://direct.yandex.ru/registered/main.pl?cmd=apiSettings&api_welcome=yes")
        return None
    return r


def main():
    args = sys.argv[1:]
    sandbox = "--sandbox" in args
    c = D.DirectClient(sandbox=sandbox, log=log)
    log("адрес: %s%s" % (c.base, " (песочница)" if sandbox else ""))

    who = check_access(c)
    if who is None:
        return 3
    log("аккаунт Директа: %s" % who.get("login"))
    log("баллов осталось: %s из %s" % (c.remaining, c.daily))
    if args and "--check" in args:
        return 0

    d = out_dir()
    index = {
        "date_from": DATE_FROM, "date_to": DATE_TO,
        "login": who.get("login"),
        "sandbox": sandbox,
        "units_spent": c.spent,
        "units_remaining": c.remaining,
        "units_daily": c.daily,
        "ok": [], "failed": [],
    }

    def step(label, fn, fname, kind="json"):
        before = c.remaining
        try:
            payload = fn()
        except D.DirectError as e:
            log("  %-18s ОТКАЗ код %s: %s" % (label, e.code, e.message[:70]))
            index["failed"].append({"step": label, "code": e.code,
                                    "message": e.message[:200]})
            return None
        if kind == "json":
            save_json(os.path.join(d, fname), payload)
        else:
            save_tsv(os.path.join(d, fname), payload)
        used = (before - c.remaining) if (before is not None and c.remaining is not None) else "?"
        log("  %-18s ок, баллов потрачено %s" % (label, used))
        index["ok"].append(label)
        return payload

    log("\n1. кампании")
    step("Campaigns.get", lambda: c.call("Campaigns", "get", {
        "fields": ["Id", "Name", "Type", "Status", "State", "DailyBudget",
                   "StartDate", "EndDate", "StrategyId", "ClientLogin",
                   "CounterIds"]}), "campaigns.json")

    log("2. группы объявлений")
    step("AdGroups.get", lambda: c.get_paged("AdGroups", "get", {
        "fields": ["Id", "Name", "CampaignId", "Status", "State",
                   "Type", "Cpc", "MaxCpc"]}), "adgroups.json")

    log("3. ключевые фразы")
    step("Keywords.get", lambda: c.get_paged("Keywords", "get", {
        "fields": ["Id", "Phrase", "AdGroupId", "CampaignId", "State",
                   "Status", "MatchType", "NormPhrase"]}), "keywords.json")

    log("4. сводка по аккаунту")
    step("report_account", lambda: c.report(report_def(
        "cifra-account", "ACCOUNT_PERFORMANCE_REPORT",
        ["Date", "Clicks", "Cost", "Impressions", "Ctr", "AvgCpc",
         "AvgClickPosition", "Sessions", "Conversions", "CostPerConversion",
         "GoalsRoi"])), "report_account.tsv", kind="tsv")

    log("5. сводка по кампаниям")
    step("report_campaign", lambda: c.report(report_def(
        "cifra-campaign", "CAMPAIGN_PERFORMANCE_REPORT",
        ["CampaignId", "CampaignName", "CampaignType", "Date", "Clicks",
         "Cost", "Impressions", "Ctr", "AvgCpc", "AvgClickPosition",
         "AvgEffectiveBid", "Sessions", "Conversions", "CostPerConversion",
         "GoalsRoi"])), "report_campaign.tsv", kind="tsv")

    log("6. условия показа, то есть фразы и автотаргетинги")
    step("report_criteria", lambda: c.report(report_def(
        "cifra-criteria", "CRITERIA_PERFORMANCE_REPORT",
        ["Date", "AdGroupId", "CampaignId", "Criteria", "CriteriaId",
         "CriteriaType", "Clicks", "Cost", "Impressions", "Ctr", "AvgCpc",
         "AvgClickPosition", "AvgTrafficVolume"])), "report_criteria.tsv", kind="tsv")

    log("7. поисковые запросы, только офлайн, это медленно")
    step("report_query", lambda: c.report(report_def(
        "cifra-query", "SEARCH_QUERY_PERFORMANCE_REPORT",
        ["Date", "AdGroupId", "CampaignId", "Query", "MatchedKeyword",
         "MatchType", "Clicks", "Cost", "Impressions", "Ctr", "AvgCpc",
         "AvgClickPosition", "AvgTrafficVolume"],
        date_from=(TODAY - timedelta(days=179)).isoformat(),
        date_to=DATE_TO)), "report_query.tsv", kind="tsv")

    index["units_spent"] = c.spent
    index["units_remaining"] = c.remaining
    save_json(os.path.join(d, "_index.json"), index)

    log("\nготово: %d шагов, %d отказов, баллов потрачено %s, осталось %s"
        % (len(index["ok"]), len(index["failed"]), c.spent, c.remaining))
    log("папка: %s" % os.path.relpath(d, ROOT))
    if index["failed"]:
        log("отказы: %s" % ", ".join(x["step"] for x in index["failed"]))
        return 5
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except D.DirectError as e:
        log("ошибка: %s" % e)
        sys.exit(1)
