from __future__ import annotations

import json
import os
import re
import hashlib
import zipfile
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timezone, date as date_cls
from collections import Counter, defaultdict
from typing import Any
import yaml


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def clean_scalar(v: Any) -> Any:
    if isinstance(v, (datetime, date_cls)):
        return v.isoformat()
    if isinstance(v, dict):
        return {str(k): clean_scalar(val) for k, val in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [clean_scalar(x) for x in v]
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    return str(v)


def extract_frontmatter(text: str) -> tuple[dict[str, Any], str, str, bool]:
    """Return parsed metadata, raw frontmatter, body, parse_success.

    Accepts files where an H1 filename appears before the first --- block.
    """
    text = text.lstrip('\ufeff')
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines[:20]) if line.strip() == '---']
    if not starts:
        return {}, '', text, False
    start = starts[0]
    end = None
    for i in range(start + 1, min(len(lines), start + 140)):
        if lines[i].strip() == '---':
            end = i
            break
    if end is None:
        return {}, '', text, False
    raw = ''.join(lines[start + 1:end])
    pre = ''.join(lines[:start]).strip()
    post = ''.join(lines[end + 1:])
    body = (pre + ('\n\n' if pre and post.strip() else '') + post).strip('\n') + '\n'
    meta: dict[str, Any] = {}
    success = False
    try:
        parsed = yaml.safe_load(raw)
        if isinstance(parsed, dict):
            meta = clean_scalar(parsed)
            success = True
    except Exception:
        pass
    if not success:
        # Conservative line-based fallback. It preserves only simple top-level fields.
        for line in raw.splitlines():
            if not line or line.startswith((' ', '\t', '-', '#')) or ':' not in line:
                continue
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            try:
                parsed_value = yaml.safe_load(value) if value else None
            except Exception:
                parsed_value = value.strip('"\'')
            meta[key] = clean_scalar(parsed_value)
    return meta, raw.strip(), body, success


def listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        if s.startswith('[') and s.endswith(']'):
            try:
                v = yaml.safe_load(s)
                if isinstance(v, list):
                    return v
            except Exception:
                pass
        if ',' in s:
            return [x.strip() for x in s.split(',') if x.strip()]
        return [s]
    return [value]


def normalized_source_name(path: str) -> str:
    base = os.path.basename(path)
    base = re.sub(r'\.md$', '', base, flags=re.I)
    base = base.strip().lstrip('#').strip()
    # Repair obvious filename-prefix typos while preserving the original path separately.
    if re.match(r'^TTOBY_', base, re.I):
        base = base[1:]
    elif re.match(r'^OBY_', base, re.I):
        base = 'T' + base
    return base


def filename_series(name: str) -> str:
    m = re.match(r'^TOBY_([A-Za-z]+)', name, re.I)
    return m.group(1).upper() if m else 'OTHER'


def document_kind(series: str) -> str:
    mapping = {
        'T': 'source_scroll',
        'L': 'lore_scroll',
        'C': 'community_commentary',
        'QA': 'question_answer',
        'QL': 'lore_questions',
        'QR': 'lore_reflection',
        'TECH': 'technical_lore',
        'ARC': 'arc_reference',
        'SARC': 'arc_reference',
        'S': 'codex_scroll',
        'R': 'rune_scroll',
        'RUNE': 'rune_scroll',
        'F': 'lore_fragment',
        'PF': 'lore_fragment',
        'RF': 'lore_fragment',
        'A': 'lore_fragment',
        'Z': 'wisdom_scroll',
        'ZEN': 'wisdom_scroll',
        'TAO': 'wisdom_scroll',
        'SUTRA': 'wisdom_scroll',
        'PHI': 'philosophy_scroll',
        'TA': 'toadaid_public_lore',
        'LG': 'lore_guide',
    }
    return mapping.get(series, 'lore_document')


def infer_languages(meta: dict[str, Any], source_name: str, body: str) -> list[str]:
    vals: list[str] = []
    for key in ('language', 'languages', 'lang'):
        vals.extend(str(x) for x in listify(meta.get(key)))
    upper = source_name.upper()
    if 'EN-ZH' in upper or 'EN_ZH' in upper or 'ZH-EN' in upper:
        vals.extend(['EN', 'ZH'])
    elif re.search(r'(?:_|-)ZH(?:_|-|$)', upper):
        vals.append('ZH')
    elif re.search(r'(?:_|-)EN(?:_|-|$)', upper):
        vals.append('EN')
    if re.search(r'[\u3400-\u9fff]', body):
        vals.append('ZH')
    if re.search(r'[A-Za-z]{4,}', body):
        vals.append('EN')
    out: list[str] = []
    for v in vals:
        x = v.strip().lower()
        if 'zh' in x or 'chinese' in x or '中文' in x:
            x = 'zh'
        elif 'en' in x or 'english' in x:
            x = 'en'
        else:
            continue
        if x not in out:
            out.append(x)
    return out or ['und']


