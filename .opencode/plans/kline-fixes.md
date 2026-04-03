# KlineChart.vue 修复计划

## 问题清单

### 1. intervalLabelMap 缺少 '30m' 键
**位置**: `frontend/src/views/KlineChart.vue:192-196`
**问题**: 周期选择器中有 '30m' 按钮，但 `intervalLabelMap` 没有对应映射，导致显示为原始值 `'30m'` 而非 `'30分钟'`

**修复**:
```typescript
// Before (line 192-196)
const intervalLabelMap: Record<string, string> = {
  '1m': '1分钟', '5m': '5分钟', '15m': '15分钟',
  '1h': '1小时', '4h': '4小时', 
  '1d': '日线', '1w': '周线', '1M': '月线'
}

// After
const intervalLabelMap: Record<string, string> = {
  '1m': '1分钟', '5m': '5分钟', '15m': '15分钟', '30m': '30分钟',
  '1h': '1小时', '4h': '4小时', 
  '1d': '日线', '1w': '周线', '1M': '月线'
}
```

---

### 2. realtimeObj hoverIndex 越界空指针
**位置**: `frontend/src/views/KlineChart.vue:215-251`
**问题**: 当 `hoverIndex` 被设置为超出 `klineData` 范围的索引时（如切换周期后旧索引残留），`klineData.value[currentIndex]` 返回 `undefined`，后续访问 `data.open_time` 抛出 `TypeError: Cannot read properties of undefined`

**修复**:
```typescript
// Before (line 219-220)
const currentIndex = hoverIndex.value !== null ? hoverIndex.value : (klineData.value.length - 1);
const data = klineData.value[currentIndex]; 

// After
const currentIndex = hoverIndex.value !== null ? hoverIndex.value : (klineData.value.length - 1);
if (currentIndex < 0 || currentIndex >= klineData.value.length) return null;
const data = klineData.value[currentIndex];
```

---

### 3. WebSocket 缺少 onerror/onclose 错误处理
**位置**: `frontend/src/views/KlineChart.vue:527-571`
**问题**: `connectWebSocket` 函数只设置了 `onmessage`，没有 `onerror` 和 `onclose` 处理。当 WS 连接失败时：
- 用户看不到任何错误提示
- 控制台可能有静默错误
- 重连机制缺失

**修复**:
```typescript
// After connectWebSocket 函数 (around line 527-571)
const connectWebSocket = (symbol: string) => {
  if (klineWs) klineWs.close();
  
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  const wsUrl = `${protocol}//${host}/api/klines/ws/${symbol}`;
  klineWs = new WebSocket(wsUrl);

  klineWs.onopen = () => {
    console.log(`WebSocket 已连接: ${symbol}`);
  };

  klineWs.onmessage = (event) => {
    try {
      if (!event.data || event.data === 'undefined') return;
      const newKline = JSON.parse(event.data);
      if (!newKline || typeof newKline.close === 'undefined') return;
      if (klineData.value.length === 0) return;
      
      const lastIndex = klineData.value.length - 1;
      const lastKline = klineData.value[lastIndex];
      const currentPrice = parseFloat(newKline.close);

      const newData = [...klineData.value];

      newData[lastIndex] = { 
        ...lastKline, 
        close: currentPrice,
        high: Math.max(lastKline.high, currentPrice),
        low: Math.min(lastKline.low, currentPrice)
      };

      if (selectedInterval.value === '1m' && newKline.open_time > lastKline.open_time) {
        newData.push(newKline);
        if (newData.length > selectedLimit.value) newData.shift();
      }

      klineData.value = newData;
    } catch (error) {
      // 拦截非标准 JSON，防止前端线程崩溃
    }
  };

  klineWs.onerror = (error) => {
    console.error('WebSocket 连接错误:', error);
  };

  klineWs.onclose = (event) => {
    console.log(`WebSocket 已断开: ${symbol}, code: ${event.code}, reason: ${event.reason}`);
    klineWs = null;
  };
};
```

---

### 4. Tooltip 除零风险
**位置**: `frontend/src/views/KlineChart.vue:327-328`
**问题**: 当 `data.open` 为 0 时，涨跌幅计算 `((data.close - data.open) / data.open) * 100` 产生 `Infinity`，振幅计算同理

**修复**:
```typescript
// Before (line 327-328)
const change = (((data.close - data.open) / data.open) * 100).toFixed(2)
const amplitude = (((data.high - data.low) / data.open) * 100).toFixed(2)

// After
const change = data.open ? (((data.close - data.open) / data.open) * 100).toFixed(2) : '0.00'
const amplitude = data.open ? (((data.high - data.low) / data.open) * 100).toFixed(2) : '0.00'
```

---

## 执行方式

由于当前权限限制，请手动应用以上 4 处修改到 `frontend/src/views/KlineChart.vue`，或授予编辑权限后自动执行。
