// 价格格式化函数
import { convertPrice, getCurrentCurrency, currencySymbols } from './exchangeRate'

export const formatPrice = (price: number, targetCurrency?: string): string => {
	// 如果指定了目标货币，进行转换
	const currency = targetCurrency || getCurrentCurrency()
	
	// 只有非 USD 才需要转换
	let finalPrice = price
	if (currency !== 'USD') {
		finalPrice = convertPrice(price, currency)
	}
	
	// 获取货币符号
	const symbol = currencySymbols[currency] || '$'
	
	// 格式化数字
	let formatted: string
	if (finalPrice >= 1000) {
		formatted = finalPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
	} else if (finalPrice >= 1) {
		formatted = finalPrice.toFixed(4)
	} else {
		// 小于1的数字正常显示
		formatted = finalPrice.toFixed(8).replace(/(\.0+)|(0+$)/, '')
		if (!formatted || formatted === '0') {
			formatted = '0.00'
		}
	}
	
	return `${symbol}${formatted}`
}

// 纯格式化（不转换货币，用于 K 线等特殊场景）
export const formatPriceRaw = (price: number): string => {
	if (price >= 1000) return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
	if (price >= 1) return price.toFixed(4)
	const fixed = price.toFixed(12).replace(/\.?0+$/, '')
	if (price > 0 && price < 1 && fixed.length > 8) {
		const match = fixed.match(/^0\.0+(\d)/)
		if (match) {
			const zeros = fixed.indexOf(match[1]) - 2
			const rest = fixed.substring(fixed.indexOf(match[1]))
			return `0.0{${zeros}}${rest}`
		}
	}
	return fixed || '0.00'
}

// 数字格式化（无货币符号，用于资产页面总计等）
export const formatNumber = (n: number): string => {
	if (n == null || isNaN(n)) return '0.00'
	// 处理极大或极小的数，避免精度问题
	if (!isFinite(n)) return '0.00'
	// 保留2位小数
	const fixed = n.toFixed(2)
	// 移除尾部 .00
	return fixed.replace(/\.00$/, '')
}