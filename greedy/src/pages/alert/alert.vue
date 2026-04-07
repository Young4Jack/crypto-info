<template>
	<view class="alert-page">
		<view class="alert-container">
			<!-- 页面头部 -->
			<view class="page-header">
				<text class="header-title">预警中心</text>
				<view v-if="isLoggedIn" class="add-btn pc-only" @tap="toggleAddForm">
					<text class="btn-text">{{ editingId ? '编辑预警' : '+ 添加预警' }}</text>
				</view>
			</view>

			<!-- 未登录态：提示 + 登录按钮 -->
			<view v-if="!isLoggedIn" class="guest-state">
				<text class="guest-title">请登录后使用</text>
				<view class="guest-login-btn" @tap="goToLogin">
					<text class="btn-text">立即登录</text>
				</view>
			</view>

			<!-- 已登录态 -->
			<view v-else>
				<!-- 首次加载骨架屏 -->
				<view v-if="loading && alertRules.length === 0" class="skeleton-state">
					<view class="skeleton-card skeleton-wide"></view>
					<view class="skeleton-card skeleton-wide"></view>
					<view class="skeleton-card"></view>
				</view>

				<!-- 已加载完成：显示表单和列表 -->
				<view v-else>
				<!-- 添加/编辑预警表单 -->
				<view v-if="showAddForm" class="add-form-card">
					<view class="form-header">
						<text class="form-title">{{ editingId ? '编辑预警' : '新建预警' }}</text>
						<text class="form-close" @tap="toggleAddForm">×</text>
					</view>

					<!-- 1. 交易对 -->
						<view class="form-group">
						<text class="form-label">交易对</text>
						<input
							class="form-input"
							type="text"
							placeholder="如 btc / BTC / BTCUSDT 均可，自动补全 USDT"
							v-model="form.crypto_symbol"
							@blur="onSymbolBlur"
						/>
					</view>

					<!-- 2. 预警类型（5选1） -->
					<view class="form-group">
						<text class="form-label">预警类型</text>
						<view class="type-group">
							<view
								v-for="t in alertTypeOptions"
								:key="t.value"
								class="radio-btn"
								:class="{ active: form.alert_type === t.value }"
								@tap="onTypeChange(t.value)"
							>
								<text>{{ t.label }}</text>
							</view>
						</view>
					</view>

					<!-- 3. 触发值输入 -->
					<view v-if="isSimpleType" class="form-group">
						<text class="form-label">触发价格 (USD)</text>
						<input
							class="form-input"
							type="digit"
							placeholder="输入触发价格"
							v-model="form.threshold_price"
						/>
					</view>

					<view v-if="!isSimpleType" class="form-group">
						<text class="form-label">基准价格 (USD)</text>
						<view class="base-price-row">
							<input
								class="form-input base-price-input"
								type="digit"
								placeholder="如当前价"
								v-model="form.base_price"
							/>
							<view v-if="basePriceLoading" class="base-price-hint-wrap">
								<text class="base-price-hint">获取中...</text>
							</view>
							<view v-else-if="basePriceAutoFetched" class="base-price-hint-wrap" @tap="onBasePriceFill">
								<text class="base-price-hint">已自动获取: ${{ autoBasePrice }}</text>
							</view>
							<view v-else class="base-price-hint-wrap" @tap="fetchBasePrice">
								<text class="base-price-hint fetch-btn">手动获取</text>
							</view>
						</view>
					</view>

					<view v-if="!isSimpleType" class="form-group">
						<text class="form-label">触发比例 (%)</text>
						<input
							class="form-input"
							type="digit"
							:placeholder="percentPlaceholder"
							v-model="form.threshold_value"
						/>
					</view>

					<!-- 4. 频率控制 -->
					<view class="form-group form-row">
						<text class="form-label">持续预警</text>
						<switch
							:checked="form.is_continuous"
							color="#409EFF"
							@change="onContinuousChange"
						/>
					</view>

					<view class="form-row-group">
						<view class="form-group form-half">
							<text class="form-label">触发间隔(分钟)</text>
							<input
								class="form-input"
								type="number"
								placeholder="最小 5"
								v-model="form.interval_minutes"
							/>
						</view>
						<view class="form-group form-half">
							<text class="form-label">最大通知次数</text>
							<input
								class="form-input"
								type="number"
								placeholder="最小 1"
								v-model="form.max_notifications"
							/>
						</view>
					</view>

					<!-- 5. 通知渠道（下拉选择） -->
					<view class="form-group">
						<text class="form-label">通知渠道</text>
						<picker
							mode="selector"
							:range="channelPickerLabels"
							:value="selectedChannelIndex >= 0 ? selectedChannelIndex : 0"
							@change="onChannelPickerChange"
						>
							<view class="picker-display">
								<text class="picker-text">{{ selectedChannelDisplay }}</text>
								<text class="picker-arrow">▼</text>
							</view>
						</picker>
					</view>

					<!-- 通知频道下拉 -->
					<view v-if="selectedChannelData?.groups?.length" class="form-group">
						<text class="form-label">通知频道</text>
						<picker
							mode="selector"
							:range="selectedChannelData.groups"
							:value="groupPickerIndex"
							@change="onGroupPickerChange"
						>
							<view class="picker-display">
								<text class="picker-text">{{ groupDisplayValue }}</text>
								<text class="picker-arrow">▼</text>
							</view>
						</picker>
					</view>

					<view class="form-submit-btn" @tap="submitAlert">
						<text class="btn-text">{{ submitting ? '提交中...' : (editingId ? '保存修改' : '确认添加') }}</text>
					</view>
				</view>

				<!-- 预警规则列表 -->
				<view v-else class="alert-list">
					<view
						v-for="item in alertRules"
						:key="item.id"
						class="alert-card"
					>
						<view class="rule-info" @tap="openEdit(item)">
							<view class="rule-header">
								<text class="rule-symbol">{{ item.crypto_symbol }}</text>
								<view class="badges">
									<text v-if="item.is_active" class="badge badge-active">监控中</text>
									<text v-if="item.is_continuous" class="badge badge-continuous">持续预警</text>
								</view>
							</view>
							<text class="rule-condition">{{ formatCondition(item) }}</text>
							<text v-if="item.notified_count > 0" class="rule-meta">
								已通知 {{ item.notified_count }} / {{ item.max_notifications }} 次
							</text>
						</view>
						<view class="rule-actions">
							<text class="edit-btn" @tap="openEdit(item)">编辑</text>
							<text class="delete-btn" @tap="confirmDelete(item)">删除</text>
						</view>
					</view>

					<view v-if="!loading && alertRules.length === 0" class="empty-state">
						<text class="empty-text">暂无预警规则</text>
						<text class="empty-hint">点击添加按钮创建你的第一条预警</text>
					</view>
				</view>

				</view>

				<!-- 移动端底部按钮 -->
				<view class="add-btn mobile-only" @tap="onMobileBtnTap">
					<text class="btn-text">{{ showAddForm ? '返回' : '+ 添加预警' }}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { alertsApi, klinesApi, notificationChannelsApi, type AlertItem, type NotificationChannel } from '@/api'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

