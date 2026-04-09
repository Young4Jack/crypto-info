// 价格格式化函数
export const formatPrice = (price: number): string => {
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