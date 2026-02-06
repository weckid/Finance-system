# receipt_ocr.py — извлечение данных из фото чека (QR + OCR)
import re
from urllib.parse import unquote
from io import BytesIO


def _parse_qr_text(text):
    """Парсит данные из QR-кода российского чека (t=, s=, fn=, fp=)."""
    result = {'amount': None, 'date': None}
    if not text or not isinstance(text, str):
        return result
    params = {}
    for m in re.finditer(r'(?:^|[?&;])([^=]+)=([^&;\s]*)', text):
        k, v = m.group(1).lower().strip(), (m.group(2) or '').strip()
        try:
            params[k] = unquote(v)
        except Exception:
            params[k] = v
    if params.get('s'):
        try:
            s = float(str(params['s']).replace(',', '.').replace(' ', ''))
            if 0 < s < 1e8:
                result['amount'] = round(s, 2)
        except (ValueError, TypeError):
            pass
    if params.get('t'):
        t = str(params['t'])
        m = re.match(r'^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})', t)
        if m:
            result['date'] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}:{m.group(5)}:00"
    return result


def _extract_from_qr(image):
    """Извлекает данные из QR-кода на изображении (pyzbar)."""
    result = {'amount': None, 'date': None}
    try:
        from pyzbar import pyzbar
        from PIL import Image
        img = Image.open(image)
        if img.mode not in ('L', 'RGB'):
            img = img.convert('RGB')
        decoded = pyzbar.decode(img)
        for obj in decoded:
            if obj.type == 'QRCODE' and obj.data:
                try:
                    text = obj.data.decode('utf-8', errors='ignore')
                except Exception:
                    text = str(obj.data)
                qr = _parse_qr_text(text)
                if qr.get('amount'):
                    result['amount'] = qr['amount']
                if qr.get('date'):
                    result['date'] = qr['date']
                if result['amount']:
                    break
    except Exception:
        pass
    return result


def extract_receipt_data(image_file):
    """
    Извлекает сумму, магазин и категорию из изображения чека.
    Сначала пробует QR-код (pyzbar), затем OCR (Tesseract).
    """
    result = {'amount': None, 'merchant': '', 'raw_text': '', 'suggested_category': None}
    raw_text = ''

    try:
        if hasattr(image_file, 'read'):
            image_file.seek(0)
            img_bytes = BytesIO(image_file.read())
            image_file.seek(0)
        else:
            img_bytes = image_file
    except Exception:
        img_bytes = image_file
    if hasattr(img_bytes, 'seek'):
        img_bytes.seek(0)

    qr_data = _extract_from_qr(img_bytes)
    if qr_data.get('amount'):
        result['amount'] = qr_data['amount']
    if qr_data.get('date'):
        result['date'] = qr_data['date']

    img_bytes.seek(0)

    try:
        import pytesseract
        from PIL import Image, ImageEnhance
        import sys
        import os
        if sys.platform == 'win32':
            for path in [r'C:\Program Files\Tesseract-OCR\tesseract.exe', r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe']:
                if os.path.isfile(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
    except ImportError:
        return result

    try:
        img = Image.open(img_bytes)
        if img.mode not in ('L', 'RGB'):
            img = img.convert('RGB')
        w, h = img.size
        if w < 800 or h < 800:
            scale = max(800 / w, 800 / h, 1.5)
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3)
        raw_text = ''
        for lang in ('rus+eng', 'rus', 'eng'):
            try:
                raw_text = pytesseract.image_to_string(img, lang=lang, config='--psm 6 --oem 3')
                if raw_text and len(raw_text.strip()) > 10:
                    break
            except Exception:
                try:
                    raw_text = pytesseract.image_to_string(img, lang=lang)
                    if raw_text and len(raw_text.strip()) > 10:
                        break
                except Exception:
                    raw_text = ''
    except Exception:
        raw_text = ''

    result['raw_text'] = raw_text

    if not result['amount'] and raw_text:
        amount_patterns = [
            r'=\s*(\d+)(?:[.,]\d{2})?\b',
            r'(?:итого|итог|сумма|наличными|картой)\s*[=:\s]*(\d+)(?:[.,]\d{2})?',
            r'(\d{3,7})(?:[.,]\d{2})?\s*[р₽]',
            r'\b(\d{3,7})(?:[.,]\d{2})?\b',
        ]
        all_amounts = []
        for pattern in amount_patterns:
            for m in re.finditer(pattern, raw_text, re.IGNORECASE):
                try:
                    num_str = m.group(1).replace(' ', '').replace(',', '.')
                    val = float(num_str)
                    if 10 <= val < 1e7:
                        all_amounts.append(round(val, 2))
                except (ValueError, TypeError):
                    continue
        if all_amounts:
            result['amount'] = max(all_amounts)

    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    merchant_candidates = []
    for line in lines[:30]:
        line = line.strip()
        if len(line) < 4 or re.match(r'^[\d\s.,:]+$', line):
            continue
        if not re.search(r'[а-яА-Яa-zA-Z]', line):
            continue
        line_upper = line.upper()
        if any(x in line_upper for x in ['ЗАО', 'ООО', 'ИП', 'ТОРГОВЫЙ', 'МАГАЗИН', 'ОБЪЕКТ']):
            merchant_candidates.insert(0, line)
        elif len(line) > 5 and not re.match(r'^\d+$', line):
            merchant_candidates.append(line)
    if merchant_candidates:
        result['merchant'] = merchant_candidates[0][:100]
    elif lines and len(lines[0]) > 6:
        first = lines[0].strip()
        if re.search(r'[а-яА-Яa-zA-Z]', first):
            result['merchant'] = first[:100]

    text_lower = raw_text.lower()
    keywords = [
        ('Здоровье', ['аптека', 'лекарств', 'клиника', 'врач', 'медицин']),
        ('Кафе и рестораны', ['кафе', 'ресторан', 'кофе', 'обед', 'ужин', 'бар', 'пиццерия']),
        ('Еда', ['продукты', 'молоко', 'хлеб', 'еда', 'супермаркет', 'магнит', 'пятерочка', 'перекресток']),
        ('Одежда и обувь', ['футболка', 'одежда', 'обувь', 'топ дев', 'топ мал']),
        ('Продукты', ['продукты', 'молоко', 'хлеб']),
        ('Коммунальные услуги', ['жкх', 'коммунал', 'электр', 'газ', 'вода', 'интернет', 'связь']),
        ('Транспорт', ['азс', 'бензин', 'транспорт', 'метро', 'заправка']),
        ('Такси', ['такси', 'яндекс', 'uber']),
        ('Развлечения', ['кино', 'театр', 'игр']),
    ]
    for cat, words in keywords:
        if any(w in text_lower for w in words):
            result['suggested_category'] = cat
            break

    return result
