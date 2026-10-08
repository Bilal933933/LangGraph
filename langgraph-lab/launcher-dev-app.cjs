const { spawn } = require('child_process');
const path = require('path');
const dir = path.join(__dirname);
const python = 'E:\\heard\\LangGraph\\langgraph-lab\\.venv\\Scripts\\python.exe';
// psycopg غير المتزامن يرفض حلقة Windows الافتراضية (ProactorEventLoop)
// فينهار الإقلاع عند تسخين الرسم — uvicorn يبني حلقته قبل استيراد التطبيق،
// لذلك نستبدل مصنع الحلقة هنا قبل بدء uvicorn (ملف المشغّل مسموح تعديله دائمًا).
// ملاحظة: ممنوع تنكير asyncio.ProactorEventLoop نفسه لأن psycopg يفحص
// isinstance ضده — الترقيع يكون على مصنع uvicorn فقط.
const prelude = [
  'import asyncio',
  'import uvicorn.loops.asyncio as _ula',
  '_ula.asyncio_loop_factory = lambda use_subprocess=False: asyncio.SelectorEventLoop',
  'from uvicorn import run',
  'run("app.main:app", host="127.0.0.1", port=5003)',
].join('; ');
const child = spawn(python, ['-c', prelude], {
  cwd: dir,
  stdio: 'inherit',
  env: {
    ...process.env,
    PYTHONUTF8: '1',
    CORS_ORIGINS: 'http://localhost:3006,http://127.0.0.1:3006',
  },
});
child.on('exit', (code) => process.exit(code ?? 1));
child.on('error', (err) => { console.error('launcher failed:', err.message); process.exit(1); });
process.on('SIGINT', () => child.kill());
process.on('SIGTERM', () => child.kill());
