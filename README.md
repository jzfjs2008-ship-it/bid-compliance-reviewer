# 招投标合规审查系统

基于 Python + CustomTkinter 的桌面端招投标文件合规审查工具，支持 PDF/DOCX/XLSX 文档的自动解析与交叉比对。

## 功能

- **拖拽导入** — 支持拖拽或点击浏览选择招标文件、商务标、技术标、价格标
- **自动解析** — 智能识别 PDF/DOCX/XLSX 文档内容，按字段规则提取关键信息
- **交叉比对** — 内置比对引擎，支持数值比较、文本包含、正则匹配等多种算子
- **风险分级** — 结果按 致命/高危/人工复核/合规 四级展示，彩色标签一目了然
- **报告导出** — 一键生成 A4 PDF 审查报告，含明细与汇总

## 技术栈

| 组件 | 技术 |
|------|------|
| GUI | CustomTkinter + tkinterdnd2 |
| 解析引擎 | PyMuPDF, python-docx, openpyxl |
| 比对引擎 | 自研规则引擎（8 种算子） |
| 数据存储 | SQLite |
| 报告生成 | ReportLab |

## 快速开始

```bash
pip install -r requirements.txt
python main.py
```

## 项目结构

```
├── main.py              # 入口
├── config/              # 配置
├── database/            # 数据库层（schema + 种子数据）
├── engine/              # 核心引擎（解析/提取/归一化/比对）
├── report/              # PDF 报告导出
├── ui/                  # 桌面 UI
│   ├── app.py           # 主窗口
│   ├── theme.py         # 主题常量
│   └── components/      # 组件库
└── utils/               # 工具类
```

## 许可

MIT License
