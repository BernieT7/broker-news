# 券商策略新聞機器人

這是一個給券商策略規劃或商業分析使用的新聞摘要 MVP。流程是：

1. 從監理機關、交易所、Google News、海外金融監理與券商相關 RSS 抓新聞。
2. 用規則先排除股價、目標價、EPS、單一個股、單一商品與重複新聞。
3. 保留和券商業務、法規、海外商業模式、市場結構、同業策略布局相關的候選新聞。
4. 用規則做內部重要度排序，但不在 email 裡顯示分數。
5. 只寄出前 10 則最重要的新聞。
6. 透過 GitHub Actions 每天台北時間早上 7:00 自動執行，抓取前 24 小時新聞。

## 本機試跑

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

把 `.env` 裡的 SMTP 與收件人填好後執行：

```bash
PYTHONPATH=src python -m newsbot.main
```

## GitHub Actions 設定

把下列資料加到 GitHub repo 的 `Settings > Secrets and variables > Actions > Secrets`：

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_TO`

`EMAIL_TO` 用逗號分隔，例如：

```text
alice@example.com,bob@example.com
```

目前排程是每天台北時間 07:00，`DIGEST_LOOKBACK_HOURS` 預設為 24，`DIGEST_MAX_ARTICLES` 預設為 10。如果只想每週一早上 7:00，將 `.github/workflows/news-digest.yml` 裡的 cron 改成：

```yaml
- cron: "0 23 * * 0"
```

## 建議下一步

- 目前已加入工商時報、經濟日報、MoneyDJ、鉅亨、日經、韓國金融監理院、日本金融廳、香港證監會、證交所、金管會、Reuters、Yahoo Finance、Bloomberg、CMoney、moomoo 等來源。商業媒體多半透過 Google News 的 `site:` 限定抓標題與連結，官方機關與交易所則優先使用官方 RSS。
- 把法規公告和一般新聞分成兩條 pipeline，避免重要法規被一般新聞淹沒。
- 將每天的候選新聞存進 Google Sheet、Notion 或資料庫，方便回顧規則有沒有漏選。
- 如果未來候選新聞又變多，再把 AI 摘要或排序加回第二層即可。
- 寄信前加入人工確認模式，等穩定後再全自動寄出。
