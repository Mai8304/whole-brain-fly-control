# Replay Renderer Worker Design

**Goal:** 把 `replay frame（回放帧）` 渲染从“每帧启动一个 Python 子进程”收敛成“单个常驻渲染器 worker（常驻工作进程）”，消除播放时反复弹出的 `Python.app`，同时保持 `flybody（果蝇身体与 MuJoCo 物理环境）` 渲染真值链不变。

**Current problem:** 当前 `GET /api/console/replay/frame` 每次请求都会通过 `subprocess.run(...)` 启动 `scripts/render_replay_frame.py`。该脚本会重新创建 `ReplayRenderer（回放渲染器）` 与 `flybody` 环境，再渲染单帧 JPEG。共享时间轴播放时，前端会按步请求新帧，因此 macOS 会反复看到新的 `Python.app` 子进程。

**Approved scope:** 只重构回放帧渲染执行模型，不改变前端的 replay 控制协议、不改变 `step_id（步编号）` 同步语义、不引入 mock fallback。

## Architecture

采用双环境、单常驻 worker 方案：

- `console_api（控制台 API）` 仍运行在当前主环境。
- `replay renderer worker（回放渲染工作进程）` 运行在 `.venv-flybody`，启动后只创建一次 `ReplayRenderer`。
- API 进程通过 `stdin/stdout` 与 worker 通信：
  - 请求：一行 JSON，包含 `step / camera / width / height`
  - 响应头：一行 JSON，包含 `ok / content_type / byte_length / error`
  - 响应体：紧随其后的固定长度 JPEG bytes

这样保留了环境隔离，同时把“每帧起新进程”变成“单进程多请求”。

## Data Flow

1. 前端播放推进 `step_id`
2. 浏览器重新请求 `/api/console/replay/frame?...`
3. API 复用一个 `ReplayFrameWorkerClient（回放帧 worker 客户端）`
4. client 向常驻 worker 发送渲染请求
5. worker 在已创建的 `ReplayRenderer` 上执行 `render_frame(...)`
6. worker 把 JPEG bytes 回传给 API
7. API 原样返回 `image/jpeg`

## Lifecycle and Failure Rules

- `create_console_api(...)` 内部懒加载 worker；第一次请求回放帧时才启动。
- worker 只绑定当前 `eval_dir`，不跨不同 replay trace 复用。
- 若 worker 退出、管道损坏或返回协议错误，API 应抛出 `503`，并在下一次请求时允许重新拉起。
- API 关闭时应尝试终止 worker，避免僵尸进程。

## Testing Strategy

- API 测试应锁定：连续两次 `GET /api/console/replay/frame` 只启动一次 worker，并能在同一 worker 上渲染不同 step。
- worker 客户端测试应锁定：协议可以传输 JPEG bytes，worker 异常能转成可读错误。
- 保留现有 replay API 行为测试，确保 `seek / camera / summary / brain-view / timeline` 不回归。

## Non-Goals

- 不把前端从 `<img src=...>` 改成 websocket 或 canvas 流。
- 不把主 API 整体迁移到 `.venv-flybody`。
- 不做离线预渲染全帧缓存。