// 预警类型选项（5种）
const alertTypeOptions = [
	{ value: 'above', label: '涨破' },
	{ value: 'below', label: '跌破' },
	{ value: 'percent_up', label: '涨幅' },
	{ value: 'percent_down', label: '跌幅' },
	{ value: 'amplitude', label: '振幅' },
]

// 登录状态
const isLoggedIn = ref(false)

// 加载状态
const loading = ref(false)
const submitting = ref(false)

const { startAutoRefresh, stopAutoRefresh } = useAutoRefresh()

// 预警列表
const alertRules = ref<AlertItem[]>([])

// 表单显隐
const showAddForm = ref(false)

// 编辑中的预警 ID（null = 新建模式）
const editingId = ref<number | null>(null)

// 通知渠道配置
const channels = ref<NotificationChannel[]>([])
const channelLoading = ref(false)

// 表单数据
const form = ref({
	crypto_symbol: '',
	alert_type: 'above' as string,
	threshold_price: '',
	base_price: '',
	threshold_value: '',
	is_continuous: false,
	interval_minutes: '',
	max_notifications: '',
	notification_channel: '',
	notification_group: '',
})

// 基准价格自动获取相关
const basePriceLoading = ref(false)
const autoBasePrice = ref(0)
const basePriceAutoFetched = ref(false)

