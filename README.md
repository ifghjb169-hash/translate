# AI 翻译助手

一个基于 Python 标准库 `tkinter` 的桌面翻译软件原型。

## 运行

```powershell
py -3 translator_app.py
```

首次运行会在同目录生成 `translator_config.json`，用于保存语言、模型、API KEY、置顶和回翻译设置。

## 发布与验证

当前发布版本：`v1.0.4`

- 组织仓库 Release：https://github.com/secure-artifacts/translate/releases/tag/v1.0.4
- 个人仓库 Release：https://github.com/ifghjb169-hash/translate/releases/tag/v1.0.4
- 构建产物：`AI-Translate-Assistant-v1.0.4-win-x64.zip`
- 可执行文件：解压后运行 `AI-Translate-Assistant.exe`
- 构建方式：GitHub Actions tag push 触发
- 构建证明：Release 产物由 GitHub Actions 上传，并通过 GitHub Attestation API 验证
- 组织仓库 SHA256：`96f4508326517c684d05c98f6367efd648afcf5ad612713f97616cab11f9e728`
- 个人仓库 SHA256：`1caa1e37ea024c3e3ea3d2733d60a8a5169e8ad618ebf73da865bd7668faf7a2`

验证方式：

```powershell
# 下载 Release 产物后计算 SHA256
Get-FileHash -Algorithm SHA256 .\AI-Translate-Assistant-v1.0.4-win-x64.zip
```

也可以使用 GitHub CLI 验证软件来源：

```bash
gh attestation verify ./AI-Translate-Assistant-v1.0.4-win-x64.zip --repo secure-artifacts/translate
gh attestation verify ./AI-Translate-Assistant-v1.0.4-win-x64.zip --repo ifghjb169-hash/translate
```

## 已实现功能

- 翻译页分为输入框、译文框和回翻译小框，启动时输入框和译文框等高，三块高度可以拖动分隔条自由调整。
- 上下两个翻译框各显示三种可切换语言，并带更多语言下拉选择。
- “交换语言”按钮位于输入框右上角，会对调上下语言；如果已有译文，也会把译文放回输入框方便继续翻译。
- 顶部使用等尺寸导航按钮：翻译、设置、文字大小。
- 设置页支持窗口永远置顶。
- 支持选择 `AI 翻译` 或 `Google 翻译`；Google 模式只使用 Google 翻译。
- AI 模式支持 Gemini 和 Groq AI；选择 Gemini 时只显示并使用 Gemini API KEY，选择 Groq 时只显示并使用 Groq API KEY。
- API KEY 可一行填写一个，并在当前密钥失败时自动尝试下一行。
- 设置页填写的 AI 平台、API KEY、模型、国家特色和性别会保存到本地配置，下次打开不用重新填写。
- 设置页新增软件界面显示语言下拉菜单，支持中文简体、中文繁体、英语、日语、韩语、法语、德语、西班牙语、俄语，保存后下次启动完整生效。
- “文字大小”页可分别设置输入框、译文框、回翻译框文字大小。
- 软件系统界面文字会随窗口缩放自动调整。
- 支持选择我的语言和对方语言，每组最多三种，已选语言会显示蓝色对勾。
- 语言列表包含尼泊尔语和缅甸语。
- 支持国家特色、我的性别、Gemini/Groq 模型选择。
- 支持开启或关闭回翻译。
- 输入框按第一次 `Enter` 开始翻译；译文完成后，第二次 `Enter` 会把译文输入到最近一次获得焦点的外部窗口输入框里。
- 使用外部输入时，先点一下 FB、Teams、记事本等软件里的聊天框/输入框，再回到翻译软件输入并翻译；软件会记住那个外部窗口。
- 按 `Shift+Enter` 可在输入框内换行。
- 窗口可自由调整大小，最小尺寸已放宽到更窄的 `420x320`。

## 模型列表

Gemini 默认列表：

- `gemini-2.0-flash`
- `gemini-2.5-flash`
- `gemini-3-flash-preview`
- `gemini-3-pro-preview`
- `gemini-3.1-flash-lite-preview`

Groq 默认列表：

- `llama-3.1-8b-instant`
- `llama-3.3-70b-versatile`
- `openai/gpt-oss-120b`
- `openai/gpt-oss-20b`

## 注意

API KEY 当前以明文保存在本地 `translator_config.json`。如果之后要正式发布，建议改成 Windows 凭据管理器或加密存储。
