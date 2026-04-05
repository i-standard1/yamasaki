// scripts/test-results-to-xlsx.mjs
// ユニットテスト結果のJSONをExcelに変換する。CI用。
// 使い方: node scripts/test-results-to-xlsx.mjs <input.json> <output.xlsx>
import fs from 'fs';
import ExcelJS from 'exceljs';

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) {
  console.error('Usage: node test-results-to-xlsx.mjs <input.json> <output.xlsx>');
  process.exit(1);
}

const raw = fs.readFileSync(inputPath, 'utf-8');
const data = JSON.parse(raw);

const workbook = new ExcelJS.Workbook();
const sheet = workbook.addWorksheet('テスト結果');

// ヘッダー
sheet.columns = [
  { header: 'テストスイート', key: 'suite', width: 40 },
  { header: 'テスト名', key: 'name', width: 50 },
  { header: '結果', key: 'status', width: 10 },
  { header: '実行時間(ms)', key: 'duration', width: 15 },
  { header: 'エラー内容', key: 'error', width: 60 },
];

// ヘッダー行のスタイル
sheet.getRow(1).font = { bold: true };
sheet.getRow(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFE0E0E0' } };

// Vitest / Jest 形式のJSON対応
const testResults = data.testResults || data.suites || [];

for (const suite of testResults) {
  const suiteName = (suite.name || suite.filename || '').replace(process.cwd(), '');
  const tests = suite.assertionResults || suite.tests || suite.cases || [];

  for (const test of tests) {
    const status = test.status === 'passed' ? 'OK' : 'NG';
    const name = test.fullName || test.title || test.name || '';
    const duration = test.duration || 0;
    const error = test.failureMessages?.join('\n') || test.error?.message || '';

    const row = sheet.addRow({
      suite: suiteName,
      name: name,
      status: status,
      duration: duration,
      error: error,
    });

    if (status === 'NG') {
      row.getCell('status').font = { color: { argb: 'FFFF0000' }, bold: true };
    } else {
      row.getCell('status').font = { color: { argb: 'FF008000' } };
    }
  }
}

// サマリー行
const total = sheet.rowCount - 1;
const passed = sheet.getColumn('status').values.filter(v => v === 'OK').length;
const failed = total - passed;

const summarySheet = workbook.addWorksheet('サマリー');
summarySheet.columns = [
  { header: '項目', key: 'label', width: 20 },
  { header: '値', key: 'value', width: 15 },
];
summarySheet.getRow(1).font = { bold: true };
summarySheet.addRow({ label: '総テスト数', value: total });
summarySheet.addRow({ label: '成功', value: passed });
summarySheet.addRow({ label: '失敗', value: failed });
summarySheet.addRow({ label: '成功率', value: total > 0 ? `${Math.round(passed / total * 100)}%` : '-' });

await workbook.xlsx.writeFile(outputPath);
console.log(`✅ ${outputPath} に ${total} 件のテスト結果を出力しました`);