// above / below 为简单类型
const isSimpleType = computed(() => {
	return form.value.alert_type === 'above' || form.value.alert_type === 'below'
})

// 百分比 placeholder
const percentPlaceholder = computed(() => {
	switch (form.value.alert_type) {
		case 'percent_up':
		case 'percent_down':
			return '如 5 表示 5%'
		case 'amplitude':
			return '如 3 表示 3%'
		default:
			return ''
	}
})

// 每次页面显示
onShow(async () => {
	const token = uni.getStorageSync('token')
	if (!token) {
		isLoggedIn.value = false
		alertRules.value = []
		return
	}
	isLoggedIn.value = true
	// 并行加载预警列表和通知渠道
	await fetchAlertList()
	if (channels.value.length === 0) {
		fetchChannels()
	}
	// 启动自动刷新
	startAutoRefresh(fetchAlertList)
})

onUnmounted(() => {
	stopAutoRefresh()
})

// 获取通知渠道
const fetchChannels = async () => {
	channelLoading.value = true
	try {
		const res = await notificationChannelsApi.getList()
		channels.value = res.data || []
		if (channels.value.length > 0) {
			const defaultIdx = channels.value.findIndex((c) => c.is_default)
			selectedChannelIndex.value = defaultIdx >= 0 ? defaultIdx : 0
			const ch = channels.value[selectedChannelIndex.value]
			if (ch) {
				form.value.notification_channel = ch.name
				const gi = ch.groups.indexOf(ch.default_group)
				groupPickerIndex.value = gi >= 0 ? gi : 0
				form.value.notification_group = ch.default_group
			}
		}
	} catch (e: any) {
		console.error('获取通知渠道失败', e)
	} finally {
		channelLoading.value = false
	}
}

// 渠道选项（无自定义）
const channelOptions = computed(() => {
	return channels.value.map((c, i) => ({ label: c.name, value: c.name, index: i }))
})

const selectedChannelIndex = ref(-1)

// 获取预警列表
const fetchAlertList = async () => {
	loading.value = true
	try {
		const res = await alertsApi.getList()
		alertRules.value = res.data
	} catch (e: any) {
		console.error('获取预警列表失败', e)
	} finally {
		loading.value = false
	}
}

// 切换表单显隐
const toggleAddForm = () => {
	showAddForm.value = !showAddForm.value
	if (!showAddForm.value) {
		editingId.value = null
		resetForm()
	}
}

// 持续预警开关
const onContinuousChange = (event: any) => {
	form.value.is_continuous = event.detail?.value ?? event.value ?? false
}

// 打开编辑
const openEdit = (item: AlertItem) => {
	editingId.value = item.id
	showAddForm.value = true
	form.value.crypto_symbol = item.crypto_symbol
	form.value.alert_type = item.alert_type
	form.value.threshold_price = item.threshold_price ? String(item.threshold_price) : ''
	form.value.base_price = item.base_price ? String(item.base_price) : ''
	form.value.threshold_value = item.threshold_value ? String(item.threshold_value) : ''
	form.value.is_continuous = item.is_continuous || false
	form.value.interval_minutes = item.interval_minutes ? String(item.interval_minutes) : ''
	form.value.max_notifications = item.max_notifications ? String(item.max_notifications) : ''
	form.value.notification_channel = ''
	form.value.notification_group = ''

	// 匹配渠道名称
	const ci = channels.value.findIndex((c) => c.name === form.value.notification_channel)
	if (ci >= 0) {
		selectedChannelIndex.value = ci
		const gi = channels.value[ci].groups.indexOf(channels.value[ci].default_group)
		groupPickerIndex.value = gi >= 0 ? gi : 0
		form.value.notification_group = channels.value[ci].default_group
	}

	// 滚动到表单顶部
	uni.pageScrollTo({ scrollTop: 0, duration: 200 })
}

