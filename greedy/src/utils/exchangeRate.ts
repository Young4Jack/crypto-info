// 汇率服务 - 从后端获取汇率数据并缓存
import { get } from '@/utils/request'

const STORAGE_KEY = 'user_pricing_currency'

interface ExchangeRates {
	CNY: number
	EUR: number
	JPY: number
}

interface CurrencyConfig {
	current_pricing_currency: string
	available_currencies: string[]
	exchange_rates: ExchangeRates
}

let cachedConfig: CurrencyConfig | null = null
let initialized = false

// 从后端获取货币配置（汇率）
export const fetchCurrencyConfig = async (): Promise<CurrencyConfig | null> => {
	try {
		const res = await get<CurrencyConfig>('/api/system-settings/public')
		if (res.data) {
			cachedConfig = {
				current_pricing_currency: res.data.current_pricing_currency || 'USD',
				available_currencies: res.data.available_currencies || ['USD', 'CNY', 'EUR', 'JPY'],
				exchange_rates: res.data.exchange_rates || { CNY: 1, EUR: 1, JPY: 1 }
			}
			return cachedConfig
		}
	} catch (e) {
		console.error('获取货币配置失败', e)
	}
	return null
}

// 获取当前计价货币
export const getCurrentCurrency = (): string => {
	// 优先使用缓存
	if (cachedConfig?.current_pricing_currency) {
		return cachedConfig.current_pricing_currency
	}
	// 其次检查本地存储（未登录用户）
	try {
		const stored = uni.getStorageSync(STORAGE_KEY)
		if (stored) return stored
	} catch {}
	// 默认 USD
	return 'USD'
}

// 设置当前计价货币
export const setCurrentCurrency = (currency: string): void => {
	try {
		uni.setStorageSync(STORAGE_KEY, currency)
	} catch {}
	// 更新缓存
	if (cachedConfig) {
		cachedConfig.current_pricing_currency = currency
	} else {
		cachedConfig = {
			current_pricing_currency: currency,
			available_currencies: ['USD', 'CNY', 'EUR', 'JPY'],
			exchange_rates: { CNY: 1, EUR: 1, JPY: 1 }
		}
	}
}

// 获取汇率
export const getExchangeRates = (): ExchangeRates => {
	if (cachedConfig?.exchange_rates) {
		return cachedConfig.exchange_rates
	}
	return { CNY: 1, EUR: 1, JPY: 1 }
}

// 转换价格到指定货币
export const convertPrice = (priceUSD: number, targetCurrency: string): number => {
	// USD 直接返回，不需要转换
	if (targetCurrency === 'USD') {
		return priceUSD
	}
	const rates = getExchangeRates()
	const rate = rates[targetCurrency as keyof ExchangeRates]
	if (rate) {
		return priceUSD * rate
	}
	return priceUSD
}

// 初始化汇率（在应用启动时调用）
export const initCurrencyService = async (): Promise<void> => {
	if (initialized) return
	
	// 先检查本地存储的货币
	let localCurrency = 'USD'
	try {
		localCurrency = uni.getStorageSync(STORAGE_KEY) || 'USD'
	} catch {}
	
	// 如果是 USD，不请求后端数据（USD 无需汇率）
	if (localCurrency === 'USD') {
		cachedConfig = {
			current_pricing_currency: 'USD',
			available_currencies: ['USD', 'CNY', 'EUR', 'JPY'],
			exchange_rates: { CNY: 1, EUR: 1, JPY: 1 }
		}
		initialized = true
		return
	}
	
	// 非 USD 需要获取汇率
	await fetchCurrencyConfig()
	initialized = true
}

// 检查是否已初始化
export const isCurrencyInitialized = (): boolean => initialized

// 货币符号映射
export const currencySymbols: Record<string, string> = {
	USD: '$',
	CNY: '¥',
	EUR: '€',
	JPY: '¥'
}

// 货币名称映射
export const currencyNames: Record<string, string> = {
	USD: '美元',
	CNY: '人民币',
	EUR: '欧元',
	JPY: '日元'
}