def extract_date(meta: dict[str, Any], source_name: str) -> tuple[str | None, str | None, str]:
    raw = None
    for key in ('date', 'Date', 'DATE', 'timestamp', 'Timestamp', 'updated'):
        if meta.get(key) not in (None, ''):
            raw = str(meta[key]).strip()
            break
    if raw is None:
        m = re.search(r'(20\d{2}[-_]\d{2}[-_](?:\d{2}|XX))', source_name, re.I)
        if m:
            raw = m.group(1).replace('_', '-')
    if raw:
        m = re.search(r'(20\d{2})-(\d{2})-(\d{2})', raw)
        if m:
            iso = m.group(0)
            try:
                datetime.strptime(iso, '%Y-%m-%d')
                return iso, raw, 'day'
            except ValueError:
                pass
        m = re.search(r'(20\d{2})-(\d{2})', raw)
        if m and 'XX' not in raw.upper():
            return None, raw, 'month_or_unvalidated'
        return None, raw, 'unknown_or_incomplete'
    return None, None, 'unknown'


def extract_title(meta: dict[str, Any], body: str, source_name: str) -> str:
    for key in ('title', 'Title', 'TITLE', 'filename'):
        val = meta.get(key)
        if val:
            title = str(val).strip().strip('"\'')
            if title.lower().endswith('.md'):
                title = re.sub(r'\.md$', '', title, flags=re.I)
            return title
    h1s = [re.sub(r'^#\s+', '', line).strip() for line in body.splitlines() if re.match(r'^#\s+', line)]
    for h in h1s:
        if h and h.lower() != source_name.lower() and not h.lower().endswith('.md'):
            return h
    if h1s:
        return re.sub(r'\.md$', '', h1s[0], flags=re.I)
    # Humanize only lightly; preserve semantic tokens.
    return source_name


def heading_language(heading: str, text: str) -> str:
    h = heading.lower()
    if any(x in h for x in ['zh', '中文', '叙事', '敘事', '神谕', '神諭', '关键', '關鍵', '运作', '運作', '传说', '傳說', '隐秘', '隱秘', '问题', '問題', '答案', '原始']):
        return 'zh'
    if '(en)' in h or 'english' in h or re.search(r'\ben\b', h):
        return 'en'
    if re.search(r'[\u3400-\u9fff]', text) and not re.search(r'[A-Za-z]{15,}', text):
        return 'zh'
    return 'en' if re.search(r'[A-Za-z]', text) else 'und'


def classify_heading(heading: str) -> str:
    h = re.sub(r'[^a-z0-9\u3400-\u9fff ]+', ' ', heading.lower())
    if any(x in h for x in ['original tweet', 'original post', 'original context', 'original source', 'source statement', 'source material', '原始推文', '原始帖文', '原始背景']):
        return 'source_material'
    if any(x in h for x in ['literal explanation', '字面解释', '字面解釋']):
        return 'editorial_literal_explanation'
    if any(x in h for x in ['spiritual interpretation', 'symbolic meaning', 'interpretation', 'mirror reflection', 'reflection', '灵性解读', '靈性解讀', '象征含义', '象徵含義', '镜之映照', '鏡之映照']):
        return 'editorial_interpretation'
    if any(x in h for x in ['question', '问题', '問題', 'poetic query']):
        return 'question'
    if any(x in h for x in ['answer', '答案']):
        return 'community_answer'
    if any(x in h for x in ['operations', 'operational', 'mechanic', 'contract', '运作', '運作']):
        return 'operational_annotation'
    if any(x in h for x in ['key marks', 'oracle', 'oracles', 'symbol table', 'symbol key', 'symbols', 'timeline', 'metadata', 'sacred number', '关键标记', '關鍵標記', '神谕', '神諭', '符号', '符號']):
        return 'reference_annotation'
    if any(x in h for x in ['lore anchor', 'anchored lineage', '传说锚点', '傳說錨點']):
        return 'cross_reference'
    if any(x in h for x in ['narrative commentary', 'narrative  commentary', 'commentary', '评述', '評述', '评论', '評論']):
        return 'community_commentary'
    if any(x in h for x in ['narrative', 'teachings', 'lore', 'riddle', 'guidance', 'closing whisper', '叙事', '敘事', '教义', '教義']):
        return 'community_authored_lore'
    return 'unclassified_section'