// 类型切换
const onTypeChange = (type: string) => {
    form.value.alert_type = type
    form.value.threshold_price = ''
    form.value.base_price = ''
    form.value.threshold_value = ''
    basePriceAutoFetched.value = false
    autoBasePrice.value = 0
    // 如果新类型不是简单类型且交易对已填写，自动触发获取基准价格
    if (type !== 'above' && type !== 'below' && form.value.crypto_symbol.trim()) {
        fetchBasePrice()
    }
}

// 移动端按钮：表单打开时关闭表单
const onMobileBtnTap = () => {
	if (showAddForm.value) {
		editingId.value = null
		showAddForm.value = false
		resetForm()
	} else {
		toggleAddForm()
	}
}

// 交易对自动补全
const normalizeSymbol = (raw: string): string => {
	const s = raw.trim().toUpperCase()
	if (!s) return ''
	if (!s.endsWith('USDT')) return `${s}USDT`
	return s
}

// 输入框失焦时自动补全交易对并获取基准价格
const onSymbolBlur = () => {
	if (form.value.crypto_symbol.trim()) {
		const normalized = normalizeSymbol(form.value.crypto_symbol)
		if (normalized && normalized !== form.value.crypto_symbol) {
			form.value.crypto_symbol = normalized
		}
		// 非简单类型时自动获取基准价格
		if (!isSimpleType.value) {
			fetchBasePrice()
		}
	}
}

// 自动获取的基准价格填入输入框
const onBasePriceFill = () => {
	if (autoBasePrice.value > 0) {
		form.value.base_price = String(autoBasePrice.value)
	}
}

// 从 API 获取基准价格
const fetchBasePrice = async () => {
    // 防重复请求，避免同一时刻的多笔请求
    if (basePriceLoading.value) return
    const symbol = normalizeSymbol(form.value.crypto_symbol)
	if (!symbol) {
		uni.showToast({ title: '请先输入交易对', icon: 'none' })
		return
	}
	basePriceLoading.value = true
	console.log('[fetchBasePrice] 开始请求, symbol:', symbol)
	try {
		const res = await klinesApi.getKlines(symbol, '1m', 1)
		console.log('[fetchBasePrice] 请求返回, res:', JSON.stringify(res))
		const body = res.data as any
		console.log('[fetchBasePrice] body:', JSON.stringify(body))
		const klines = body?.data?.klines || body?.klines || []
		console.log('[fetchBasePrice] klines:', JSON.stringify(klines))
		if (Array.isArray(klines) && klines.length > 0) {
			const close = klines[0].close
			if (close != null) {
				const price = parseFloat(close)
				if (price > 0) {
					autoBasePrice.value = price
					basePriceAutoFetched.value = true
					form.value.base_price = String(price)
					console.log('[fetchBasePrice] 成功, 价格:', price)
				} else {
					uni.showToast({ title: '获取到的价格无效', icon: 'none' })
				}
			}
		} else if (body?.success === false) {
			uni.showToast({ title: body.error || '获取价格失败', icon: 'none' })
		} else {
			uni.showToast({ title: '未获取到价格数据', icon: 'none' })
		}
	} catch (e: any) {
		console.error('[fetchBasePrice] 异常:', e)
		uni.showToast({ title: '获取价格失败: ' + (e?.message || '未知'), icon: 'none' })
	} finally {
		basePriceLoading.value = false
	}
}

// 重置表单
const resetForm = () => {
	form.value = {
		crypto_symbol: '',
		alert_type: 'above',
		threshold_price: '',
		base_price: '',
		threshold_value: '',
		is_continuous: false,
		interval_minutes: '',
		max_notifications: '',
		notification_channel: '',
		notification_group: '',
	}
	selectedChannelIndex.value = -1
	groupPickerIndex.value = 0
	basePriceAutoFetched.value = false
	autoBasePrice.value = 0
	if (channels.value.length > 0) {
		const defaultIdx = channels.value.findIndex((c) => c.is_default)
		selectedChannelIndex.value = defaultIdx >= 0 ? defaultIdx : 0
		const ch = channels.value[selectedChannelIndex.value]
		if (ch) {
			form.value.notification_channel = ch.name
			const gi = ch.groups.indexOf(ch.default_group)
			groupPickerIndex.value = gi >= 0 ? gi : 0
			form.value.notification_group = ch.default_group
		}
	}
}

