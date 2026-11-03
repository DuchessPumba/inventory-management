// Marks a numeric cell so it is written as-is (no formula-injection prefix),
// optionally fixed to a number of decimals, e.g. csvNumber(12.5, 2) -> 12.50
export const csvNumber = (value, decimals) => ({
  csvRaw:
    decimals === undefined ? String(value) : Number(value).toFixed(decimals),
})

const escapeCell = (cell) => {
  if (cell && typeof cell === 'object' && 'csvRaw' in cell) return cell.csvRaw
  let text = cell === null || cell === undefined ? '' : String(cell)
  // Spreadsheets run text starting with = + - @ as a formula; a leading quote forces plain text
  if (/^[=+\-@]/.test(text)) text = `'${text}`
  // RFC 4180: quote cells containing comma, quote or newline, doubling embedded quotes
  if (/[",\r\n]/.test(text)) text = `"${text.replace(/"/g, '""')}"`
  return text
}

// Builds CSV text (CRLF line endings, no BOM) from an array of row arrays
export const buildCsv = (rows) =>
  rows.map((row) => row.map(escapeCell).join(',')).join('\r\n')

// Built from a char code, not typed as a literal: an invisible literal BOM can be stripped or
// rewritten by editors and formatters
const BOM = String.fromCharCode(0xfeff)

// Downloads rows (array of arrays) as a UTF-8 CSV with BOM so Excel reads Japanese text
export const downloadCsv = (filename, rows) => {
  const blob = new Blob([BOM, buildCsv(rows)], {
    type: 'text/csv;charset=utf-8;',
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function useCsvExport() {
  return { downloadCsv, buildCsv, csvNumber }
}
