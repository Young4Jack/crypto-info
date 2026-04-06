import { ref } from 'vue'

// 全局响应式配置（所有模块共享）
export const apiBase = ref('')
export const wsBase = ref('')

// 检测是否为 IP 地址（IPv4 或 IPv6）
function isIpAddress(host: string): boolean {
	const ipv4 = /^\d{1,3}(\.\d{1,3}){3}$/
	const ipv6 = /^\[?[0-9a-fA-F:]+\]?$/
	return ipv4.test(host) || ipv6.test(host)
}

// 补全协议前缀：将裸域名转为完整 URL
function normalizeUrl(raw: string, protocolHint?: string): { http: string; ws: string } {
	let url = raw.trim()
	
	// 1. 先检测原始 URL 是否自带协议
	const hasProtocol = url.startsWith('http://') || url.startsWith('https://') || 
	                    url.startsWith('ws://') || url.startsWith('wss://')
	
	let isHttps: boolean
	
	if (hasProtocol) {
		// 有协议 → 按原始的来
		isHttps = url.startsWith('https://') || url.startsWith('wss://')
		url = url.replace(/^https?:\/\//, '').replace(/^wss?:\/\//, '')
	} else if (protocolHint) {
		// 无协议但传了提示 → 按提示
		isHttps = protocolHint.startsWith('https') || protocolHint.startsWith('wss')
	} else {
		// 无协议也没提示 → 智能判断：IP 用 http，域名用 https
		const host = url.split('/')[0].split(':')[0]
		isHttps = !isIpAddress(host)
	}
	
	if (!url) return { http: '', ws: '' }
	const http = isHttps ? `https://${url}` : `http://${url}`
	const ws = isHttps ? `wss://${url}` : `ws://${url}`
	return { http, ws }
}

// 优先级 1：用当前域名尝试请求后端接口
// 核心原则：只有后端明确返回 base_url 才设置 apiBase，否则保持空字符串（走相对路径/Vite 代理）
async function tryCurrentDomain(): Promise<boolean> {
	// #ifdef H5
	const host = window.location.host
	if (!host) return false

	return new Promise((resolve) => {
		uni.request({
			url: `/api/system-settings/public`,
			method: 'GET',
			timeout: 5000,
			success: (res) => {
				if (res.statusCode >= 200 && res.statusCode < 300) {
					const data = res.data as any
					const base = data?.base_url
					if (base) {
						const { http, ws } = normalizeUrl(base)
						apiBase.value = http
						wsBase.value = ws
						resolve(true)
					} else {
						// 请求成功但没返回 base_url，保持 apiBase 为空（走相对路径）
						resolve(true)
					}
				} else {
					resolve(false)
				}
			},
			fail: () => {
				resolve(false)
			},
		})
	})
	// #endif
	// #ifndef H5
	return false
	// #endif
}

// 优先级 2：环境变量兜底（生产环境域名默认 https）
function loadFromEnv() {
	const base = (import.meta as any).env?.VITE_API_BASE || ''
	if (base) {
		const { http, ws } = normalizeUrl(base, 'https')
		apiBase.value = http
		wsBase.value = ws
	}
}

// 入口函数：按优先级加载配置
export async function initConfig() {
	const success = await tryCurrentDomain()
	if (!success) {
		loadFromEnv()
	}
}