// 渠道选择器
const channelPickerLabels = computed(() => channelOptions.value.map((o) => o.label))

const selectedChannelData = computed(() => {
	const idx = selectedChannelIndex.value
	if (idx < 0 || idx >= channels.value.length) return null
	return channels.value[idx]
})

const selectedChannelDisplay = computed(() => {
	const idx = selectedChannelIndex.value
	if (idx < 0 || idx >= channels.value.length) return '请选择通知渠道'
	const ch = channels.value[idx]
	return ch ? ch.name : '请选择通知渠道'
})

const groupPickerIndex = ref(0)

const groupDisplayValue = computed(() => {
	const groups = selectedChannelData.value?.groups || []
	if (groups.length === 0) return ''
	return groups[groupPickerIndex.value] || groups[0]
})

const onChannelPickerChange = (e: any) => {
	const idx = parseInt(e.detail.value, 10)
	const opt = channelOptions.value[idx]
	if (opt) {
		selectedChannelIndex.value = idx
		const ch = channels.value[opt.index]
		if (ch) {
			form.value.notification_channel = ch.name
			const gi = ch.groups.indexOf(ch.default_group)
			groupPickerIndex.value = gi >= 0 ? gi : 0
			form.value.notification_group = ch.default_group
		}
	}
}

const onGroupPickerChange = (e: any) => {
	groupPickerIndex.value = parseInt(e.detail.value, 10)
	const groups = selectedChannelData.value?.groups || []
	form.value.notification_group = groups[groupPickerIndex.value] || ''
}

// 提交（新增或编辑）
const submitAlert = async () => {
	const symbol = normalizeSymbol(form.value.crypto_symbol)
	if (!symbol) {
		uni.showToast({ title: '请输入交易对', icon: 'none' })
		return
	}

	let thresholdPrice = 0
	let thresholdValue = 0

	if (isSimpleType.value) {
		thresholdPrice = parseFloat(form.value.threshold_price)
		if (!thresholdPrice || thresholdPrice <= 0) {
			uni.showToast({ title: '请输入有效触发价格', icon: 'none' })
			return
		}
	} else {
		thresholdValue = parseFloat(form.value.threshold_value)
		if (!thresholdValue || thresholdValue <= 0) {
			uni.showToast({ title: '请输入有效触发比例', icon: 'none' })
			return
		}
	}

	submitting.value = true
	const payload: any = {
		crypto_symbol: symbol,
		alert_type: form.value.alert_type,
	}

	if (isSimpleType.value) {
		payload.threshold_price = parseFloat(thresholdPrice.toFixed(4))
	} else {
		payload.threshold_price = 0
		payload.threshold_value = parseFloat(thresholdValue.toFixed(2))
		const baseInput = parseFloat(form.value.base_price)
		if (baseInput && baseInput > 0) {
			payload.base_price = parseFloat(baseInput.toFixed(4))
		}
	}

	if (form.value.is_continuous) {
		payload.is_continuous = true
	}
	payload.interval_minutes = parseInt(form.value.interval_minutes, 10) || 5
	payload.max_notifications = parseInt(form.value.max_notifications, 10) || 1

	if (form.value.notification_channel.trim()) {
		payload.notification_channel = form.value.notification_channel.trim()
	}
	if (form.value.notification_group.trim()) {
		payload.notification_group = form.value.notification_group.trim()
	}

	try {
		if (editingId.value) {
			// 暂时用 PUT 接口，如果后端不支持则删重建
			await alertsApi.update(editingId.value, payload)
			uni.showToast({ title: '预警已更新', icon: 'success' })
		} else {
			await alertsApi.create(payload)
			uni.showToast({ title: '预警添加成功', icon: 'success' })
		}
		showAddForm.value = false
		editingId.value = null
		resetForm()
		await fetchAlertList()
	} catch (e: any) {
		if (e.message && e.message.includes('405')) {
			// PUT 不支持，尝试删重建
			await handleEditFallback(payload)
			return
		}
		uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
	} finally {
		submitting.value = false
	}
}

