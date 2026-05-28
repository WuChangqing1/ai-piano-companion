# CosyVoice For Windows 使用手册

> 最后更新：2026-05-29

## 一、启动服务

```bash
# 在 cosyvoice conda 环境下
conda activate cosyvoice
python api.py
```

服务启动后访问地址：**`http://127.0.0.1:9880`**

## 二、可用模型

| 模型目录 | 用途 | 说明 |
|---|---|---|
| `CosyVoice-300M` | 零样本复刻 / 跨语种合成 | 提供参考音频即可克隆任意音色 |
| `CosyVoice-300M-SFT` | 预训练音色（默认） | 内置 7 种预训练音色，即选即用 |
| `CosyVoice-300M-Instruct` | 自然语言控制 | 用文字描述想要的语气/情感/风格 |

**当前 `api.py` 使用的是 `CosyVoice-300M-SFT` 模型。**

## 三、音色列表

### 默认预训练音色（7个）

| 音色名 | 语言 | 调用示例 |
|---|---|---|
| `中文女` | 中文 | `speaker=中文女` |
| `中文男` | 中文 | `speaker=中文男` |
| `日语男` | 日语 | `speaker=日语男` |
| `粤语女` | 粤语 | `speaker=粤语女` |
| `英文女` | 英文 | `speaker=英文女` |
| `英文男` | 英文 | `speaker=英文男` |
| `韩语女` | 韩语 | `speaker=韩语女` |

### 自定义复刻音色（12个）

这些是预先用零样本复刻保存的自定义音色，存在 `voices/` 目录下：

| 音色名 | 说明 |
|---|---|
| `Keira` | Keira 角色 |
| `gakki(日文)` | 日文 gakki |
| `jok老师` | jok 老师 |
| `叶内法` | 叶内法角色 |
| `叶奈法` | 叶奈法角色 |
| `团长_悲伤` | 团长（悲伤语气） |
| `团长_愤怒` | 团长（愤怒语气） |
| `步非烟` | 步非烟角色 |
| `英文男(低沉)` | 低沉英文男声 |
| `阿星(粤语)` | 阿星粤语版 |
| `阿星` | 阿星普通话 |
| `阿珊(粤语)` | 阿珊粤语 |

> 访问 `http://127.0.0.1:9880/speakers` 可获取完整音色列表。

## 四、API 接口

### 1. GET `/` — TTS 文字转语音（最常用）

直接在浏览器地址栏或 curl 使用：

```
http://127.0.0.1:9880/?text=你好世界&speaker=中文女
```

**参数：**

| 参数 | 必填 | 说明 | 示例 |
|---|---|---|---|
| `text` | 是 | 要合成的文字 | `text=你好世界` |
| `speaker` | 是 | 音色名称 | `speaker=中文女` |
| `speed` | 否 | 语速，默认 1.0 | `speed=1.5`（快1.5倍）|
| `streaming` | 否 | 是否流式，0=否 1=是，默认 0 | `streaming=1` |
| `new` | 否 | 是否用自定义音色，0=否 | `new=0` |

**curl 示例：**

```bash
# 基础调用
curl -o output.wav "http://127.0.0.1:9880/?text=测试测试&speaker=中文女"

# 英文调用
curl -o en.wav "http://127.0.0.1:9880/?text=Hello+world&speaker=英文女"

# 调节语速
curl -o fast.wav "http://127.0.0.1:9880/?text=快快快&speaker=中文男&speed=1.5"

# 流式输出
curl -o stream.ogg "http://127.0.0.1:9880/?text=流式合成&speaker=中文女&streaming=1"

# 使用自定义音色
curl -o custom.wav "http://127.0.0.1:9880/?text=自定义音色测试&speaker=Keira"
```

### 2. POST `/` — TTS（JSON 格式）

```bash
curl -X POST http://127.0.0.1:9880/ \
  -H "Content-Type: application/json" \
  -d '{"text":"你好世界","speaker":"中文女"}' \
  -o output.wav
```

**JSON 参数：**

```json
{
  "text": "要合成的文字",
  "speaker": "音色名",
  "streaming": 0,
  "speed": 1.0
}
```

### 3. POST `/tts_to_audio/` — 固定音色 TTS

使用 `speaker_config.py` 中配置的音色和语速，适合固定的自动化场景。

```bash
curl -X POST http://127.0.0.1:9880/tts_to_audio/ \
  -H "Content-Type: application/json" \
  -d '{"text":"你好世界"}' \
  -o output.wav
```

编辑 `speaker_config.py` 修改默认音色和语速：

```python
speaker = "中文女"   # 修改默认音色
speed = 1.0         # 修改默认语速
```

### 4. GET `/speakers` — 获取音色列表

```bash
curl http://127.0.0.1:9880/speakers
```

返回 JSON 数组，每项包含 `name` 和 `voice_id`。

### 5. GET `/speakers_list` — 简化音色列表

```bash
curl http://127.0.0.1:9880/speakers_list
```

### 6. GET `/save_voice` — 保存自定义音色（零样本复刻）

用一段参考音频克隆音色并保存：

```
http://127.0.0.1:9880/save_voice?text=参考文本&audio=音频URL&voice_name=新音色名
```

| 参数 | 说明 |
|---|---|
| `text` | 参考音频对应的文本 |
| `audio` | 参考音频的 URL（mp3 格式） |
| `voice_name` | 保存的音色名称 |

### 7. GET `/file/<filename>` — 下载生成的文件

```
http://127.0.0.1:9880/file/output.wav    # 下载合成的音频
http://127.0.0.1:9880/file/output.srt    # 下载字幕文件
```

## 五、WebUI 界面

除了 API 接口，还提供 Gradio WebUI：

```bash
# SFT 预训练音色界面
python webui.py --port 9886 --model_dir ./pretrained_models/CosyVoice-300M-SFT

# 音色转换界面
python vc_webui.py
```

WebUI 支持四种推理模式：
- **预训练音色**：选音色 → 输入文本 → 生成
- **3s极速复刻**：上传参考音频 → 输入对应文本 → 生成
- **跨语种复刻**：上传参考音频 → 输入目标语言文本 → 生成
- **自然语言控制**：选音色 → 输入情感描述 → 生成

## 六、语速调节

语速通过 `speed` 参数控制：

| speed 值 | 效果 |
|---|---|
| 0.5 | 慢速，拖长音 |
| 0.8 | 稍慢 |
| 1.0 | 正常语速（默认） |
| 1.2 | 稍快 |
| 1.5 | 快速 |
| 2.0 | 非常快 |

## 七、常见问题

**Q: 中文文本出现乱码？**
URL 中的中文需要做 URL 编码。例如 `中文女` → `%E4%B8%AD%E6%96%87%E5%A5%B3`

**Q: 自定义音色保存在哪？**
音色文件（`.pt`）保存在 `voices/` 目录下，文件名即音色名。

**Q: 如何切换模型？**
修改 `api.py` 第 29 行的模型路径：
```python
cosyvoice = CosyVoice('pretrained_models/CosyVoice-300M-SFT')          # 预训练音色
# cosyvoice = CosyVoice('pretrained_models/CosyVoice-300M')            # 零样本复刻
# cosyvoice = CosyVoice('pretrained_models/CosyVoice-300M-Instruct')   # 自然语言控制
```
