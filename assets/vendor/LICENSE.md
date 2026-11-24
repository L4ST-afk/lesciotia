# 随包第三方库（vendor）

只一件，2026-11-23 从 jsDelivr 取回的官方发行版，只改文件名，内容未改。

| 文件 | 库 | 版本 | 许可 | 许可证 |
|---|---|---|---|---|
| `chart.umd.min.js` | [Chart.js](https://github.com/chartjs/Chart.js) | 4.4.3 | MIT | https://github.com/chartjs/Chart.js/blob/master/LICENSE.md |

为什么随包：`layouts/charts` 一族此前从 CDN 取库，离线（本库主张离线可跑）打开就是空白；取回后离线可渲染。
⛔ 升级时按上表重取并更新版本号，别手工改压缩件。

**没有收的**：highlight.js。原 `layouts/code` 只引了 core 与语言包、没引主题样式，跑起来一个颜色都不出；
要么连主题一起收（多一份第三方），要么不收——选了不收，`code` 一族按纯文本呈现。
