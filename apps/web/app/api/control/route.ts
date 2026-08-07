import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { action } = await req.json();

  // Control signals processing
  if (action === 'pause') {
    return NextResponse.json({ message: 'پائپ لائن روک دی گئی ہے۔', action: 'paused' });
  } else if (action === 'resume') {
    return NextResponse.json({ message: 'پائپ لائن دوبارہ شروع کر دی گئی ہے۔', action: 'resumed' });
  }

  return NextResponse.json({ error: 'غلط ایکشن' }, { status: 400 });
}