def section_layer_summary(body: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in body.splitlines():
        m = re.match(r'^(#{1,6})\s+(.+?)\s*$', line)
        if not m:
            continue
        heading = m.group(2).strip()
        items.append({
            'level': len(m.group(1)),
            'heading': heading,
            'evidence_layer': classify_heading(heading),
            'language': heading_language(heading, heading),
        })
    return items


def status_flags(source_name: str, raw_date: str | None, body: str) -> list[str]:
    s = (source_name + '\n' + (raw_date or '') + '\n' + body[:2500]).lower()
    flags: list[str] = []
    if 'cancel' in s or 'cancelled' in s or 'cancellation' in s:
        flags.append('cancellation_or_ended_mechanism')
    if 'correction' in s or 'corrected' in s:
        flags.append('correction_record')
    if any(x in s for x in ['xx-xx', 'tbd', 'pending', 'enter the date', 'leave blank for now', 'placeholder']):
        flags.append('incomplete_metadata_or_draft_marker')
    if 'proposal' in s or 'proposed' in s:
        flags.append('may_describe_proposal')
    return flags


def extract_meta(meta: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in meta and meta[k] not in (None, ''):
            return clean_scalar(meta[k])
    return None


# Legacy source archive

def build_pack(source_zip: Path, legacy_json: Path, out_root: Path, dist_dir: Path, version: str = 'public-v1') -> dict[str, Any]:
    global SOURCE_ZIP, LEGACY_JSON, OUT_ROOT, VERSION, SCHEMA_NAME
    SOURCE_ZIP = source_zip.resolve()
    LEGACY_JSON = legacy_json.resolve()
    OUT_ROOT = out_root.resolve()
    VERSION = version
    SCHEMA_NAME = 'toadgod_lore_record_public_v1'

    if not SOURCE_ZIP.is_file():
        raise FileNotFoundError(f'Source ZIP not found: {SOURCE_ZIP}')
    if not LEGACY_JSON.is_file():
        raise FileNotFoundError(f'Legacy JSON not found: {LEGACY_JSON}')

    dist_dir = dist_dir.resolve()
    dist_dir.mkdir(parents=True, exist_ok=True)
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)
    (OUT_ROOT / 'gemini-gem').mkdir(parents=True)
    (OUT_ROOT / 'chatgpt-gpt').mkdir(parents=True)
    (OUT_ROOT / 'schema').mkdir(parents=True)
    (OUT_ROOT / 'reports').mkdir(parents=True)
    (OUT_ROOT / 'scripts').mkdir(parents=True)

    legacy_data = json.loads(LEGACY_JSON.read_text(encoding='utf-8'))
    legacy_t_numbers: set[int] = set()
    for row in legacy_data:
        m = re.match(r'TOBY_T(\d+)', str(row.get('id', '')), re.I)
        if m:
            legacy_t_numbers.add(int(m.group(1)))

    records: list[dict[str, Any]] = []
    used_ids: Counter[str] = Counter()

    def unique_record_id(candidate: str, suffix_hint: str = '') -> str:
        candidate = candidate.strip() or 'UNNAMED_RECORD'
        used_ids[candidate] += 1
        if used_ids[candidate] == 1:
            return candidate
        hint = re.sub(r'[^A-Za-z0-9_-]+', '_', suffix_hint).strip('_')[:80]
        alt = f'{candidate}__{hint or used_ids[candidate]}'
        while used_ids[alt]:
            used_ids[candidate] += 1
            alt = f'{candidate}__{hint or used_ids[candidate]}_{used_ids[candidate]}'
        used_ids[alt] = 1
        return alt

    for idx, row in enumerate(legacy_data, start=1):
        source_record_id = str(row.get('id') or f'LEGACY_{idx:04d}')
        title = str(row.get('title') or source_record_id)
        date_iso, date_raw, date_precision = extract_date({'date': row.get('date')}, source_record_id)
        rid = unique_record_id(source_record_id, f'{row.get("date", "")}_{title}')
        original = str(row.get('original') or '').strip()
        comment = str(row.get('comment') or '').strip()
        content_markdown = (
            f'# {title}\n\n'
            f'## SOURCE MATERIAL — legacy `original` field\n\n{original}\n\n'
            f'## COMMUNITY COMMENTARY — legacy `comment` field\n\n{comment}\n'
        )
        tags = [str(x).strip() for x in listify(row.get('tags')) if str(x).strip()]
        record = {
            'schema': SCHEMA_NAME,
            'record_id': rid,
            'source_record_id': source_record_id,
            'title': title,
            'date': date_iso,
            'date_raw': date_raw,
            'date_precision': date_precision,
            'series': filename_series(source_record_id),
            'document_kind': 'legacy_source_and_commentary',
            'languages': ['en'],
            'epoch': None,
            'chain': 'Base' if '@base' in (original + comment).lower() or 'base' in tags else None,
            'tags': tags,
            'symbols': [],
            'sacred_numbers': [],
            'status_flags': status_flags(source_record_id, date_raw, content_markdown),
            'source': {
                'collection': 'toadgod-lore.json',
                'source_file': LEGACY_JSON.name,
                'source_position': idx,
                'source_sha256': sha256_bytes(json.dumps(row, ensure_ascii=False, sort_keys=True).encode('utf-8')),
                'url': row.get('url') or None,
                'image_reference': row.get('img') or None,
            },
            'evidence_boundary': {
                'source_material_field': 'original',
                'community_commentary_field': 'comment',
                'independent_verification': 'not_implied',
            },
            'section_layers': [
                {'level': 2, 'heading': 'SOURCE MATERIAL', 'evidence_layer': 'source_material', 'language': 'en'},
                {'level': 2, 'heading': 'COMMUNITY COMMENTARY', 'evidence_layer': 'community_commentary', 'language': 'en'},
            ],
            'content_markdown': content_markdown,
            'content_sha256': sha256_bytes(content_markdown.encode('utf-8')),
        }
        records.append(record)

    # Markdown scroll corpus
    excluded: list[dict[str, Any]] = []
    seen_content_hash: dict[str, str] = {}
    frontmatter_stats = Counter()


    def exclusion_reason(path: str, source_name: str, series: str, content_hash: str) -> str | None:
        rel = path.split('/', 1)[1] if '/' in path else path
        lower_path = rel.lower()
        lower_name = source_name.lower()
        if '/product/' in '/' + lower_path or '/training/' in '/' + lower_path:
            return 'non_lore_product_or_training_file'
        # Public agent corpus is Toby/Toadgod lore. MIRROR_/VOID_ and generic aggregate packs stay outside.
        if not re.match(r'^TOBY_', source_name, re.I):
            return 'outside_toby_public_lore_prefix'
        if 'template' in lower_name or re.match(r'^toby_format', lower_name):
            return 'template_not_knowledge'
        if any(x in lower_name for x in ['mirrorinstruction', 'grandcodexinstruction', 'instructionseal']):
            return 'agent_or_builder_instruction_not_lore_knowledge'
        if any(x in lower_name for x in ['patchset', 'fullmega', '_full', 'lore_v1.1_full']):
            return 'aggregate_duplicate_pack'
        if 'index' in lower_name:
            return 'source_index_replaced_by_generated_record_index'
        # Four near-duplicate, incomplete cancellation drafts existed; retain the first structured update only.
        if re.match(r'^toby_l121[789]_rune3_patiencevaultcancelled', lower_name):
            return 'near_duplicate_cancellation_update'
        if content_hash in seen_content_hash:
            return f'exact_duplicate_of:{seen_content_hash[content_hash]}'
        # Foundation T-series is sourced from the legacy JSON with source URL + explicit original/comment split.
        m = re.match(r'^TOBY_T(\d+)', source_name, re.I)
        if m and int(m.group(1)) in legacy_t_numbers:
            return 'duplicate_foundation_t_series_represented_by_legacy_json'
        return None

    with zipfile.ZipFile(SOURCE_ZIP) as zf:
        md_infos = [i for i in zf.infolist() if not i.is_dir() and i.filename.lower().endswith('.md')]
        for info in md_infos:
            raw_bytes = zf.read(info)
            text = raw_bytes.decode('utf-8', errors='replace')
            content_hash = sha256_bytes(raw_bytes)
            source_name = normalized_source_name(info.filename)
            series = filename_series(source_name)
            reason = exclusion_reason(info.filename, source_name, series, content_hash)
            if reason:
                excluded.append({'source_file': info.filename, 'reason': reason, 'sha256': content_hash, 'bytes': info.file_size})
                continue
            seen_content_hash[content_hash] = info.filename
            meta, fm_raw, body, fm_success = extract_frontmatter(text)
            frontmatter_stats['parsed' if fm_success else ('fallback_or_missing' if fm_raw else 'missing')] += 1
            title = extract_title(meta, body, source_name)
            date_iso, date_raw, date_precision = extract_date(meta, source_name)
            languages = infer_languages(meta, source_name, body)
            source_record_id = str(extract_meta(meta, 'id', 'ID') or source_name)
            source_record_id = re.sub(r'\.md$', '', source_record_id, flags=re.I)
            # Prefer the source filename stem as the unique public citation ID if metadata is generic or duplicated.
            rid_candidate = source_record_id if source_record_id.upper().startswith('TOBY_') else source_name
            rid = unique_record_id(rid_candidate, source_name)
            tags = [str(x).strip() for x in listify(extract_meta(meta, 'tags', 'Tags')) if str(x).strip()]
            symbols = [str(x).strip() for x in listify(extract_meta(meta, 'symbols', 'Symbols')) if str(x).strip()]
            sacred = [clean_scalar(x) for x in listify(extract_meta(meta, 'sacred_numbers', 'Sacred Numbers', 'sacred number'))]
            record = {
                'schema': SCHEMA_NAME,
                'record_id': rid,
                'source_record_id': source_record_id,
                'title': title,
                'date': date_iso,
                'date_raw': date_raw,
                'date_precision': date_precision,
                'series': series,
                'document_kind': document_kind(series),
                'languages': languages,
                'epoch': extract_meta(meta, 'epoch', 'Epoch'),
                'chain': extract_meta(meta, 'chain', 'Chain'),
                'tags': tags,
                'symbols': symbols,
                'sacred_numbers': sacred,
                'status_flags': status_flags(source_name, date_raw, body),
                'source': {
                    'collection': 'lore-scrolls',
                    'source_file': info.filename,
                    'source_sha256': content_hash,
                    'zip_member_bytes': info.file_size,
                },
                'evidence_boundary': {
                    'document_may_mix_layers': True,
                    'section_classification_is_heading_based': True,
                    'source_statement_does_not_imply_independent_verification': True,
                },
                'frontmatter': clean_scalar(meta),
                'frontmatter_raw': fm_raw or None,
                'section_layers': section_layer_summary(body),
                'content_markdown': body,
                'content_sha256': sha256_bytes(body.encode('utf-8')),
            }
            records.append(record)

    # Assign high-level group and sort.
    def sort_key(r: dict[str, Any]):
        d = r.get('date') or '9999-99-99'
        return (d, str(r.get('record_id', '')).lower())

    foundation = [r for r in records if r['source']['collection'] == 'toadgod-lore.json' or r['series'] == 'T']
    lore = [r for r in records if r not in foundation and r['series'] == 'L']
    commentary = [r for r in records if r not in foundation and r['series'] == 'C']
    qa = [r for r in records if r not in foundation and r['series'] == 'QA']
    other = [r for r in records if r not in foundation and r['series'] not in {'L', 'C', 'QA'}]
    for group in (foundation, lore, commentary, qa, other):
        group.sort(key=sort_key)


    def record_size(r: dict[str, Any]) -> int:
        return len(json.dumps(r, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


    def split_half(group: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not group:
            return [], []
        total = sum(record_size(r) for r in group)
        target = total / 2
        acc = 0
        split = 1
        for i, r in enumerate(group):
            acc += record_size(r)
            if acc >= target:
                split = i + 1
                break
        return group[:split], group[split:]

    lore_a, lore_b = split_half(lore)
    comm_a, comm_b = split_half(commentary)
    qa_a, qa_b = split_half(qa)
    other_a, other_b = split_half(other)

    volumes: list[tuple[str, str, list[dict[str, Any]]]] = [
        ('01-foundation-source-records', 'Foundation source statements and legacy commentary, plus unmatched T-series source scrolls.', foundation),
        ('02-lore-scrolls-early', 'Earlier half of L-series lore scrolls, ordered by date and record ID.', lore_a),
        ('03-lore-scrolls-later', 'Later half of L-series lore scrolls, ordered by date and record ID.', lore_b),
        ('04-community-commentary-early', 'Earlier half of C-series community commentary records.', comm_a),
        ('05-community-commentary-later', 'Later half of C-series community commentary records.', comm_b),
        ('06-questions-and-answers-early', 'Earlier half of QA-series lore question-and-answer records.', qa_a),
        ('07-questions-and-answers-later', 'Later half of QA-series lore question-and-answer records.', qa_b),
        ('08-codex-reflections-early', 'Earlier half of remaining codex, technical, reflection, rune, fragment, and public builder-context records.', other_a),
        ('09-codex-reflections-later', 'Later half of remaining codex, technical, reflection, rune, fragment, and public builder-context records.', other_b),
    ]

    volume_reports = []
    record_index = []
    for vol_num, (slug, desc, vol_records) in enumerate(volumes, start=1):
        for r in vol_records:
            r['volume'] = slug
        gem_path = OUT_ROOT / 'gemini-gem' / f'{slug}.json'
        gpt_path = OUT_ROOT / 'chatgpt-gpt' / f'{slug}.jsonl'
        gem_payload = {
            'schema': 'toadgod_lore_volume_public_v1',
            'corpus': 'toadgod-lore-agent-pack-public-v1',
            'version': VERSION,
            'volume': slug,
            'description': desc,
            'record_count': len(vol_records),
            'records': vol_records,
        }
        gem_path.write_text(json.dumps(gem_payload, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
        with gpt_path.open('w', encoding='utf-8', newline='\n') as f:
            for r in vol_records:
                f.write(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n')
        gem_bytes = gem_path.stat().st_size
        gpt_bytes = gpt_path.stat().st_size
        volume_reports.append({
            'volume': slug,
            'description': desc,
            'record_count': len(vol_records),
            'gemini_file': gem_path.name,
            'gemini_bytes': gem_bytes,
            'gemini_approx_tokens_chars_div_4': round(len(gem_path.read_text(encoding='utf-8')) / 4),
            'gemini_sha256': sha256_file(gem_path),
            'chatgpt_file': gpt_path.name,
            'chatgpt_bytes': gpt_bytes,
            'chatgpt_approx_tokens_chars_div_4': round(len(gpt_path.read_text(encoding='utf-8')) / 4),
            'chatgpt_sha256': sha256_file(gpt_path),
        })
        for r in vol_records:
            record_index.append({
                'record_id': r['record_id'],
                'source_record_id': r.get('source_record_id'),
                'title': r.get('title'),
                'date': r.get('date'),
                'date_raw': r.get('date_raw'),
                'series': r.get('series'),
                'document_kind': r.get('document_kind'),
                'languages': r.get('languages'),
                'status_flags': r.get('status_flags'),
                'volume': slug,
                'source_file': r['source'].get('source_file'),
                'source_url': r['source'].get('url'),
                'content_sha256': r.get('content_sha256'),
            })

    # Manifest copied into both platform folders as the 10th upload file.
    series_counts = Counter(r['series'] for r in records)
    doc_counts = Counter(r['document_kind'] for r in records)
    lang_counts = Counter(lang for r in records for lang in r['languages'])
    status_counts = Counter(flag for r in records for flag in r['status_flags'])
    valid_dates = sorted(r['date'] for r in records if r.get('date'))
    manifest = {
        'schema': 'toadgod_lore_corpus_manifest_public_v1',
        'corpus': 'toadgod-lore-agent-pack-public-v1',
        'version': VERSION,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'Public, portable knowledge corpus for Toadgang-built Gemini Gems, ChatGPT GPTs, and other lore-guardian agents.',
        'platform_upload_design': {
            'files_per_platform': 10,
            'content_volumes': 9,
            'manifest_file': '10-corpus-manifest.json',
            'note': 'Upload all 10 files from only one platform folder. Put behavior rules in the Gem/GPT Instructions field, not in knowledge files.',
        },
        'source_archives': [
            {'file': SOURCE_ZIP.name, 'sha256': sha256_file(SOURCE_ZIP), 'markdown_member_count': 4799},
            {'file': LEGACY_JSON.name, 'sha256': sha256_file(LEGACY_JSON), 'legacy_record_count': len(legacy_data)},
        ],
        'record_count': len(records),
        'date_range_of_valid_iso_dates': {'min': valid_dates[0] if valid_dates else None, 'max': valid_dates[-1] if valid_dates else None},
        'counts_by_series': dict(sorted(series_counts.items())),
        'counts_by_document_kind': dict(sorted(doc_counts.items())),
        'counts_by_language': dict(sorted(lang_counts.items())),
        'counts_by_status_flag': dict(sorted(status_counts.items())),
        'evidence_layer_definitions': {
            'source_material': 'Quoted or reproduced source material. It establishes that the source statement appears in the archive; it does not by itself prove every claim is independently true.',
            'editorial_literal_explanation': 'Community-authored literal explanation of source material.',
            'editorial_interpretation': 'Spiritual, symbolic, or reflective interpretation.',
            'community_commentary': 'Community-authored commentary or annotation.',
            'community_authored_lore': 'Lore narrative created or compiled in the scroll corpus; do not silently treat it as a direct Toadgod statement.',
            'community_answer': 'Answer authored in a Q&A or guide record.',
            'operational_annotation': 'Mechanics, actions, contracts, or operational notes stated by the scroll; verify against source/onchain evidence when precision matters.',
            'reference_annotation': 'Key marks, symbols, oracles, metadata, or timeline annotations.',
            'cross_reference': 'Links between records; relationship does not itself prove a factual claim.',
            'unclassified_section': 'Section not safely classifiable from its heading alone.',
        },
        'public_scope_boundaries': [
            'Tobyworld is Toadgod’s project/world. ToadAid, Mirror, and Toadgang builders may preserve or reflect the lore but must not claim ownership, authorship, control, or official authority over Tobyworld.',
            'Do not expose or invent private credentials, internal operator data, unpublished secrets, or user-specific information.',
            'Do not provide price predictions or financial advice. Token-price movement and community excitement are not lore evidence.',
            'Preserve the difference between source statements, independently verifiable onchain facts, community records, and interpretations.',
            'When a later record explicitly corrects, cancels, or closes an earlier mechanism, present the earlier record as historical and the later status as the current archive position. If dates or authority are incomplete, say so.',
        ],
        'high_priority_update_records': [
            {
                'record_id': 'TOBY_L1216_Rune3_PatienceVaultCancelled_2026-XX-XX_EN',
                'topic': 'Rune3 Patience Vault',
                'guidance': 'The record explicitly says the proposed Patience Vault distribution was later cancelled. Its date metadata is incomplete; state both facts. Do not describe the vault as currently active.'
            },
            {
                'record_id': 'TOBY_QA003_SatobyBurnMisconceptionCorrection_EN',
                'topic': 'Burning 777 $TOBY for Taboshi1/Satoby eligibility',
                'guidance': 'Treat this as a correction record and do not advise that the historical burn window remains open.'
            },
            {
                'record_id': 'TOBY_QA1114_TotalSupplyCorrection_2025-10-29_EN',
                'topic': 'Supply claims',
                'guidance': 'Treat this as a correction record, while distinguishing its community-authored assertions from independently verified onchain evidence.'
            },
        ],
        'volumes': volume_reports,
        'excluded_markdown_file_count': len(excluded),
        'exclusion_policy_summary': Counter(x['reason'].split(':', 1)[0] for x in excluded),
        'frontmatter_parse_stats_for_included_markdown': dict(frontmatter_stats),
    }
    # Counter is not JSON serializable
    manifest['exclusion_policy_summary'] = dict(manifest['exclusion_policy_summary'])

    for folder in ('gemini-gem', 'chatgpt-gpt'):
        p = OUT_ROOT / folder / '10-corpus-manifest.json'
        p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # Schema
    schema = {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': 'https://toadaid.example/schemas/toadgod-lore-record-public-v1.schema.json',
        'title': 'Toadgod Lore Record Public v1',
        'type': 'object',
        'required': ['schema', 'record_id', 'title', 'series', 'document_kind', 'languages', 'source', 'content_markdown', 'content_sha256'],
        'properties': {
            'schema': {'const': SCHEMA_NAME},
            'record_id': {'type': 'string', 'minLength': 1},
            'source_record_id': {'type': ['string', 'null']},
            'title': {'type': 'string'},
            'date': {'type': ['string', 'null'], 'pattern': '^20\\d{2}-\\d{2}-\\d{2}$'},
            'date_raw': {'type': ['string', 'null']},
            'date_precision': {'type': 'string'},
            'series': {'type': 'string'},
            'document_kind': {'type': 'string'},
            'languages': {'type': 'array', 'items': {'type': 'string'}},
            'epoch': {},
            'chain': {},
            'tags': {'type': 'array'},
            'symbols': {'type': 'array'},
            'sacred_numbers': {'type': 'array'},
            'status_flags': {'type': 'array', 'items': {'type': 'string'}},
            'source': {'type': 'object'},
            'evidence_boundary': {'type': 'object'},
            'frontmatter': {'type': 'object'},
            'frontmatter_raw': {'type': ['string', 'null']},
            'section_layers': {'type': 'array'},
            'content_markdown': {'type': 'string'},
            'content_sha256': {'type': 'string', 'pattern': '^[a-f0-9]{64}$'},
            'volume': {'type': 'string'},
        },
        'additionalProperties': True,
    }
    (OUT_ROOT / 'schema' / 'toadgod-lore-record-public-v1.schema.json').write_text(json.dumps(schema, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # Record index and reports
    (OUT_ROOT / 'record-index.json').write_text(json.dumps({
        'schema': 'toadgod_lore_record_index_public_v1',
        'corpus': manifest['corpus'],
        'version': VERSION,
        'record_count': len(record_index),
        'records': record_index,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT_ROOT / 'reports' / 'excluded-files.json').write_text(json.dumps({
        'excluded_count': len(excluded),
        'files': excluded,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


    # Copy the platform-specific prompts maintained at the repository root.
    repo_root = Path(__file__).resolve().parents[1]
    for prompt_name in ('GEM_SYSTEM_PROMPT.md', 'GPT_INSTRUCTIONS_PROMPT.md'):
        source_prompt = repo_root / prompt_name
        if not source_prompt.is_file():
            raise FileNotFoundError(
                f'Platform prompt not found: {source_prompt}'
            )
        shutil.copy2(source_prompt, OUT_ROOT / prompt_name)

    readme = f'''# Toadgod Lore Agent Pack — Public v1

    A portable, provenance-aware public lore corpus for Toadgang builders creating Gemini Gems, ChatGPT GPTs, and other lore-guardian agents.

    ## Ready-to-upload folders

    - `gemini-gem/`: upload all 10 JSON files to the Gem’s Knowledge section.
    - `chatgpt-gpt/`: upload all 10 files to the GPT’s Knowledge section.
    - Paste `GEM_SYSTEM_PROMPT.md` into a Gemini Gem’s Instructions field.
    - Paste `GPT_INSTRUCTIONS_PROMPT.md` into a ChatGPT GPT’s Instructions field.

    The two platform folders contain the same {len(records):,} records in different serialization formats:

    - Gemini: JSON volume objects with record arrays.
    - ChatGPT: JSONL, one complete lore record per line.

    ## Provenance model

    Each record preserves:

    - record ID and source ID
    - source filename or source URL
    - source hash and content hash
    - date and raw date
    - series, language, tags, symbols, and status flags
    - heading-based evidence-layer map
    - exact Markdown content

    The `original` and `comment` fields from the legacy `toadgod-lore.json` archive are explicitly separated as source material and community commentary.

    ## Current-status rule

    Historical mechanics remain in the archive. Later explicit correction or cancellation records must be presented as later status updates. The Rune3 Patience Vault cancellation record is flagged in the manifest so an agent does not describe the proposed vault as currently active.

    ## Public boundary

    Tobyworld remains Toadgod’s project/world. ToadAid, Mirror, and Toadgang builders are preservation and reflection layers, not owners or official authorities. The pack is for lore study, not price predictions or financial advice.

    ## Repository files

    - `GEM_SYSTEM_PROMPT.md`: Gemini Gem instructions.
    - `GPT_INSTRUCTIONS_PROMPT.md`: compact ChatGPT GPT instructions.
    - `record-index.json`: compact index of all included records.
    - `schema/toadgod-lore-record-public-v1.schema.json`: record contract.
    - `reports/excluded-files.json`: deterministic exclusions and reasons.
    - `scripts/build_lore_pack.py`: reproducible builder.
    '''
    (OUT_ROOT / 'README.md').write_text(readme, encoding='utf-8')

    # Copy build script for repo reproducibility.
    shutil.copy2(Path(__file__), OUT_ROOT / 'scripts' / 'build_lore_pack.py')

    # Build report after all files exist.
    platform_checks = {}
    for folder in ('gemini-gem', 'chatgpt-gpt'):
        files = sorted(p.name for p in (OUT_ROOT / folder).iterdir() if p.is_file())
        platform_checks[folder] = {'file_count': len(files), 'files': files}

    build_report = {
        'corpus': manifest['corpus'],
        'record_count': len(records),
        'legacy_records': len(legacy_data),
        'included_markdown_records': len(records) - len(legacy_data),
        'excluded_markdown_files': len(excluded),
        'platform_checks': platform_checks,
        'unique_record_ids': len({r['record_id'] for r in records}) == len(records),
        'volumes': volume_reports,
        'source_zip_sha256': sha256_file(SOURCE_ZIP),
        'legacy_json_sha256': sha256_file(LEGACY_JSON),
    }
    (OUT_ROOT / 'reports' / 'build-report.json').write_text(json.dumps(build_report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # Validation
    assert len(records) == len({r['record_id'] for r in records}), 'record IDs must be unique'
    assert platform_checks['gemini-gem']['file_count'] == 10, platform_checks['gemini-gem']
    assert platform_checks['chatgpt-gpt']['file_count'] == 10, platform_checks['chatgpt-gpt']
    # Parse all generated files.
    for p in (OUT_ROOT / 'gemini-gem').glob('*.json'):
        json.loads(p.read_text(encoding='utf-8'))
    for p in (OUT_ROOT / 'chatgpt-gpt').glob('*.json'):
        json.loads(p.read_text(encoding='utf-8'))
    line_count = 0
    for p in (OUT_ROOT / 'chatgpt-gpt').glob('*.jsonl'):
        with p.open(encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    obj = json.loads(line)
                    assert obj['schema'] == SCHEMA_NAME
                    line_count += 1
    assert line_count == len(records), (line_count, len(records))
    # Check exact restricted token, not substrings such as coMPASS.
    for r in records:
        assert '$AID' not in r['content_markdown']
        assert not re.search(r'(?<![A-Za-z])MPASS(?![A-Za-z])', r['content_markdown'], re.I)
    # Conservative file size/token checks.
    for vr in volume_reports:
        assert vr['gemini_bytes'] < 100 * 1024 * 1024
        assert vr['chatgpt_bytes'] < 512 * 1024 * 1024
        assert vr['chatgpt_approx_tokens_chars_div_4'] < 2_000_000

    # Zip platform folders and full repo pack.
    def zip_dir(src: Path, dest: Path, include_root: bool = False):
        if dest.exists():
            dest.unlink()
        with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for p in sorted(src.rglob('*')):
                if p.is_file():
                    arc = p.relative_to(src.parent if include_root else src)
                    z.write(p, arcname=str(arc))

    GEM_ZIP = dist_dir / 'toadgod-lore-gemini-gem-public-v1.zip'
    GPT_ZIP = dist_dir / 'toadgod-lore-chatgpt-gpt-public-v1.zip'
    FULL_ZIP = dist_dir / 'toadgod-lore-agent-pack-public-v1.zip'
    zip_dir(OUT_ROOT / 'gemini-gem', GEM_ZIP)
    zip_dir(OUT_ROOT / 'chatgpt-gpt', GPT_ZIP)
    zip_dir(OUT_ROOT, FULL_ZIP, include_root=True)

    summary = {
        'record_count': len(records),
        'legacy_record_count': len(legacy_data),
        'included_markdown_record_count': len(records) - len(legacy_data),
        'excluded_markdown_file_count': len(excluded),
        'gemini_zip': {'path': str(GEM_ZIP), 'bytes': GEM_ZIP.stat().st_size, 'sha256': sha256_file(GEM_ZIP)},
        'chatgpt_zip': {'path': str(GPT_ZIP), 'bytes': GPT_ZIP.stat().st_size, 'sha256': sha256_file(GPT_ZIP)},
        'full_pack_zip': {'path': str(FULL_ZIP), 'bytes': FULL_ZIP.stat().st_size, 'sha256': sha256_file(FULL_ZIP)},
        'largest_gemini_volume_tokens_approx': max(v['gemini_approx_tokens_chars_div_4'] for v in volume_reports),
        'largest_chatgpt_volume_tokens_approx': max(v['chatgpt_approx_tokens_chars_div_4'] for v in volume_reports),
        'platform_file_counts': platform_checks,
        'volume_counts': {v['volume']: v['record_count'] for v in volume_reports},
    }
    (dist_dir / 'toadgod-lore-agent-pack-public-v1-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build the public Toad Lore Guardian corpus pack.')
    parser.add_argument('--source-zip', type=Path, required=True, help='ZIP containing Markdown lore scrolls.')
    parser.add_argument('--legacy-json', type=Path, required=True, help='Legacy annotated toadgod-lore.json file.')
    parser.add_argument('--out-root', type=Path, default=Path('build/toadgod-lore-agent-pack-public-v1'), help='Generated unpacked pack directory.')
    parser.add_argument('--dist-dir', type=Path, default=Path('dist'), help='Directory for ZIP bundles and the build summary.')
    parser.add_argument('--version', default='public-v1', help='Corpus version label.')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_pack(args.source_zip, args.legacy_json, args.out_root, args.dist_dir, args.version)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
