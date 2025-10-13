
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import json
import csv
import re
from io import StringIO, BytesIO

try:
    import openpyxl
except Exception:
    openpyxl = None

# -----------------------------
# Product Template helpers (autocomplete & search more)
# -----------------------------

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Autocomplete: search across name + ptp_part_number + ptp_value_unit_combined (if exist)."""
        args = args or []
        name = name or ''
        fields_m = self.env['ir.model.fields'].sudo()
        fields_to_use = ['name']
        if fields_m.search([('model','=','product.template'), ('name','=','ptp_part_number')], limit=1):
            fields_to_use.append('ptp_part_number')
        if fields_m.search([('model','=','product.template'), ('name','=','ptp_value_unit_combined')], limit=1):
            fields_to_use.append('ptp_value_unit_combined')

        dom = []
        if len(fields_to_use) > 1:
            dom = ['|'] * (len(fields_to_use) - 1)
        dom += [(f, operator, name) for f in fields_to_use]

        recs = self.search(dom + (args or []), limit=limit)
        return [(r.id, r.with_context(bom_import_show_labels=True).display_name) for r in recs]

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        name = name or ''
        fields_m = self.env['ir.model.fields'].sudo()
        extras = []
        if fields_m.search([('model','=','product.template'), ('name','=','ptp_part_number')], limit=1):
            extras.append('ptp_part_number')
        if fields_m.search([('model','=','product.template'), ('name','=','ptp_value_unit_combined')], limit=1):
            extras.append('ptp_value_unit_combined')
        search_fields = ['name'] + extras

        dom = []
        if len(search_fields) > 1:
            dom = ['|'] * (len(search_fields) - 1)
        dom += [(f, operator, name) for f in search_fields]

        recs = self.search(dom + (args or []), limit=limit, access_rights_uid=name_get_uid)
        return [(r.id, r.with_context(bom_import_show_labels=True).display_name) for r in recs]

    @api.depends_context('bom_import_show_labels')
    def _compute_display_name(self):
        super()._compute_display_name()
        if not self.env.context.get('bom_import_show_labels'):
            return
        for rec in self:
            extra = []
            pn = getattr(rec, 'ptp_part_number', '') or ''
            if pn and pn.lower() not in (rec.display_name or '').lower():
                extra.append(pn)
            vuc = getattr(rec, 'ptp_value_unit_combined', '') or ''
            if vuc and vuc.lower() not in (rec.display_name or '').lower():
                extra.append(vuc)
            if extra:
                rec.display_name = f"{rec.display_name} — {' | '.join(extra)}"

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if not res.get('arch'):
            return res
        try:
            from lxml import etree
            arch = etree.fromstring(res['arch'])
            fields_m = self.env['ir.model.fields'].sudo()
            has_pn = bool(fields_m.search([('model','=','product.template'), ('name','=','ptp_part_number')], limit=1))
            has_vuc = bool(fields_m.search([('model','=','product.template'), ('name','=','ptp_value_unit_combined')], limit=1))

            if view_type in ('list','tree'):
                lsts = arch.xpath("//list")
                if lsts:
                    lst = lsts[0]
                    anchor = (lst.xpath(".//field[@name='display_name']") or lst.xpath(".//field[@name='name']"))
                    if has_pn:
                        node_pn = etree.Element('field', name='ptp_part_number', string='Part Number')
                        (anchor[0].addnext(node_pn) if anchor else lst.insert(0, node_pn))
                    if has_vuc:
                        node_vuc = etree.Element('field', name='ptp_value_unit_combined', string='PTP Value/Unit Combined')
                        (anchor[0].addnext(node_vuc) if anchor else lst.insert(0, node_vuc))
                    res['arch'] = etree.tostring(arch, encoding='unicode')

            elif view_type == 'search':
                if has_pn or has_vuc:
                    if has_pn:
                        arch.append(etree.Element('field', name='ptp_part_number', string='Part Number'))
                    if has_vuc:
                        arch.append(etree.Element('field', name='ptp_value_unit_combined', string='PTP Value/Unit Combined'))
                    res['arch'] = etree.tostring(arch, encoding='unicode')
        except Exception:
            return res
        return res

# -----------------------------
# Import session & lines
# -----------------------------

class MrpBomImport(models.Model):
    _name = 'mrp.bom.import'
    _description = 'BOM Import Session'
    _order = 'id desc'

    name = fields.Char(default=lambda self: self.env['ir.sequence'].next_by_code('mrp.bom.import') or _('New'), readonly=True)
    state = fields.Selection([('draft','Draft'),('parsed','Parsed'),('done','Done')], default='draft')

    # Source
    file_type = fields.Selection([('csv','CSV'),('xlsx','XLSX'),('json','JSON')], default='csv', required=True)
    delimiter = fields.Char(string='CSV Delimiter', default=',')
    file_data = fields.Binary(string='File')
    filename = fields.Char()


    # ---- Source alternatives ----
    source_mode = fields.Selection([('upload','Upload'), ('document','Document')], default='upload', required=True)
    document_id = fields.Many2one('documents.document', string='Document')
    attachment_id = fields.Many2one('ir.attachment', string='Attachment')

    def _detect_type_from_filename(self, fname):
        fname = (fname or '').lower()
        if fname.endswith('.json'):
            return 'json'
        if fname.endswith('.xlsx') or fname.endswith('.xlsm'):
            return 'xlsx'
        if fname.endswith('.csv') or fname.endswith('.txt'):
            return 'csv'
        return self.file_type or 'csv'

    def action_load_from_document(self):
        for imp in self:
            att = imp.attachment_id
            if not att and imp.document_id:
                att = imp.document_id.attachment_id
            if not att:
                raise ValueError(_("No document/attachment selected."))
            if not att.datas:
                raise ValueError(_("Selected attachment has no data."))
            imp.filename = att.name
            imp.file_type = imp._detect_type_from_filename(att.name)
            imp.file_data = att.datas
        return True
    default_vendor_id = fields.Many2one(
        'res.partner',
        string='Default Vendor',
        domain="[('supplier_rank', '>', 0)]",
        help='Vendor to set on newly created products.'
    )
    default_vendor_delay = fields.Integer(
        string='Default Vendor Lead Time (days)',
        default=0,
        help='Supplier lead time in days to apply on created products.'
    )
    # Target
    bom_target_mode = fields.Selection([('new','Create New BOM'),('update','Update Existing BOM')], default='new')
    product_tmpl_id = fields.Many2one('product.template', string='BOM for Product')
    existing_bom_id = fields.Many2one('mrp.bom', string='Update BOM')
    product_uom_id = fields.Many2one('uom.uom', string='Default UoM', default=lambda self: self.env.ref('uom.product_uom_unit'))

    # Matching selector
    match_field_key = fields.Selection([
        ('ptp_part_number','Part Number (ptp_part_number)'),
        ('default_code','Internal Reference (default_code)'),
        ('name','Name'),
        ('barcode','Barcode'),
    ], string='Primary Match Field', default='ptp_part_number', required=True)

    line_ids = fields.One2many('mrp.bom.import.line', 'import_id', string='Lines')
    note = fields.Text()

    # ---- Header normalization & mapping ----
    def _normalize_key(self, s):
        if not s:
            return ''
        s = str(s)
        try:
            import unicodedata
            s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
        except Exception:
            pass
        s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).strip().lower()
        s = re.sub(r'\s+', ' ', s)
        return s

    def _get_header_map(self, sample_row: dict):
        keys = {}
        for k in (sample_row or {}).keys():
            nk = self._normalize_key(k)
            if nk and nk not in keys:
                keys[nk] = k

        def pick(*names):
            for n in names:
                if n in keys:
                    return keys[n]
            return False

        return {
            'footprint': pick(
                'footprint','package','pkg','land pattern','pattern','case','size','housing','package type','pkg type'
            ),
            'part_number': pick(
                'mpn', 'mfr part', 'mfr part number', 'manufacturer part',
                'manufacturer part number', 'manf part', 'manuf part',
                'part number', 'part no', 'part', 'part #', 'pn',
                'item number', 'item no', 'item', 'sku',
                'internal reference', 'default code', 'code', 'product code',
                'product id', 'catalog number', 'cat no'
            ),
            'description': pick(
                'description', 'desc', 'designation', 'item description',
                'product description', 'name', 'item name',
                'long description', 'title'
            ),
            'quantity': pick(
                'qty', 'quantity', 'amount', 'q',
                'qty required', 'required qty', 'qty per', 'bom qty',
                'qty bom', 'qty bom per', 'quantity per', 'qty pcs'
            ),
            'uom': pick(
                'uom', 'unit of measure', 'unit', 'units',
                'uom name', 'unit name', 'measure'
            ),
            'designator': pick(
                'designator', 'designators', 'reference designator',
                'refdes', 'ref des', 'ref', 'bom ref', 'refdes bom ref'
            ),
            'time': pick(
                'ptp bom time', 'time', 'time s', 'processing time',
                'cycle time', 'operation time', 'op time',
                'assembly time', 'elapsed time', 'duration', 'lead time'
            ),
        }

    def _coerce_float(self, v):
        if v is None or v == '':
            return 0.0
        s = str(v).strip()
        try:
            return float(s.replace(',', '.'))
        except Exception:
            try:
                return float(s)
            except Exception:
                return 0.0

    # ---- Parse file (CSV/XLSX) ----
    def action_parse_file(self):
        # 4) Ensure filename is retained on parse (nothing to do if already set by the binary field)
        for imp in self:
            if not imp.file_data:
                raise ValueError(_("Please upload a file."))
            data = base64.b64decode(imp.file_data or b'')
            lines = []
            seq = 10

            if imp.file_type == 'csv':
                content = data.decode('utf-8', errors='ignore')
                reader = csv.DictReader(StringIO(content), delimiter=(imp.delimiter or ',')[:1])
                header_map = None
                for row in reader:
                    if header_map is None:
                        header_map = imp._get_header_map(row)

                    def gv(key):
                        src = header_map.get(key)
                        return row.get(src) if src else ''

                    rp = gv('part_number')
                    rd = gv('description')
                    rq = gv('quantity')
                    uom = gv('uom')
                    fp  = gv('footprint')
                    des = gv('designator')
                    tm  = gv('time')

                    vals = {
                        'sequence': seq,
                        'raw_part_number': rp or '',
                        'raw_description': rd or '',
                        'raw_quantity': imp._coerce_float(rq),
                        'raw_uom_name': uom or '',
                        'raw_footprint': fp or '',
                        'raw_bom_designator': des or '',
                        'raw_bom_Time': imp._coerce_float(tm),
                        'raw_data_json': json.dumps(row, ensure_ascii=False),
                    }
            elif imp.file_type == 'json':
                content = data.decode('utf-8', errors='ignore')
                try:
                    obj = json.loads(content)
                except Exception as e:
                    raise ValueError(_("Invalid JSON: %s") % e)

                rows = None
                if isinstance(obj, list):
                    rows = obj
                elif isinstance(obj, dict):
                    if isinstance(obj.get('rows'), list):
                        rows = obj['rows']
                    elif isinstance(obj.get('data'), list):
                        rows = obj['data']
                    elif isinstance(obj.get('sheets'), list) and obj['sheets']:
                        first = obj['sheets'][0]
                        rows = first.get('rows') or first.get('data') or []

                # Support Odoo Spreadsheet grid: sheet['cells'] = {'A1': {'content': '...'}, ...}
                if not rows and isinstance(obj, dict) and isinstance(obj.get('sheets'), list) and obj['sheets']:
                    first = obj['sheets'][0]
                    if isinstance(first.get('cells'), dict) and first.get('cells'):
                        cells = first['cells']  # keys like 'A1', 'B2', values dicts with 'content'
                        def col_to_idx(col):
                            # 'A'->1, 'Z'->26, 'AA'->27
                            col = col.upper()
                            val = 0
                            for ch in col:
                                if not ('A' <= ch <= 'Z'):
                                    return 0
                                val = val * 26 + (ord(ch) - 64)
                            return val
                        # Build sparse grid map: (row, col_idx) -> content
                        grid = {}
                        used_rows = set()
                        used_cols = set()
                        for a1, meta in cells.items():
                            # split letters and numbers
                            m = re.match(r'^([A-Za-z]+)(\d+)$', a1)
                            if not m: 
                                continue
                            c_letters, r_str = m.group(1), m.group(2)
                            r = int(r_str)
                            c = col_to_idx(c_letters)
                            val = meta.get('content') if isinstance(meta, dict) else meta
                            # normalize value (strip whitespace)
                            if val is None:
                                val = ''
                            if isinstance(val, str):
                                val = val.strip()
                            grid[(r, c)] = val
                            used_rows.add(r); used_cols.add(c)
                        if used_rows and used_cols:
                            # header row: pick the smallest row index with at least one non-empty value
                            header_row = min(used_rows)
                            header_cols = sorted([c for c in used_cols if grid.get((header_row, c), '') not in (None, '')])
                            header_keys = [str(grid.get((header_row, c), '')).strip() for c in header_cols]
                            # Build row dicts for subsequent rows until we hit long empty streaks
                            # We'll iterate through sorted rows greater than header_row
                            data_rows = sorted([r for r in used_rows if r > header_row])
                            built = []
                            for r in data_rows:
                                row_dict = {}
                                empty_count = 0
                                for i, c in enumerate(header_cols):
                                    key = header_keys[i] if i < len(header_keys) else f'col{c}'
                                    val = grid.get((r, c), '')
                                    if val in (None, ''):
                                        empty_count += 1
                                    row_dict[key] = val
                                # consider row if it has at least one non-empty among header columns
                                if empty_count < len(header_cols):
                                    built.append(row_dict)
                            rows = built


                    else:
                        for k, v in obj.items():
                            if isinstance(v, list) and v and isinstance(v[0], (dict, list)):
                                rows = v
                                break
                if not rows:
                    rows = []

                def to_values(r):
                    if isinstance(r, dict) and isinstance(r.get('cells'), list):
                        return [ (c.get('v') if isinstance(c, dict) else c) for c in r['cells'] ]
                    return r

                rows = [to_values(r) for r in rows]

                

                # Special case: JSON bundle of OOXML parts (keys like "xl/worksheets/sheet1.xml").
                if not rows and isinstance(obj, dict) and any(k.startswith('xl/') for k in obj.keys()):
                    try:
                        import xml.etree.ElementTree as ET
                        ns_ss = {}  # no namespaces in sharedStrings needed
                        # 1) shared strings
                        shared = []
                        sst_xml = obj.get('xl/sharedStrings.xml') or obj.get('xl\\sharedStrings.xml')
                        if isinstance(sst_xml, str):
                            try:
                                root = ET.fromstring(sst_xml)
                                # both <si><t> and rich text <si><r><t>
                                for si in root.findall('.//{*}si'):
                                    # concatenate all t under si
                                    txt = ''.join((t.text or '') for t in si.findall('.//{*}t'))
                                    shared.append(txt)
                            except Exception:
                                shared = []
                        # 2) pick first worksheet
                        ws_key = None
                        for k in obj.keys():
                            if re.match(r'^xl/worksheets/sheet\d+\.xml$', k.replace('\\','/')):
                                ws_key = k
                                break
                        if not ws_key:
                            # try generic worksheet path
                            for k in obj.keys():
                                if 'worksheets' in k and k.endswith('.xml'):
                                    ws_key = k
                                    break
                        rows = []
                        if ws_key and isinstance(obj.get(ws_key), str):
                            ws_root = ET.fromstring(obj[ws_key])
                            # Build cell grid: map (row_idx, col_idx) -> value
                            def col_to_idx(col):
                                col = col.upper()
                                val = 0
                                for ch in col:
                                    if not ('A' <= ch <= 'Z'):
                                        return 0
                                    val = val * 26 + (ord(ch) - 64)
                                return val
                            grid = {}
                            used_rows, used_cols = set(), set()
                            for c in ws_root.findall('.//{*}c'):
                                r = c.attrib.get('r')  # e.g., A1
                                if not r:
                                    continue
                                mrc = re.match(r'^([A-Za-z]+)(\d+)$', r)
                                if not mrc:
                                    continue
                                col_letters, row_str = mrc.group(1), mrc.group(2)
                                row_idx = int(row_str)
                                col_idx = col_to_idx(col_letters)
                                ctype = c.attrib.get('t')  # 's' for shared string, 'inlineStr' etc.
                                v_el = c.find('{*}v')
                                is_el = c.find('{*}is')
                                val = ''
                                if ctype == 's' and v_el is not None and v_el.text is not None:
                                    try:
                                        si = int(v_el.text.strip())
                                        val = shared[si] if 0 <= si < len(shared) else ''
                                    except Exception:
                                        val = v_el.text.strip()
                                elif is_el is not None:
                                    # inline string
                                    val = ''.join((t.text or '') for t in is_el.findall('.//{*}t'))
                                elif v_el is not None and v_el.text is not None:
                                    val = v_el.text.strip()
                                # normalize
                                if val is None:
                                    val = ''
                                if isinstance(val, str):
                                    val = val.strip()
                                grid[(row_idx, col_idx)] = val
                                used_rows.add(row_idx); used_cols.add(col_idx)
                            if used_rows and used_cols:
                                header_row = min(used_rows)
                                header_cols = sorted([c for c in used_cols if (grid.get((header_row, c)) or '') != ''])
                                header_keys = [str(grid.get((header_row, c)) or '').strip() for c in header_cols]
                                # build row dicts for subsequent rows
                                data_rows = sorted([r for r in used_rows if r > header_row])
                                built = []
                                for r in data_rows:
                                    row_dict = {}
                                    empty = 0
                                    for i, c in enumerate(header_cols):
                                        key = header_keys[i] if i < len(header_keys) and header_keys[i] else f'col{c}'
                                        vv = grid.get((r, c), '')
                                        if vv in (None, ''):
                                            empty += 1
                                        row_dict[key] = vv
                                    if empty < len(header_cols):
                                        built.append(row_dict)
                                rows = built
                    except Exception:
                        # fallback: leave rows empty
                        rows = rows
                header_map = None
                header_keys = None
                for raw in rows:
                    if isinstance(raw, (list, tuple)):
                        if header_keys is None:
                            header_keys = [str(h) for h in raw]
                            continue
                        else:
                            row = {header_keys[i]: (raw[i] if i < len(raw) else None) for i in range(len(header_keys))}
                    elif isinstance(raw, dict):
                        row = raw
                    else:
                        continue

                    if header_map is None:
                        header_map = imp._get_header_map(row)

                    def gv(key):
                        src = header_map.get(key)
                        return row.get(src) if src else ''

                    rp = gv('part_number')
                    rd = gv('description')
                    rq = gv('quantity')
                    uom = gv('uom')
                    fp  = gv('footprint')
                    des = gv('designator')
                    tm  = gv('time')

                    vals = {
                        'sequence': seq,
                        'raw_part_number': rp or '',
                        'raw_description': rd or '',
                        'raw_quantity': imp._coerce_float(rq),
                        'raw_uom_name': uom or '',
                        'raw_footprint': fp or '',
                        'raw_bom_designator': des or '',
                        'raw_bom_Time': imp._coerce_float(tm),
                        'raw_data_json': json.dumps({k: ('' if v is None else v) for k, v in row.items()}, ensure_ascii=False),
                    }
                    lines.append((0, 0, vals))
                    seq += 10
    


            elif imp.file_type == 'xlsx':
                if not openpyxl:
                    raise ValueError(_("openpyxl is required to parse XLSX files."))
                wb = openpyxl.load_workbook(filename=BytesIO(data), data_only=True, read_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(values_only=True))
                if not rows:
                    imp.line_ids = [(5, 0, 0)]
                    imp.state = 'parsed'
                    continue
                headers = [str(h).strip() if h is not None else '' for h in rows[0]]

                sample_row = {headers[i]: (rows[1][i] if len(rows) > 1 and i < len(rows[1]) else None) for i in range(len(headers))}
                header_map = imp._get_header_map(sample_row)

                def row_to_dict(r):
                    return {headers[i]: (r[i] if i < len(r) else None) for i in range(len(headers))}

                for r in rows[1:]:
                    raw = row_to_dict(r)

                    def gv(key):
                        src = header_map.get(key)
                        val = raw.get(src) if src else ''
                        return '' if val is None else val

                    rp = gv('part_number')
                    rd = gv('description')
                    rq = gv('quantity')
                    uom = gv('uom')
                    fp  = gv('footprint')
                    des = gv('designator')
                    tm  = gv('time')

                    vals = {
                        'sequence': seq,
                        'raw_part_number': rp or '',
                        'raw_description': rd or '',
                        'raw_quantity': imp._coerce_float(rq),
                        'raw_uom_name': uom or '',
                        'raw_footprint': fp or '',
                        'raw_bom_designator': des or '',
                        'raw_bom_Time': imp._coerce_float(tm),
                        'raw_data_json': json.dumps({k: ('' if v is None else v) for k, v in raw.items()}, ensure_ascii=False),
                    }
                    lines.append((0, 0, vals))
                    seq += 10
            else:
                raise ValueError(_("Unsupported file type."))

            imp.line_ids = [(5, 0, 0)] + lines
            imp.state = 'parsed'
        return True

    def action_reset_to_draft(self):
        """Reset whole import back to draft.
        - Import: state -> 'draft'
        """
        for imp in self:
            # reset state importu
            if 'state' in imp._fields:
                imp.state = 'draft'

    # ---- Auto match using selected fields ----
    def action_auto_match(self):
        PT = self.env['product.template'].sudo()
        PP = self.env['product.product'].sudo()
        for imp in self:
            fields_to_try = []
            key = imp.match_field_key or 'ptp_part_number'
            if key:
                fields_to_try.append(key)
            for line in imp.line_ids:
                if line.product_tmpl_id_ui:
                    continue
                matched = False

                for fkey in fields_to_try:
                    raw_val = line._raw_value_for_field(fkey)
                    val = '' if raw_val is None else str(raw_val).strip()
                    line._log_step('auto_match', _("Trying %s → «%s»") % (fkey, val))

                    if not val:
                        continue

                    if fkey in ('ptp_part_number', 'name', 'barcode'):
                        cands = PT.search([(fkey, 'ilike', val)], limit=50)
                        exact = cands.filtered(lambda t: str(t[fkey] or '').strip().casefold() == val.casefold())
                        if len(exact) == 1:
                            line.product_tmpl_id_ui = exact.id
                            line.status = 'matched'
                            line.resolution_done = True
                            line._log_step('auto_match', _("Matched EXACT by %s = %s") % (fkey, val))
                            matched = True
                            break
                        if not matched and len(cands) == 1:
                            line.product_tmpl_id_ui = cands.id
                            line.status = 'matched'
                            line.resolution_done = True
                            line._log_step('auto_match', _("Matched (unique ILIKE) by %s ~ %s") % (fkey, val))
                            matched = True
                            break
                        if fkey == 'barcode' and not matched:
                            pv = PP.search([('barcode', 'ilike', val)], limit=50)
                            pv_exact = pv.filtered(lambda p: str(p.barcode or '').strip().casefold() == val.casefold())
                            pts = (pv_exact or pv).mapped('product_tmpl_id')
                            if len(pts) == 1:
                                line.product_tmpl_id_ui = pts.id
                                line.status = 'matched'
                                line.resolution_done = True
                                line._log_step('auto_match', _("Matched by variant.%s → template (%s)") % (fkey, val))
                                matched = True
                                break

                    
                # Vendor-based matching (product.supplierinfo)
                if not matched and val:
                    PSI = self.env['product.supplierinfo']
                    si_exact = PSI.search(['|', ('product_code','=',val), ('product_name','=',val)], limit=50)
                    if len(si_exact) == 1 and si_exact.product_tmpl_id:
                        line.product_tmpl_id_ui = si_exact.product_tmpl_id.id
                        line.product_id = si_exact.product_tmpl_id.product_variant_id.id
                        line.status = 'matched'
                        line.resolution_done = True
                        line._log_step('auto_match', _("Matched by vendor %s = %s") % (fkey, val))
                        matched = True
                if not matched and val:
                    si_cands = PSI.search(['|', ('product_code','ilike',val), ('product_name','ilike',val)], limit=50)
                    if len(si_cands) == 1 and si_cands.product_tmpl_id:
                        line.product_tmpl_id_ui = si_cands.product_tmpl_id.id
                        line.product_id = si_cands.product_tmpl_id.product_variant_id.id
                        line.status = 'matched'
                        line.resolution_done = True
                        line._log_step('auto_match', _("Matched (vendor ILIKE) by %s ~ %s") % (fkey, val))
                        matched = True
                    elif fkey == 'default_code':
                        pv = PP.search([('default_code', 'ilike', val)], limit=50)
                        pv_exact = pv.filtered(lambda p: str(p.default_code or '').strip().casefold() == val.casefold())
                        pts = (pv_exact or pv).mapped('product_tmpl_id')
                        if len(pts) == 1:
                            line.product_tmpl_id_ui = pts.id
                            line.status = 'matched'
                            line.resolution_done = True
                            line._log_step('auto_match', _("Matched by default_code → template (%s)") % (val,))
                            matched = True
                            break
                if not matched:
                    line._log_step('auto_match', _("No match for: %s") % (', '.join(fields_to_try)))
        return True

    # ---- Finalize ----
    def action_finalize(self):
        Uom = self.env['uom.uom']
        unit_uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False) or Uom.search([('category_id.measure_type','=','unit')], limit=1)
        for imp in self:
            # 1) Check all lines are resolved and none is in 'new'
            unresolved = imp.line_ids.filtered(lambda l: not l.resolution_done or l.status == 'new')
            if unresolved:
                raise UserError(_("Cannot finalize. All lines must be resolved and none may have status 'New'. Unresolved lines: %s") % (len(unresolved),))

            # Create or pick target BOM
            if imp.bom_target_mode == 'new':
                if not imp.product_tmpl_id:
                    raise ValueError(_("Please select a target product for the new BOM."))
                bom = self.env['mrp.bom'].create({
                    'product_tmpl_id': imp.product_tmpl_id.id,
                    # 3) Default UOM always pcs (Units)
                    'product_uom_id': (unit_uom.id if unit_uom else imp.product_tmpl_id.uom_id.id),
                    'type': 'normal',
                })
            else:
                if not imp.existing_bom_id:
                    raise ValueError(_("Please choose an existing BOM to update."))
                bom = imp.existing_bom_id
                # also enforce BOM UoM to Units when finalizing update
                if unit_uom and bom.product_uom_id != unit_uom:
                    bom.product_uom_id = unit_uom.id

            # 2) Only import/update for lines in status matched or manual
            for l in imp.line_ids.filtered(lambda ln: ln.status in ('matched','manual')):
                product = l.product_tmpl_id_ui.product_variant_id if l.product_tmpl_id_ui else False
                if not product:
                    continue
                self.env['mrp.bom.line'].create({
                    'bom_id': bom.id,
                    'product_id': product.id,
                    'product_qty': l.raw_quantity or 0.0,
                    'product_uom_id': (product.uom_id.id),
                    'ptp_designator': (l.raw_bom_designator or False),
                })

            # 5) After import/update, write filename into BOM code
            if imp.filename and bom:
                bom.code = imp.filename

            imp.state = 'done'
        return True


class MrpBomImportLine(models.Model):
    _name = 'mrp.bom.import.line'
    _description = 'BOM Import Line'
    _order = 'sequence,id'

    import_id = fields.Many2one('mrp.bom.import', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    status = fields.Selection([('new','New'),('matched','Matched'),('manual','Manual'),('skipped','Skipped')], default='new')

    raw_part_number = fields.Char()
    raw_description = fields.Char()
    raw_quantity = fields.Float(default=1.0)
    raw_uom_name = fields.Char()
    raw_footprint = fields.Char(string='Raw Footprint')

    product_tmpl_id_ui = fields.Many2one('product.template', string='Matched Template')
    product_id = fields.Many2one('product.product', string='Variant')

    raw_bom_designator = fields.Text(string='Designator')
    raw_bom_Time = fields.Float(string='Time')

    create_from_template_id = fields.Many2one('product.template', string='Use Template')
    created_product_id = fields.Many2one('product.product', string='Newly Created Variant', readonly=True)

    resolution_done = fields.Boolean(default=False)

    raw_data_json = fields.Json(string='Raw Row')

    step_log_ids = fields.One2many('mrp.bom.import.line.step', 'line_id', string='Steps')

    ptp_qty_onhand = fields.Float(
        string='On Hand',
        compute='_compute_ptp_availability',
        digits='Product Unit of Measure',
        help='Current on-hand quantity of the selected product (template).'
    )
    ptp_qty_forecast = fields.Float(
        string='Forecasted',
        compute='_compute_ptp_availability',
        digits='Product Unit of Measure',
        help='Forecasted quantity (virtual available) of the selected product (template).'
    )

    @api.depends('product_tmpl_id_ui',
                 'product_tmpl_id_ui.qty_available',
                 'product_tmpl_id_ui.virtual_available')

    def _compute_ptp_availability(self):
        for rec in self:
            tmpl = rec.product_tmpl_id_ui
            if tmpl:
                # product.template už má agregované qty přes varianty
                rec.ptp_qty_onhand = tmpl.qty_available or 0.0
                rec.ptp_qty_forecast = tmpl.virtual_available or 0.0
            else:
                rec.ptp_qty_onhand = 0.0
                rec.ptp_qty_forecast = 0.0

    @api.onchange('product_tmpl_id_ui')
    def _onchange_product_tmpl_id_ui(self):
        for rec in self:
            rec.product_id = rec.product_tmpl_id_ui.product_variant_id.id if rec.product_tmpl_id_ui else False
            if rec.product_tmpl_id_ui:
                rec.status = 'matched'
                rec.resolution_done = True

    def _raw_row(self):
        self.ensure_one()
        try:
            return self.raw_data_json if isinstance(self.raw_data_json, dict) else (json.loads(self.raw_data_json or '{}') if self.raw_data_json else {})
        except Exception:
            return {}

    def _raw_value_for_field(self, fpath):
        self.ensure_one()
        key = str(fpath or '').split('.')[-1]
        row = self._raw_row()

        def norm(s):
            import unicodedata
            s = '' if s is None else str(s)
            try:
                s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
            except Exception:
                pass
            s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).strip().lower()
            s = re.sub(r'\s+', ' ', s)
            return s

        if key in row:
            return row.get(key)
        if key.lower() in row:
            return row.get(key.lower())
        if key.upper() in row:
            return row.get(key.upper())

        key_norm = norm(key.replace('_', ' '))
        idx = {}
        for k in row.keys():
            idx.setdefault(norm(k), k)

        aliases = {
            'ptp_part_number': [
                'ptp part number','ptp-part-number','ptp part','ptp pn',
                'mpn','mfr part','manufacturer part','manufacturer part number',
                'part number','part no','pn','sku','internal reference',
                'default code','code','product code'
            ],
            'name': ['name','description','desc','designation','title','item name'],
            'barcode': ['barcode','ean','ean13','ean-13','gtin'],
            'default_code': ['default code','internal reference','code','sku','item number','item no'],
        }
        for k, als in aliases.items():
            if key_norm == norm(k):
                for a in als:
                    n = norm(a)
                    if n in idx:
                        return row.get(idx[n])

        if key_norm == 'ptp part number' and self.raw_part_number:
            return self.raw_part_number

        return None

    def _log_step(self, action, message):
        for rec in self:
            self.env['mrp.bom.import.line.step'].create({
                'line_id': rec.id,
                'action': action,
                'message': message,
            })

    def write(self, vals):
        # detect manual matching when product_tmpl_id_ui is set by user
        was_unmatched = {rec.id: rec.product_tmpl_id_ui.id for rec in self}
        res = super(MrpBomImportLine, self).write(vals)
        if 'product_tmpl_id_ui' in vals:
            for rec in self:
                before = was_unmatched.get(rec.id)
                after = rec.product_tmpl_id_ui.id if rec.product_tmpl_id_ui else False
                if not before and after:
                    rec.status = 'matched'
                    rec.resolution_done = True
                    rec._log_step('manual_match', _("Manually matched to %s") % rec.product_tmpl_id_ui.display_name)
                if before and not after:
                    rec.status = 'new'
                    rec.resolution_done = False
                    rec._log_step('manual_match', _("Manually unmatched to %s") % rec.product_tmpl_id_ui.display_name)
        return res

    def action_show_line(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom.import.line',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }
    def action_create_new_from_template(self):
        """Create product.template from an import line with robust pre-filling.
        Handles Char vs Many2one fields safely (e.g. ptp_footprint)."""
        self.ensure_one()
        PT = self.env['product.template'].sudo()

        def _m2o_safe_val(model_field_name: str, text_value: str):
            """Return a value for create() respecting field type.
            If Many2one -> return related record ID (create if missing).
            If not Many2one -> return original text.
            If text is empty/None -> return False."""
            if not text_value:
                return False
            if model_field_name not in PT._fields:
                return False
            fld = PT._fields[model_field_name]
            if getattr(fld, 'type', None) == 'many2one':
                comodel = self.env[fld.comodel_name].sudo()
                rec = comodel.search([('name', '=', text_value)], limit=1)
                if not rec:
                    rec = comodel.create({'name': text_value})
                return rec.id
            return text_value

        rec = self

        base_name = rec.raw_part_number or (rec.raw_description[:80] if rec.raw_description else _("Imported Component"))
        vals = {
            'name': base_name,
            'purchase_ok': True,
            'sale_ok': False,
            'type': 'consu',
            'standard_price': 1.0,
        }

        if getattr(rec.import_id, 'product_category_id', False):
            vals['categ_id'] = rec.import_id.product_category_id.id
        if getattr(rec.import_id, 'product_uom_id', False):
            u = rec.import_id.product_uom_id.id
            vals['uom_id'] = u
            vals['uom_po_id'] = u

        if 'default_code' in PT._fields and rec.raw_part_number:
            vals['default_code'] = rec.raw_part_number
        if 'ptp_part_number' in PT._fields and rec.raw_part_number:
            vals['ptp_part_number'] = rec.raw_part_number

        if 'ptp_footprint' in PT._fields and getattr(rec, 'raw_footprint', False):
            vals['ptp_footprint'] = _m2o_safe_val('ptp_footprint', rec.raw_footprint)

        desc_lines = [
            _("Imported component from BOM %s, line %s (ID %s).") % (rec.import_id.display_name, rec.sequence, rec.id),
            _("Raw Part Number: %s") % (rec.raw_part_number or ""),
            _("Raw Footprint: %s") % (getattr(rec, 'raw_footprint', "") or ""),
            _("Raw Description: %s") % (rec.raw_description or ""),
        ]
        vals['description'] = "\n".join(desc_lines)

        tmpl = PT.create(vals)
        imp = rec.import_id
        if imp and getattr(imp, 'default_vendor_id', False) and imp.default_vendor_id:
            # seller_ids existuje v purchase a správně založí product.supplierinfo
            seller_cmd = (0, 0, {
                'partner_id': imp.default_vendor_id.id,
                # volitelně: 'company_id': imp.company_id.id if 'company_id' in tmpl._fields else False,
                # Lead time v dnech:
                'delay': int(imp.default_vendor_delay or 0),
                # Nepředáváme cenu/měnu/min_qty, ať nic „nepřestřelíme“
            })
            # zapíšeme na šablonu
            if 'seller_ids' in tmpl._fields:
                tmpl.write({'seller_ids': [seller_cmd]})
                # jistota, že je produkt k nákupu
                if 'purchase_ok' in tmpl._fields and not tmpl.purchase_ok:
                    tmpl.purchase_ok = True
                if hasattr(rec, '_log_step'):
                    rec._log_step(
                        'create_new',
                        _("Vendor set: %s (lead time %sd)") % (imp.default_vendor_id.display_name,
                                                               imp.default_vendor_delay or 0)
                    )
        rec.write({
            'product_tmpl_id_ui': tmpl.id if 'product_tmpl_id_ui' in rec._fields else False,
            'product_id': tmpl.product_variant_id.id,
            'status': 'matched' if 'status' in rec._fields else False,
            'resolution_done': True if 'resolution_done' in rec._fields else False,
        })
        if hasattr(rec, '_log_step'):
            rec._log_step('create_new', _("Created new template %s from import line") % tmpl.display_name)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Product'),
            'res_model': 'product.template',
            'view_mode': 'form',
            'res_id': tmpl.id,
            'target': 'current',
        }
class MrpBomImportLineStep(models.Model):
    _name = 'mrp.bom.import.line.step'
    _description = 'BOM Import Line Step'

    line_id = fields.Many2one('mrp.bom.import.line', required=True, ondelete='cascade')
    date = fields.Datetime(default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    action = fields.Char()
    message = fields.Text()