<template>
	<view class="alert-page">
		<view class="alert-container">
			<!-- 页面头部 -->
			<view class="page-header">
				<text class="header-title">预警中心</text>
				<!-- PC 端显示的添加按钮 -->
				<view class="add-btn pc-only" @tap="handleAdd">
					<text class="btn-text">+ 添加预警</text>
				</view>
			</view>

			<!-- 预警规则列表 -->
			<scroll-view scroll-y class="alert-scroll">
				<view class="alert-list">
					<view
						v-for="item in alertRules"
						:key="item.id"
						class="alert-card"
					>
						<view class="rule-info">
							<view class="rule-header">
								<text class="rule-symbol">{{ item.symbol }}</text>
								<text :class="['rule-status', item.enabled ? 'active' : 'inactive']">
									{{ item.enabled ? '监控中' : '已暂停' }}
								</text>
							</view>
							<text class="rule-condition">{{ item.condition }}</text>
							<text class="rule-time">创建于 {{ item.createdAt }}</text>
						</view>
						<view class="rule-action">
							<switch
								:checked="item.enabled"
								color="#409EFF"
								@change="toggleRule(item)"
							/>
						</view>
					</view>

					<view v-if="alertRules.length === 0" class="empty-state">
						<text class="empty-text">暂无预警规则</text>
						<text class="empty-hint">点击添加按钮创建你的第一条预警</text>
					</view>
				</view>
			</scroll-view>

			<!-- 移动端底部添加按钮 -->
			<view class="add-btn mobile-only" @tap="handleAdd">
				<text class="btn-text">+ 添加预警</text>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
// @update: 实现预警中心页面，含规则列表、开关控制与响应式添加按钮
interface AlertRule {
	id: number
	symbol: string
	condition: string
	enabled: boolean
	createdAt: string
}

const alertRules = ref<AlertRule[]>([
	{ id: 1, symbol: 'BTC', condition: '价格上涨超过 $70,000', enabled: true, createdAt: '2024-03-15' },
	{ id: 2, symbol: 'ETH', condition: '价格下跌低于 $3,200', enabled: true, createdAt: '2024-03-14' },
	{ id: 3, symbol: 'SOL', condition: '24h 涨幅超过 10%', enabled: false, createdAt: '2024-03-10' },
])

const toggleRule = (item: AlertRule) => {
	item.enabled = !item.enabled
	uni.showToast({
		title: item.enabled ? '已开启监控' : '已暂停监控',
		icon: 'none',
	})
}

const handleAdd = () => {
	uni.showToast({ title: '添加预警功能开发中', icon: 'none' })
}
</script>

<style scoped>
.alert-page {
	display: flex;
	justify-content: center;
	min-height: 100vh;
	background-color: #f5f7fa;
	padding: 20rpx;
}

.alert-container {
	width: 100%;
	max-width: 1200px;
	display: flex;
	flex-direction: column;
	height: 100%;
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
	color: #1a1a2e;
}

/* 添加按钮通用样式 */
.add-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 12rpx;
	padding: 16rpx 32rpx;
	transition: opacity 0.2s;
}

.add-btn:active {
	opacity: 0.8;
}

.btn-text {
	font-size: 28rpx;
	color: #ffffff;
	font-weight: 500;
}

/* 响应式显隐控制 */
.pc-only {
	display: none;
}

.mobile-only {
	margin-top: 20rpx;
}

/* 滚动列表 */
.alert-scroll {
	flex: 1;
	height: 0;
}

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
	background-color: #ffffff;
	border-radius: 16rpx;
	padding: 28rpx;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}

.rule-info {
	display: flex;
	flex-direction: column;
	gap: 10rpx;
	flex: 1;
}

.rule-header {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.rule-symbol {
	font-size: 30rpx;
	font-weight: 600;
	color: #1a1a2e;
}

.rule-status {
	font-size: 22rpx;
	padding: 4rpx 12rpx;
	border-radius: 6rpx;
}

.rule-status.active {
	background-color: #e6f7ec;
	color: #00c853;
}

.rule-status.inactive {
	background-color: #f0f2f5;
	color: #909399;
}

.rule-condition {
	font-size: 26rpx;
	color: #606266;
}

.rule-time {
	font-size: 22rpx;
	color: #c0c4cc;
}

.rule-action {
	margin-left: 20rpx;
}

/* 空状态 */
.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 100rpx 0;
}

.empty-text {
	font-size: 30rpx;
	color: #909399;
	margin-bottom: 12rpx;
}

.empty-hint {
	font-size: 24rpx;
	color: #c0c4cc;
}

/* PC 端响应式 */
@media (min-width: 768px) {
	.pc-only {
		display: flex;
	}

	.mobile-only {
		display: none;
	}
}
</style>
