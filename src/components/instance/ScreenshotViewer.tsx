import { useRef, useEffect } from 'react';
import { useAppStore, type Instance } from '@/stores/appStore';

interface ScreenshotViewerProps {
  instance: Instance | null;
}

export function ScreenshotViewer({ instance }: ScreenshotViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { wsConnected } = useAppStore();

  const currentStep = instance?.steps.find(
    (s) => s.no === instance?.activeStepNo
  ) || instance?.steps[instance.steps.length - 1];

  useEffect(() => {
    if (!instance || !currentStep) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const img = canvas.previousElementSibling as HTMLImageElement;
    if (!img) return;

    const drawOverlay = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const rect = img.getBoundingClientRect();
      canvas.width = Math.max(1, Math.floor(rect.width));
      canvas.height = Math.max(1, Math.floor(rect.height));
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (!currentStep.overlay) return;

      const { baseW = 1280, baseH = 720 } = currentStep.overlay;
      const fit = containFit(rect.width, rect.height, baseW, baseH);
      const ox = (rect.width - fit.w) / 2;
      const oy = (rect.height - fit.h) / 2;

      ctx.save();
      ctx.translate(ox, oy);
      ctx.scale(fit.w / baseW, fit.h / baseH);

      const boxes = currentStep.overlay.boxes || [];
      boxes.forEach((b, idx) => {
        const alpha = idx === 0 ? 0.95 : 0.55;
        ctx.lineWidth = idx === 0 ? 3 : 2;
        ctx.strokeStyle = idx === 0 ? `rgba(59,130,246,${alpha})` : `rgba(6,182,212,${alpha})`;
        ctx.fillStyle = idx === 0 ? 'rgba(59,130,246,0.12)' : 'rgba(6,182,212,0.10)';
        ctx.beginPath();
        ctx.roundRect(b.x, b.y, b.w, b.h, 10);
        ctx.fill();
        ctx.stroke();
      });

      if (currentStep.overlay.point) {
        const { x, y } = currentStep.overlay.point;
        ctx.strokeStyle = 'rgba(245,158,11,0.95)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, 10, 0, Math.PI * 2);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(x - 18, y);
        ctx.lineTo(x + 18, y);
        ctx.moveTo(x, y - 18);
        ctx.lineTo(x, y + 18);
        ctx.stroke();
      }

      ctx.restore();
    };

    drawOverlay();
    window.addEventListener('resize', drawOverlay);
    return () => window.removeEventListener('resize', drawOverlay);
  }, [currentStep, instance]);

  const placeholderUrl = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(`<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0B1220" />
      <stop offset="1" stop-color="#1F2A44" />
    </linearGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#bg)" />
  <rect x="40" y="40" width="1200" height="640" rx="22" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.10)" />
  <text x="640" y="380" fill="rgba(229,231,235,0.86)" font-family="sans-serif" font-size="24" text-anchor="middle">等待开始推流</text>
</svg>`)}`;

  if (!instance) {
    return (
      <div className="border border-[var(--border)] rounded-[var(--radius)] overflow-hidden bg-[#0b1220] flex flex-col min-h-[360px]">
        <div className="flex items-center justify-between gap-[10px] px-3 py-[10px] border-b border-white/10 text-gray-200">
          <div>
            <div className="font-bold text-sm">视觉画面 + 标注层</div>
            <div className="text-xs text-gray-400">Overlay: bbox / click point / multi-candidates</div>
          </div>
          <div className="text-xs text-gray-400">WS: disconnected</div>
        </div>
        <div className="flex-1 relative flex items-center justify-center overflow-hidden">
          <img src={placeholderUrl} alt="screenshot" className="w-full h-full object-contain" />
          <canvas ref={canvasRef} className="absolute inset-0 pointer-events-none" />
        </div>
      </div>
    );
  }

  return (
    <div className="border border-[var(--border)] rounded-[var(--radius)] overflow-hidden bg-[#0b1220] flex flex-col">
      <div className="flex items-center justify-between gap-[10px] px-3 py-[10px] border-b border-white/10 text-gray-200">
        <div>
          <div className="font-bold text-sm">视觉画面 + 标注层</div>
          <div className="text-xs text-gray-400">Overlay: bbox / click point / multi-candidates</div>
        </div>
        <div className="text-xs text-gray-400">WS: {wsConnected ? 'connected' : 'disconnected'}</div>
      </div>
      <div className="flex-1 relative flex items-center justify-center overflow-hidden">
        <img
          src={currentStep?.screenshot || placeholderUrl}
          alt="screenshot"
          className="w-full h-full object-contain"
          onLoad={(e) => {
            const img = e.currentTarget;
            const canvas = canvasRef.current;
            if (canvas && img) {
              const rect = img.getBoundingClientRect();
              canvas.width = Math.floor(rect.width);
              canvas.height = Math.floor(rect.height);
            }
          }}
        />
        <canvas ref={canvasRef} className="absolute inset-0 pointer-events-none" />
      </div>
    </div>
  );
}

const containFit = (cw: number, ch: number, iw: number, ih: number) => {
  const cr = cw / ch;
  const ir = iw / ih;
  if (ir > cr) {
    const w = cw;
    const h = cw / ir;
    return { w, h };
  }
  const h = ch;
  const w = ch * ir;
  return { w, h };
};