// 编辑接口不支持时的降级策略
const handleEditFallback = async (payload: any) => {
	try {
		await alertsApi.delete(editingId.value!)
		await alertsApi.create(payload)
		uni.showToast({ title: '预警已更新', icon: 'success' })
		showAddForm.value = false
		editingId.value = null
		resetForm()
		await fetchAlertList()
	} catch (e: any) {
		uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
	}
	submitting.value = false
}

// 确认删除
const confirmDelete = (item: AlertItem) => {
	uni.showModal({
		title: '确认删除',
		content: `确定删除 ${item.crypto_symbol} 的预警规则吗？`,
		success: async (res) => {
			if (res.confirm) {
				await deleteAlert(item.id)
			}
		},
	})
}

const deleteAlert = async (id: number) => {
	try {
		await alertsApi.delete(id)
		uni.showToast({ title: '已删除', icon: 'success' })
		await fetchAlertList()
	} catch (e: any) {
		uni.showToast({ title: e?.message || '删除失败', icon: 'none' })
	}
}

// 格式化显示
const formatCondition = (item: AlertItem): string => {
	const price = (n: number) => n > 0 ? n.toLocaleString() : '--'
	switch (item.alert_type) {
		case 'above':
			return `高于 $${price(item.threshold_price)}`
		case 'below':
			return `低于 $${price(item.threshold_price)}`
		case 'percent_up':
			return `涨幅 ${item.threshold_value}%`
		case 'percent_down':
			return `跌幅 ${item.threshold_value}%`
		case 'amplitude':
			return `振幅 ${item.threshold_value}%`
		default:
			return `${item.alert_type} $${price(item.threshold_price)}`
	}
}

const goToLogin = () => {
	uni.navigateTo({
		url: '/pages/login/login',
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}
</script>

<style scoped>
.alert-page {
    min-height: 100vh;
    background-color: var(--page-bg);
    padding: 20rpx;
}

.alert-container {
	width: 100%;
	max-width: 1200px;
	margin: 0 auto;
}

/* 页面头部 */
.page-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 10rpx 0 20rpx;
}

.header-title {
    font-size: 36rpx;
    font-weight: bold;
    color: var(--text-primary);
}

/* 添加按钮 */
.add-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 12rpx;
	padding: 16rpx 32rpx;
}

.add-btn:active {
	opacity: 0.8;
}

.btn-text {
	font-size: 28rpx;
	color: #ffffff;
	font-weight: 500;
}

.pc-only {
	display: none;
}

.mobile-only {
	display: flex;
	margin-top: 24rpx;
}

/* 未登录态 */
.guest-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 200rpx 0;
	gap: 40rpx;
}

.guest-title {
	font-size: 32rpx;
	color: var(--text-tertiary);
}

.guest-login-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 12rpx;
	padding: 20rpx 60rpx;
}

/* 表单卡片 */
.add-form-card {
	background-color: var(--card-bg);
	border-radius: 16rpx;
	padding: 30rpx;
	margin-bottom: 24rpx;
	box-shadow: var(--card-shadow);
}

.form-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24rpx;
}

.form-title {
	font-size: 32rpx;
	font-weight: 600;
	color: var(--text-primary);
}

.form-close {
	font-size: 48rpx;
	color: var(--text-tertiary);
	line-height: 1;
}

.form-group {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
	margin-bottom: 24rpx;
}

.form-label {
	font-size: 26rpx;
	font-weight: 500;
	color: var(--text-primary);
}

.form-input {
	width: 100%;
	height: 80rpx;
	padding: 0 20rpx;
	border: 2rpx solid var(--border-color);
	border-radius: 8rpx;
	font-size: 28rpx;
	color: var(--text-primary);
	box-sizing: border-box;
}

