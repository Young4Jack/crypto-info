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
			const fixedPrice = finalPrice.toFixed(2)
			const parts = fixedPrice.split('.')
			parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',')
			formatted = parts.join('.')
		} else if (finalPrice >= 1) {
		formatted = finalPrice
	} else {
		const fixed = finalPrice.toFixed(12).replace(/\.?0+$/, '')
		if (finalPrice > 0 && finalPrice < 1 && fixed.length > 8) {
			const match = fixed.match(/^0\.0+(\d)/)
			if (match) {
				const zeros = fixed.indexOf(match[1]) - 2
				const rest = fixed.substring(fixed.indexOf(match[1]))
				formatted = `0.0{${zeros}}${rest}`
			} else {
				formatted = fixed || '0.00'
			}
		} else {
			formatted = fixed || '0.00'
		}
	}
	
	return `${symbol}${formatted}`
}

// 纯格式化（不转换货币，用于 K 线等特殊场景）
export const formatPriceRaw = (price: number): string => {
	if (price >= 1000) {
		const fixedPrice = price.toFixed(2)
		const parts = fixedPrice.split('.')
		parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',')
		return parts.join('.')
	}
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