# Подразделы каталога без сущности услуги в графе

Сгенерировано: `landings/_scrape/export_kg_landings.py --apply` (2026-10-04).
Перегенерировать после того, как допишешь описания.

## Что это

Выкачка сайта содержит 88 подразделов. Описание услуги в графе есть для 71 из них, нет для 17.

Из этих 17 на лендингах встречаются 16; оставшийся 1 не попал ни на одну страницу и в списке ниже не нужен.

Из-за этого `entities/landings.ttl` ссылается только на те услуги,
которые в графе есть, и молчит про остальные. Число ссылок в графе
не равно числу подразделов каталога: один подраздел может
покрываться несколькими лендингами, и наоборот.

Цифры считаются при генерации, а не написаны здесь руками:
текст с зашитым «меньше половины» продержался одну правку и стал
враньём, когда сопоставление подразделов починили.

## Чего не хватает

| Подраздел каталога | На каких лендингах |
|---|---|
| `ezhednevniki1738` | merch-s-l-logotipom |
| `kartiny-na-kholste6473` | shirokoformatnaya-i-interyer |
| `konverty-` | upakovka |
| `papki-` | upakovka |
| `pechat-chertezhey-proektnoy-dokumentatsii` | inzhenernaya-pechat |
| `pechat-na-bannere-shirinoy-do-1-6m` | shirokoformatnaya-i-interyer |
| `pechat-na-bannere-shirinoy-do-3-2m` | shirokoformatnaya-i-interyer |
| `pechat-na-posternoy-bumage8706` | shirokoformatnaya-i-interyer |
| `roll-up-0-85kh2-m` | stendy-i-mobilnye-stendy |
| `roll-up-1-2x2-m` | stendy-i-mobilnye-stendy |
| `roll-up-1-5x2-m` | stendy-i-mobilnye-stendy |
| `roll-up2950451249975881` | stendy-i-mobilnye-stendy |
| `suvenirnye-chasy-na-zakaz` | melenie-suvenery |
| `tablichka-dlya-oplaty-s-qr-kodom` | stendy-i-mobilnye-stendy |
| `uf-pechat1` | uf-pechat-i-dop-uslugi |
| `znachki-zakatnye9558` | merch-s-l-logotipom, vizitki-i-identifikaciya |

## Что делать

Дописать сущности в соответствующие файлы:
`entities/suvenirnaya_services.ttl`, `entities/poligrafiya_services.ttl`,
`entities/inzhenernaya_services.ttl`, `entities/stendy_services.ttl`,
`entities/mobilnye_stendy_services.ttl`, `entities/interer_services.ttl`,
`entities/shirokoformatnaya_services.ttl`.

Идентификатор по образцу соседей: `cifra:service_<раздел>_<подраздел>`,
где раздел подписан сокращённо: `suvenirnaya` вместо
`suvenirnaya-produktsiya`. После этого экспорт запускается ещё раз,
и ссылки появляются сами.