.base-price-row {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.base-price-input {
	flex: 1;
}

.base-price-hint-wrap {
	flex-shrink: 0;
	display: flex;
	align-items: center;
}

.base-price-hint {
	font-size: 24rpx;
	color: var(--text-tertiary);
	white-space: nowrap;
	cursor: pointer;
}

.base-price-hint.fetch-btn {
	color: #409eff;
}

.type-group {
	display: grid;
	grid-template-columns: repeat(5, 1fr);
	gap: 12rpx;
}

.radio-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 64rpx;
	border: 2rpx solid var(--border-color);
	border-radius: 8rpx;
	font-size: 24rpx;
	color: var(--text-secondary);
}

.radio-btn.active {
	border-color: #409eff;
	background-color: #ecf5ff;
	color: #409eff;
}

.form-row {
	flex-direction: row;
	justify-content: space-between;
	align-items: center;
}

.form-row-group {
	display: flex;
	gap: 20rpx;
}

.form-half {
	flex: 1;
}

.form-submit-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 8rpx;
	height: 80rpx;
}

.form-submit-btn:active {
	opacity: 0.85;
}

/* 列表 */
.alert-list {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	padding-bottom: 20rpx;
}

.alert-card {
	display: flex;
	justify-content: space-between;
	align-items: center;
	background-color: var(--card-bg);
	border-radius: 16rpx;
	padding: 28rpx;
	box-shadow: var(--card-shadow);
}

.rule-info {
	display: flex;
	flex-direction: column;
	gap: 10rpx;
	flex: 1;
	cursor: pointer;
}

.rule-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 16rpx;
}

.rule-symbol {
	font-size: 30rpx;
	font-weight: 600;
	color: var(--text-primary);
}

.badges {
	display: flex;
	gap: 10rpx;
}

.badge {
	font-size: 20rpx;
	padding: 4rpx 10rpx;
	border-radius: 6rpx;
}

.badge-active {
	background-color: #e6f7ec;
	color: #00c853;
}

.badge-continuous {
	background-color: #ecf5ff;
	color: #409eff;
}

.rule-condition {
	font-size: 26rpx;
	color: var(--text-secondary);
}

.rule-meta {
	font-size: 22rpx;
	color: var(--text-tertiary);
}

.rule-actions {
	display: flex;
	align-items: center;
	gap: 16rpx;
	flex-shrink: 0;
}

.edit-btn {
	font-size: 26rpx;
	color: #409eff;
	padding: 8rpx 16rpx;
}

.edit-btn:active {
	opacity: 0.6;
}

.delete-btn {
	font-size: 26rpx;
	color: #f56c6c;
	padding: 8rpx 16rpx;
}

.delete-btn:active {
	opacity: 0.6;
}

/* 空状态 */
.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 100rpx 0;
}

/* 骨架屏 */
.skeleton-state {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	padding: 20rpx 0;
}

.skeleton-card {
	height: 160rpx;
	background: linear-gradient(90deg, var(--border-color) 25%, var(--text-placeholder) 50%, var(--border-color) 75%);
	background-size: 200% 100%;
	animation: skeleton-loading 1.5s ease-in-out infinite;
	border-radius: 16rpx;
}

.skeleton-card.skeleton-wide {
	height: 180rpx;
}

@keyframes skeleton-loading {
	0% { background-position: 200% 0; }
	100% { background-position: -200% 0; }
}

.empty-text {
	font-size: 30rpx;
	color: var(--text-tertiary);
	margin-bottom: 12rpx;
}

.empty-hint {
	font-size: 24rpx;
	color: var(--text-tertiary);
}

/* PC 端 */
@media (min-width: 768px) {
	.pc-only {
		display: flex;
	}

	.mobile-only {
		display: none;
	}

	.alert-list {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 20rpx;
	}
}

/* 选择器 */
.picker-display {
	display: flex;
	justify-content: space-between;
	align-items: center;
	height: 80rpx;
	padding: 0 20rpx;
	border: 2rpx solid var(--border-color);
	border-radius: 8rpx;
}

.picker-text {
	font-size: 28rpx;
	color: var(--text-primary);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.picker-arrow {
	font-size: 20rpx;
	color: var(--text-tertiary);
	margin-left: 16rpx;
}
</style>
