# 008. GitHub — tasks

- [x] `.gitignore` (секреты, exports, db, rar, большой PDF) + `.gitattributes`
- [x] `git init`, ветка `main`, первый коммит `88a9de1`
- [x] `README.md`
- [x] `deploy_github_pages.bat`: dirty-guard, вход браузером, rebase, авто-откат при конфликте (ASCII-only)
- [x] Сквозной тест деплоя на локальном bare-репозитории: все ветки, секретов в дереве нет
- [x] `.github/workflows/weekly-refresh.yml`: push / cron / dispatch, без цикла коммитов
- [x] Репозиторий `homgorn/cifra` (private), remote добавлен
- [x] `.wrangler/cache` удалён из репозитория + в `.gitignore`
- [x] Битый PAT удалён из Credential Manager
- [ ] Запустить `deploy_github_pages.bat` (сам открывает браузер для входа)
- [ ] Settings → Pages → Source: GitHub Actions
- [ ] Secrets → `YANDEX_OAUTH_TOKEN` (+ client id/secret), ручной прогон Actions
- [ ] Проверить `https://homgorn.github.io/cifra/` из браузера
