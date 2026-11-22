# 干中学｜可打印桌游与谜题 PDF 出版避坑库

1. **同时给 US Letter 与 A4 两种纸型 + 省墨黑白版（Ink-Saver B&W）**：北美桌面玩家用 `US Letter (8.5×11 in)`，欧洲/英联邦玩家用 `A4 (210×297 mm)`，且家里打印最怕深色底费墨——出书必须标配三版合一 ZIP，评价与转化极高。
2. **`@page { size: ...; margin: 0; }` + 固定高度容器防分页撕裂**：用 Chromium CDP `Page.printToPDF({ preferCSSPageSize: true, printBackground: true })` 导 PDF 时，每张地图固定单页像素/英寸高度与 `break-after: page`，严防 50 张地图跑偏成 53 页错位。
3. **算法 100% 验证可通关 / 唯一解**：单人桌游和逻辑谜题最怕死局图导致差评，生成脚本必须内置 BFS/求解器断言后再排版导出。
4. **Git 仓库只托管 3 页免费试玩样本 PDF 与图文展示页**：全量 50 页付费 PDF 包严格留在 `.gitignore` 忽略范围，仅上传 `itch.io` 付费墙后。
5. **2026-11-22 首书上线实测固化**：
   - itch.io `Short description` 严格限制 `1–120` 字符，超长会导致后台弹出校验遮罩并中断文件上传流程，脚本需硬断言 `len(short_text) <= 120`；
   - itch.io 必须先选 `Paid` 才会展开各文件行的 `input[name$="[demo]"]` 复选框，然后再精准匹配试玩 PDF 行打勾；
   - Chromium CDP `Page.printToPDF` 配合 `@page { margin: 0; }` 与固定尺寸 `.sheet` 能做到 `52 / 52 / 52 / 5` 页 100% 精确无溢页。
6. **2026-11-22 (16:00) 第 2 本《Starship Salvage》实测补充**：
   - itch.io `/game/new` 的 `Classification` 使用 Selectize 控件，需先点 `.classification_picker .selectize-input` 再点 `[data-value='physical_game']`；`Public` 单选框在首次创建保存（Draft）前默认 `disabled`，首次保存跳转到 `/game/edit/<id>` 后方可切换 `Public`；
   - itch.io `/game/edit/<id>` 页面存在上下两个可见 `button.save_btn`，`ego-browser` 需用 `css=button.save_btn >> nth=0` 避免选择器歧义；
   - 首书 `pocket-dungeon-50` 实盘来源数据证实 `tag-no-ai`、`tag-solo-rpg`、`tag-singleplayer` 与 `physical-games/newest` 是核心自然流量入口，新书务必通过 `.tag_input` Selectize 实例挂载对应官方标签；
   - 12×10 宽比例网格在 A4（`210mm` 较 Letter 窄）下将 `.map-canvas-wrap` 限制在 `max-height: 4.95in`，可确保 US Letter 与 A4 均保持精确 42 页不溢出。
